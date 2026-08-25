"""Core typed pipeline for exact candidate-bound Lean replay generation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from adapters.common.exact_replay.registry import get_plugin
from adapters.common.limits import ResourceLimits
from adapters.common.security_bounds import enforce_nesting_depth

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_MODULE_RE = re.compile(r"^MathEvidence\.Generated\.Replay\.[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class CanonicalCandidate:
    """Schema-validated, capability-bound candidate payload."""

    capability_id: str
    capability_version: str
    request: dict[str, Any]
    certificate: dict[str, Any]
    candidate_bundle_digest: str
    request_digest: str
    claim_class: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayIR:
    """Typed intermediate representation. No raw Lean fragment slots."""

    capability_id: str
    generator_id: str
    generator_version: str
    grammar_version: str
    module_name: str
    declaration_name: str
    nodes: tuple[Any, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedModule:
    module_name: str
    declaration_name: str
    source_text: str
    source_hash: str
    generator_id: str
    generator_version: str
    grammar_version: str
    candidate_bundle_digest: str
    request_digest: str


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    detail: str
    identity_report: dict[str, Any] | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class AssuranceEvidence:
    capability_id: str
    generator_id: str
    generator_version: str
    grammar_version: str
    generated_source_hash: str
    candidate_hash: str
    request_digest: str
    module_name: str
    declaration_name: str
    verifier: str
    extras: dict[str, Any] = field(default_factory=dict)


class ExactReplayPlugin(Protocol):
    capability_id: str
    generator_id: str
    generator_version: str
    grammar_version: str
    verifier: str

    def parse_and_validate(
        self,
        *,
        request: dict[str, Any],
        certificate: dict[str, Any],
        candidate_bundle_digest: str,
        limits: ResourceLimits,
    ) -> CanonicalCandidate: ...

    def to_replay_ir(
        self,
        canonical: CanonicalCandidate,
        *,
        module_name: str,
        declaration_name: str,
    ) -> ReplayIR: ...

    def render(self, ir: ReplayIR) -> str: ...


def _source_hash(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _validate_module_name(module_name: str) -> None:
    if _SAFE_MODULE_RE.fullmatch(module_name) is None:
        raise ValueError(f"unsafe or non-canonical module name: {module_name!r}")


def _validate_digest(value: str, *, what: str) -> str:
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{what} must be a canonical sha256 digest")
    return value


def parse_and_validate(
    *,
    capability_id: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
    limits: ResourceLimits | None = None,
) -> CanonicalCandidate:
    """Validate candidate JSON and produce a canonical semantic object."""
    lim = limits or ResourceLimits()
    enforce_nesting_depth(request, limits=lim)
    enforce_nesting_depth(certificate, limits=lim)
    _validate_digest(candidate_bundle_digest, what="candidateBundleDigest")
    plugin = get_plugin(capability_id)
    return plugin.parse_and_validate(
        request=request,
        certificate=certificate,
        candidate_bundle_digest=candidate_bundle_digest,
        limits=lim,
    )


def to_replay_ir(
    canonical: CanonicalCandidate,
    *,
    module_name: str,
    declaration_name: str,
) -> ReplayIR:
    _validate_module_name(module_name)
    if not declaration_name or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", declaration_name):
        raise ValueError(f"unsafe declaration name: {declaration_name!r}")
    plugin = get_plugin(canonical.capability_id)
    return plugin.to_replay_ir(
        canonical, module_name=module_name, declaration_name=declaration_name
    )


def render(ir: ReplayIR, generator_version: str | None = None) -> GeneratedModule:
    plugin = get_plugin(ir.capability_id)
    if generator_version is not None and generator_version != plugin.generator_version:
        raise ValueError(
            f"generator_version {generator_version!r} != plugin {plugin.generator_version!r}"
        )
    if ir.generator_version != plugin.generator_version:
        raise ValueError("ReplayIR generator_version disagrees with registered plugin")
    source = plugin.render(ir)
    if "\r" in source:
        raise ValueError("generated source must use LF newlines only")
    # Deterministic: no timestamps / absolute paths in source by construction.
    banned = ("C:\\", "/Users/", "/home/", "T:", "file://")
    for token in banned:
        if token in source:
            raise ValueError(f"generated source contains forbidden path token {token!r}")
    return GeneratedModule(
        module_name=ir.module_name,
        declaration_name=ir.declaration_name,
        source_text=source,
        source_hash=_source_hash(source),
        generator_id=ir.generator_id,
        generator_version=ir.generator_version,
        grammar_version=ir.grammar_version,
        candidate_bundle_digest=str(ir.metadata.get("candidate_bundle_digest") or ""),
        request_digest=str(ir.metadata.get("request_digest") or ""),
    )


def verify(
    module: GeneratedModule,
    toolchain_contract: dict[str, Any] | None = None,
) -> VerificationResult:
    """Framework-level verify hook.

    Lake/lean execution remains argv-only in ``kernel_replay``. This
    function validates module metadata and optional contract digests without
    spawning processes, so plugins stay unit-testable offline.
    """
    del toolchain_contract  # reserved for offline bundle contracts
    if not module.source_text.strip():
        return VerificationResult(ok=False, detail="empty generated source")
    if module.source_hash != _source_hash(module.source_text):
        return VerificationResult(ok=False, detail="generatedSourceHash mismatch")
    try:
        _validate_module_name(module.module_name)
    except ValueError as exc:
        return VerificationResult(ok=False, detail=str(exc))
    return VerificationResult(ok=True, detail="module metadata verified")


def bind(
    module: GeneratedModule,
    *,
    capability_id: str,
    verifier: str | None = None,
    extras: dict[str, Any] | None = None,
) -> AssuranceEvidence:
    plugin = get_plugin(capability_id)
    return AssuranceEvidence(
        capability_id=capability_id,
        generator_id=module.generator_id,
        generator_version=module.generator_version,
        grammar_version=module.grammar_version,
        generated_source_hash=module.source_hash,
        candidate_hash=module.candidate_bundle_digest,
        request_digest=module.request_digest,
        module_name=module.module_name,
        declaration_name=module.declaration_name,
        verifier=verifier or plugin.verifier,
        extras=dict(extras or {}),
    )


def generate_module(
    *,
    capability_id: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
    module_name: str,
    declaration_name: str,
    limits: ResourceLimits | None = None,
) -> GeneratedModule:
    """Convenience: full generate path used by kernel_replay / script wrappers."""
    canonical = parse_and_validate(
        capability_id=capability_id,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=candidate_bundle_digest,
        limits=limits,
    )
    ir = to_replay_ir(
        canonical, module_name=module_name, declaration_name=declaration_name
    )
    return render(ir)
