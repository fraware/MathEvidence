"""Offline exact-replay release bundle.

A self-contained package that can be replayed after dependency materialization
with network disabled. Absolute local paths are never semantic fields.

Two modes for a valid bundle (both require regenerability of the bound source):
  - regenerate-and-verify: rebuild source from canonical candidate + pinned
    generator and require byte-identical text plus matching source hash
  - artifact-replay: verify the saved generated source hash, then regenerate
    and require matching source hash (text equality optional)

Neither mode mints a Certification Record. Default logical outcome is
``theorem_pending`` (integrity only). Opt-in Lean inspect
(``MATHEVIDENCE_OFFLINE_LEAN=1`` / ``require_lean=True``) may yield
``theorem_proved`` after declaration-identity checks; that is still weaker than
online ``kernel_replay`` CR promotion (online remains the promotion authority).

Missing dependencies are reported as setup/integrity errors, never theorem failures.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from adapters.common.bounded_process import EXECUTION_POLICY_ID
from adapters.common.bundle import file_digest, write_cjson, write_text_lf
from adapters.common.canonical import sha256_digest
from adapters.common.environment_lock import current_capability_environment_lock
from adapters.common.errors import AdapterError
from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.exact_replay.registry import get_plugin
from adapters.common.security_bounds import reject_path_traversal
from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SCHEMA_VERSION,
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    environment_lock_digest,
    theorem_type_digest,
)

BUNDLE_SCHEMA_VERSION = "0.1.0"
DRIVER_VERSION = "0.1.0"
DRIVER_ID = "mathevidence.offline_exact_replay"

ReplayMode = Literal["regenerate-and-verify", "artifact-replay"]
LogicalOutcome = Literal[
    "integrity_ok",
    "setup_integrity_error",
    "tamper_detected",
    "theorem_pending",  # structure OK; Lean verify not run / unavailable
    "theorem_proved",  # Lake inspect succeeded offline
    "theorem_failure",  # Lake available; theorem/identity rejected
]

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ABS_PATH_MARKERS = ("C:\\", "c:\\", "/Users/", "/home/", "file://")

# Relative roles inside an offline exact-replay bundle (never absolute).
ROLE_FILES = (
    "exact-replay-manifest.cjson",
    "request.cjson",
    "certificate.cjson",
    "generated-source.lean",
    "toolchain-contract.cjson",
    "expected-identity.cjson",
)


@dataclass(frozen=True)
class OfflineReplayResult:
    ok: bool
    mode: ReplayMode
    logical_outcome: LogicalOutcome
    detail: str
    capability_id: str
    generated_source_hash: str
    regenerated_source_hash: str | None
    manifest_hash: str
    error_kind: str | None = None
    extras: dict[str, Any] | None = None


def _offline_error(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    **extra: Any,
) -> AdapterError:
    """Map offline-bundle failure codes onto the stable AdapterError vocabulary."""
    aliases = {
        "environment_mismatch": "assurance_mode_unavailable",
        "goal_claim_mismatch": "goal_mismatch",
    }
    mapped = aliases.get(code, code)
    merged: dict[str, Any] = {"offlineCode": code}
    if details:
        merged.update(details)
    merged.update(extra)
    kind = merged.get("kind")
    try:
        return AdapterError(code=mapped, message=f"{code}: {message}", details=merged)
    except ValueError:
        fallback = (
            "replay_dependency_missing"
            if kind == "setup_integrity"
            else "malformed_evidence"
        )
        return AdapterError(code=fallback, message=f"{code}: {message}", details=merged)


def _digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_digest(value: Any, *, what: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise _offline_error(
            "malformed_evidence",
            f"{what} must be a canonical sha256 digest",
        )
    return value


def _reject_absolute_semantic_paths(obj: Any, *, path: str = "$") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Relative path fields are allowed; absolute ones are not.
            if isinstance(value, str) and any(m in value for m in _ABS_PATH_MARKERS):
                raise _offline_error(
                    "malformed_evidence",
                    f"absolute local path forbidden in semantic field {path}.{key}",
                )
            _reject_absolute_semantic_paths(value, path=f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            _reject_absolute_semantic_paths(value, path=f"{path}[{i}]")


def _assert_offline_env() -> None:
    """After materialization, network must stay disabled for exact offline replay."""
    if os.environ.get("MATHEVIDENCE_ALLOW_NETWORK") == "1":
        raise _offline_error(
            "replay_dependency_missing",
            "offline exact replay refuses MATHEVIDENCE_ALLOW_NETWORK=1",
            kind="setup_integrity",
        )
    # Explicit offline marker expected for release-grade drivers.
    if os.environ.get("MATHEVIDENCE_OFFLINE", "1") not in {"1", "true", "TRUE", "yes"}:
        raise _offline_error(
            "replay_dependency_missing",
            "MATHEVIDENCE_OFFLINE must remain enabled during offline exact replay",
            kind="setup_integrity",
        )


def _load_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise _offline_error("malformed_evidence", f"{path.name} must be an object")
    return data


def build_toolchain_contract(repo_root: Path, capability_id: str) -> dict[str, Any]:
    """Pin toolchain/lock digests without embedding absolute paths."""
    root = Path(repo_root).resolve()
    lock = current_capability_environment_lock(root, capability_id)
    lean_toolchain = (root / "lean-toolchain").read_text(encoding="utf-8").strip()
    lake_manifest = root / "lake-manifest.json"
    if not lake_manifest.is_file():
        raise _offline_error(
            "replay_dependency_missing",
            "lake-manifest.json missing (setup/integrity)",
            details={"kind": "setup_integrity"},
        )
    return {
        "schemaVersion": BUNDLE_SCHEMA_VERSION,
        "capabilityId": capability_id,
        "leanToolchain": lean_toolchain,
        "environmentLock": lock,
        "dependencyLockDigest": file_digest(lake_manifest),
        "toolchainContractDigest": sha256_digest(
            {
                "leanToolchain": lean_toolchain,
                "environmentLock": lock,
                "dependencyLockDigest": file_digest(lake_manifest),
            }
        ),
        # Relative vendor integrity pointer — not an absolute path.
        "dependencyLockRelativePath": "lake-manifest.json",
    }


def build_offline_exact_bundle(
    bundle_dir: Path | str,
    *,
    capability_id: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
    module_name: str,
    declaration_name: str,
    repo_root: Path | str | None = None,
    certification_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Materialize a release-grade offline exact-replay bundle."""
    root = Path(repo_root or Path(__file__).resolve().parents[3]).resolve()
    out = Path(bundle_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name in out.iterdir():
        # Bundle directory should be dedicated; refuse unexpected absolute-path roles.
        if name.is_symlink():
            raise _offline_error(
                "malformed_evidence",
                "bundle directory must not contain symlinks at write time",
            )

    plugin = get_plugin(capability_id)
    cand = _require_digest(candidate_bundle_digest, what="candidateBundleDigest")
    module = generate_module(
        capability_id=capability_id,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=cand,
        module_name=module_name,
        declaration_name=declaration_name,
    )
    toolchain = build_toolchain_contract(root, capability_id)
    expected_identity = {
        "schemaVersion": BUNDLE_SCHEMA_VERSION,
        "moduleName": module.module_name,
        "declarationName": module.declaration_name,
        "verifier": plugin.verifier,
        # Identity digest filled after Lean inspect; placeholder is explicit.
        "theoremOrDeclarationIdentity": module.declaration_name,
        "identityAuthority": "pending_lean_environment",
    }

    write_cjson(out / "request.cjson", request)
    write_cjson(out / "certificate.cjson", certificate)
    write_text_lf(out / "generated-source.lean", module.source_text)
    write_cjson(out / "toolchain-contract.cjson", toolchain)
    write_cjson(out / "expected-identity.cjson", expected_identity)
    if certification_receipt is not None:
        write_cjson(out / "certification-receipt.cjson", certification_receipt)

    artifact_hashes = {
        "request.cjson": file_digest(out / "request.cjson"),
        "certificate.cjson": file_digest(out / "certificate.cjson"),
        "generated-source.lean": file_digest(out / "generated-source.lean"),
        "toolchain-contract.cjson": file_digest(out / "toolchain-contract.cjson"),
        "expected-identity.cjson": file_digest(out / "expected-identity.cjson"),
    }

    manifest: dict[str, Any] = {
        "schemaVersion": BUNDLE_SCHEMA_VERSION,
        "driverId": DRIVER_ID,
        "driverVersion": DRIVER_VERSION,
        "executionPolicyId": EXECUTION_POLICY_ID,
        "capabilityId": capability_id,
        "capabilityVersion": str(request.get("capabilityVersion") or ""),
        "candidateBundleDigest": cand,
        "requestDigest": str(request.get("requestDigest") or ""),
        "generatorId": module.generator_id,
        "generatorVersion": module.generator_version,
        "grammarVersion": module.grammar_version,
        "generatedSourceHash": module.source_hash,
        "moduleName": module.module_name,
        "declarationName": module.declaration_name,
        "verifier": plugin.verifier,
        "toolchainContractDigest": toolchain["toolchainContractDigest"],
        "dependencyLockDigest": toolchain["dependencyLockDigest"],
        "artifactHashes": artifact_hashes,
        "expectedDeclarationIdentity": expected_identity["theoremOrDeclarationIdentity"],
        "modes": ["regenerate-and-verify", "artifact-replay"],
        # Relative role paths only — never absolute.
        "roles": {name: name for name in ROLE_FILES},
    }
    if certification_receipt is not None:
        manifest["certificationReceiptRelativePath"] = "certification-receipt.cjson"
        artifact_hashes["certification-receipt.cjson"] = file_digest(
            out / "certification-receipt.cjson"
        )
        manifest["artifactHashes"] = artifact_hashes

    _reject_absolute_semantic_paths(manifest)
    write_cjson(out / "exact-replay-manifest.cjson", manifest)
    manifest_hash = file_digest(out / "exact-replay-manifest.cjson")
    # Re-bind manifest hash into a sidecar so the manifest itself stays stable.
    write_cjson(
        out / "exact-replay-manifest.hash.cjson",
        {"schemaVersion": BUNDLE_SCHEMA_VERSION, "manifestHash": manifest_hash},
    )
    return {"manifest": manifest, "manifestHash": manifest_hash, "bundleDir": str(out)}


def _verify_artifact_hashes(bundle_dir: Path, manifest: dict[str, Any]) -> None:
    hashes = manifest.get("artifactHashes")
    if not isinstance(hashes, dict) or not hashes:
        raise _offline_error("malformed_evidence", "manifest artifactHashes missing")
    for rel, expected in hashes.items():
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise _offline_error("malformed_evidence", "artifactHashes entry invalid")
        reject_path_traversal(rel.replace("\\", "/"))
        path = bundle_dir / rel
        if not path.is_file():
            raise _offline_error(
                "content_digest_mismatch",
                f"artifact missing: {rel}",
                details={"kind": "tamper", "role": rel},
            )
        if path.is_symlink():
            raise _offline_error(
                "malformed_evidence",
                f"symlink artifact rejected: {rel}",
                details={"kind": "tamper", "role": rel},
            )
        actual = file_digest(path)
        if actual != expected:
            raise _offline_error(
                "content_digest_mismatch",
                f"artifact digest mismatch: {rel}",
                details={"kind": "tamper", "role": rel, "expected": expected, "actual": actual},
            )


def _check_toolchain_lock(
    *,
    repo_root: Path,
    capability_id: str,
    manifest: dict[str, Any],
    toolchain: dict[str, Any],
) -> None:
    try:
        live = build_toolchain_contract(repo_root, capability_id)
    except AdapterError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _offline_error(
            "replay_dependency_missing",
            f"failed to materialize toolchain contract: {exc}",
            details={"kind": "setup_integrity"},
        ) from exc

    for key in ("toolchainContractDigest", "dependencyLockDigest"):
        bound = manifest.get(key) or toolchain.get(key)
        if bound != live.get(key):
            raise _offline_error(
                "environment_mismatch",
                f"{key} mismatch vs live workspace lock",
                details={"kind": "setup_integrity", "field": key},
            )


def _should_attempt_lean_inspect(*, require_lean: bool) -> bool:
    """Prefer Lean inspect when explicitly required or opted-in via env."""
    if require_lean:
        return True
    flag = os.environ.get("MATHEVIDENCE_OFFLINE_LEAN", "").strip().lower()
    return flag in {"1", "true", "yes"}


def _lean_inspect_offline(
    *,
    repo_root: Path,
    module_name: str,
    declaration_name: str,
    source_text: str,
    environment_lock_digest_value: str,
) -> tuple[LogicalOutcome, str, dict[str, Any] | None]:
    """Compile + declaration-identity inspect for an offline bundle source.

    Requires the same identity surface as online kernel_replay for the
    declaration/type/proof/axiom fields. Does **not** mint a Certification
    Record; online ``run_kernel_replay`` remains the CR promotion path.
    """
    from adapters.common.kernel_replay import (
        ALLOWED_AXIOMS_DEFAULT,
        KernelReplayError,
        axiom_policy_ok,
        find_lake,
    )
    from adapters.common.kernel_replay import (
        _compile_and_inspect,  # noqa: PLC2701 — shared inspect path
    )

    _SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

    lake = find_lake(repo_root)
    if lake is None:
        return (
            "setup_integrity_error",
            "lake not found for offline Lean theorem inspect",
            None,
        )
    try:
        identity_report, _stdout, _stderr = _compile_and_inspect(
            root=repo_root,
            lake=lake,
            module_name=module_name,
            declaration_name=declaration_name,
            source_text=source_text,
            environment_lock_digest_value=environment_lock_digest_value,
        )
    except KernelReplayError as exc:
        code = exc.code
        if code in {
            "replay_dependency_missing",
            "resource_limit_exceeded",
            "environment_mismatch",
        }:
            return ("setup_integrity_error", f"{code}: {exc.message}", None)
        return ("theorem_failure", f"{code}: {exc.message}", None)
    except Exception as exc:  # noqa: BLE001
        return ("setup_integrity_error", f"offline Lean inspect failed: {exc}", None)

    if identity_report.get("declarationName") != declaration_name:
        return ("theorem_failure", "inspected declaration name mismatch", identity_report)
    if identity_report.get("environmentLockDigest") != environment_lock_digest_value:
        return (
            "theorem_failure",
            "Lean identity environment-lock mismatch",
            identity_report,
        )
    type_identity = identity_report.get("typeIdentity")
    if not isinstance(type_identity, dict):
        return ("theorem_failure", "Lean identity report missing typeIdentity", identity_report)
    if type_identity.get("schemaVersion") != THEOREM_IDENTITY_SCHEMA_VERSION:
        return (
            "theorem_failure",
            "Lean theorem identity schema version mismatch",
            identity_report,
        )
    if type_identity.get("serializerVersion") != THEOREM_IDENTITY_SERIALIZER_VERSION:
        return (
            "theorem_failure",
            "Lean theorem identity serializer version mismatch",
            identity_report,
        )
    emitted_type_digest = identity_report.get("theoremTypeDigest")
    if theorem_type_digest(type_identity) != emitted_type_digest:
        return (
            "theorem_failure",
            "Python recomputation of Lean-emitted theorem type identity disagrees",
            identity_report,
        )
    proof_digest = identity_report.get("proofDeclarationDigest")
    if not isinstance(proof_digest, str) or _SHA256_RE.fullmatch(proof_digest) is None:
        return (
            "theorem_failure",
            "Lean identity report missing proof digest",
            identity_report,
        )
    axioms_raw = identity_report.get("axioms")
    if not isinstance(axioms_raw, list) or not all(isinstance(a, str) for a in axioms_raw):
        return ("theorem_failure", "Lean identity report has invalid axiom set", identity_report)
    if not axiom_policy_ok(sorted(set(axioms_raw)), ALLOWED_AXIOMS_DEFAULT):
        return (
            "theorem_failure",
            f"unexpected axioms {sorted(set(axioms_raw))}",
            identity_report,
        )
    return (
        "theorem_proved",
        "offline exact bundle Lean theorem inspect succeeded",
        identity_report,
    )


def replay_offline_exact_bundle(
    bundle_dir: Path | str,
    *,
    mode: ReplayMode = "regenerate-and-verify",
    repo_root: Path | str | None = None,
    require_lean: bool = False,
    check_live_toolchain: bool = True,
) -> OfflineReplayResult:
    """Replay an offline exact bundle. Network must stay disabled.

    Default success means integrity + regenerability (``theorem_pending``).
    When ``require_lean`` is true or ``MATHEVIDENCE_OFFLINE_LEAN=1``, Lake
    declaration-identity inspect is attempted and may yield ``theorem_proved``.
    Setup/missing Lake stays distinct from ``theorem_failure``.
    """
    root = Path(repo_root or Path(__file__).resolve().parents[3]).resolve()
    path = Path(bundle_dir)
    if not path.is_dir():
        return OfflineReplayResult(
            ok=False,
            mode=mode,
            logical_outcome="setup_integrity_error",
            detail=f"bundle directory missing: {path}",
            capability_id="",
            generated_source_hash="",
            regenerated_source_hash=None,
            manifest_hash="",
            error_kind="setup_integrity",
        )

    try:
        _assert_offline_env()
        for role in ROLE_FILES:
            reject_path_traversal(role)
            role_path = path / role
            if not role_path.is_file():
                raise _offline_error(
                    "replay_dependency_missing",
                    f"missing bundle role {role}",
                    details={"kind": "setup_integrity"},
                )
            if role_path.is_symlink():
                raise _offline_error(
                    "malformed_evidence",
                    f"symlink role rejected: {role}",
                    details={"kind": "tamper"},
                )

        manifest = _load_json(path / "exact-replay-manifest.cjson")
        _reject_absolute_semantic_paths(manifest)
        if manifest.get("schemaVersion") != BUNDLE_SCHEMA_VERSION:
            raise _offline_error(
                "malformed_evidence",
                f"unsupported offline bundle schemaVersion {manifest.get('schemaVersion')!r}",
            )
        if manifest.get("driverId") != DRIVER_ID:
            raise _offline_error(
                "malformed_evidence",
                "driverId mismatch",
                details={"kind": "tamper"},
            )
        if manifest.get("driverVersion") != DRIVER_VERSION:
            raise _offline_error(
                "environment_mismatch",
                "driverVersion mismatch",
                details={"kind": "setup_integrity"},
            )
        if manifest.get("executionPolicyId") != EXECUTION_POLICY_ID:
            raise _offline_error(
                "environment_mismatch",
                "executionPolicyId mismatch",
                details={"kind": "tamper"},
            )

        capability_id = str(manifest.get("capabilityId") or "")
        plugin = get_plugin(capability_id)
        for key, expected in (
            ("generatorId", plugin.generator_id),
            ("generatorVersion", plugin.generator_version),
            ("grammarVersion", plugin.grammar_version),
        ):
            if manifest.get(key) != expected:
                raise _offline_error(
                    "environment_mismatch",
                    f"{key} does not match registered plugin",
                    details={"kind": "tamper", "field": key},
                )

        _verify_artifact_hashes(path, manifest)

        request = _load_json(path / "request.cjson")
        certificate = _load_json(path / "certificate.cjson")
        toolchain = _load_json(path / "toolchain-contract.cjson")
        expected_identity = _load_json(path / "expected-identity.cjson")
        source_text = (path / "generated-source.lean").read_text(encoding="utf-8")
        source_text = source_text.replace("\r\n", "\n").replace("\r", "\n")
        bound_hash = _require_digest(manifest.get("generatedSourceHash"), what="generatedSourceHash")
        if _digest_text(source_text) != bound_hash:
            raise _offline_error(
                "content_digest_mismatch",
                "generated-source.lean does not match generatedSourceHash",
                details={"kind": "tamper"},
            )

        if check_live_toolchain:
            _check_toolchain_lock(
                repo_root=root,
                capability_id=capability_id,
                manifest=manifest,
                toolchain=toolchain,
            )
        else:
            for key in ("toolchainContractDigest", "dependencyLockDigest"):
                if manifest.get(key) != toolchain.get(key):
                    raise _offline_error(
                        "environment_mismatch",
                        f"manifest {key} disagrees with toolchain-contract.cjson",
                        details={"kind": "tamper", "field": key},
                    )

        cand = _require_digest(
            manifest.get("candidateBundleDigest"), what="candidateBundleDigest"
        )
        module_name = str(manifest.get("moduleName") or "")
        declaration_name = str(manifest.get("declarationName") or "")
        if expected_identity.get("declarationName") != declaration_name:
            raise _offline_error(
                "goal_claim_mismatch",
                "expected-identity declarationName mismatch",
                details={"kind": "tamper"},
            )
        if expected_identity.get("moduleName") != module_name:
            raise _offline_error(
                "goal_claim_mismatch",
                "expected-identity moduleName mismatch",
                details={"kind": "tamper"},
            )

        regenerated_hash: str | None = None
        if mode == "regenerate-and-verify":
            regenerated = generate_module(
                capability_id=capability_id,
                request=request,
                certificate=certificate,
                candidate_bundle_digest=cand,
                module_name=module_name,
                declaration_name=declaration_name,
            )
            regenerated_hash = regenerated.source_hash
            if regenerated.source_hash != bound_hash or regenerated.source_text != source_text:
                raise _offline_error(
                    "content_digest_mismatch",
                    "regenerated source does not match bound generatedSourceHash",
                    details={"kind": "tamper"},
                )
        elif mode == "artifact-replay":
            regenerated = generate_module(
                capability_id=capability_id,
                request=request,
                certificate=certificate,
                candidate_bundle_digest=cand,
                module_name=module_name,
                declaration_name=declaration_name,
            )
            regenerated_hash = regenerated.source_hash
            if regenerated.source_hash != bound_hash:
                raise _offline_error(
                    "content_digest_mismatch",
                    "artifact replay regenerability check failed",
                    details={"kind": "tamper"},
                )
        else:
            raise _offline_error("malformed_evidence", f"unknown replay mode {mode!r}")

        manifest_hash = file_digest(path / "exact-replay-manifest.cjson")
        extras: dict[str, Any] = {
            "driverVersion": DRIVER_VERSION,
            "executionPolicyId": EXECUTION_POLICY_ID,
            "modesAgree": True,
        }

        if _should_attempt_lean_inspect(require_lean=require_lean):
            env_lock = toolchain.get("environmentLock")
            if isinstance(env_lock, dict):
                lock_digest = environment_lock_digest(env_lock)
            else:
                # Fall back only when the bundle predates environmentLock embedding.
                lock_digest = str(
                    toolchain.get("toolchainContractDigest")
                    or manifest.get("toolchainContractDigest")
                    or ""
                )
            outcome, detail, identity = _lean_inspect_offline(
                repo_root=root,
                module_name=module_name,
                declaration_name=declaration_name,
                source_text=source_text,
                environment_lock_digest_value=lock_digest,
            )
            if identity is not None:
                extras["identityAuthority"] = identity.get("authority")
                extras["theoremTypeDigest"] = identity.get("theoremTypeDigest")
            if outcome == "theorem_proved":
                return OfflineReplayResult(
                    ok=True,
                    mode=mode,
                    logical_outcome="theorem_proved",
                    detail=detail,
                    capability_id=capability_id,
                    generated_source_hash=bound_hash,
                    regenerated_source_hash=regenerated_hash,
                    manifest_hash=manifest_hash,
                    extras=extras,
                )
            if outcome == "theorem_failure":
                return OfflineReplayResult(
                    ok=False,
                    mode=mode,
                    logical_outcome="theorem_failure",
                    detail=detail,
                    capability_id=capability_id,
                    generated_source_hash=bound_hash,
                    regenerated_source_hash=regenerated_hash,
                    manifest_hash=manifest_hash,
                    error_kind="theorem",
                    extras=extras,
                )
            if require_lean:
                return OfflineReplayResult(
                    ok=False,
                    mode=mode,
                    logical_outcome="setup_integrity_error",
                    detail=detail,
                    capability_id=capability_id,
                    generated_source_hash=bound_hash,
                    regenerated_source_hash=regenerated_hash,
                    manifest_hash=manifest_hash,
                    error_kind="setup_integrity",
                    extras=extras,
                )
            extras["leanInspectDeferred"] = detail

        return OfflineReplayResult(
            ok=True,
            mode=mode,
            logical_outcome="theorem_pending",
            detail=(
                "offline exact bundle integrity and regenerability verified; "
                "Lean theorem inspect deferred "
                "(set MATHEVIDENCE_OFFLINE_LEAN=1 or require_lean=True)"
            ),
            capability_id=capability_id,
            generated_source_hash=bound_hash,
            regenerated_source_hash=regenerated_hash,
            manifest_hash=manifest_hash,
            extras=extras,
        )
    except AdapterError as exc:
        kind = "tamper" if (exc.details or {}).get("kind") == "tamper" else "setup_integrity"
        if (exc.details or {}).get("kind") == "setup_integrity":
            outcome = "setup_integrity_error"
        elif kind == "tamper" or exc.code in {
            "content_digest_mismatch",
            "goal_mismatch",
            "malformed_evidence",
        }:
            outcome = "tamper_detected"
            kind = "tamper"
        else:
            outcome = "setup_integrity_error"
            kind = "setup_integrity"
        return OfflineReplayResult(
            ok=False,
            mode=mode,
            logical_outcome=outcome,
            detail=str(exc),
            capability_id=str((locals().get("manifest") or {}).get("capabilityId") or ""),
            generated_source_hash=str(
                (locals().get("manifest") or {}).get("generatedSourceHash") or ""
            ),
            regenerated_source_hash=None,
            manifest_hash="",
            error_kind=kind,
            extras={"errorCode": exc.code, "details": exc.details},
        )


def both_modes_agree(
    bundle_dir: Path | str,
    *,
    repo_root: Path | str | None = None,
    check_live_toolchain: bool = True,
    require_lean: bool = False,
) -> tuple[OfflineReplayResult, OfflineReplayResult]:
    """Run both offline modes; callers assert equal logical outcomes."""
    a = replay_offline_exact_bundle(
        bundle_dir,
        mode="regenerate-and-verify",
        repo_root=repo_root,
        check_live_toolchain=check_live_toolchain,
        require_lean=require_lean,
    )
    b = replay_offline_exact_bundle(
        bundle_dir,
        mode="artifact-replay",
        repo_root=repo_root,
        check_live_toolchain=check_live_toolchain,
        require_lean=require_lean,
    )
    return a, b

def mutate_bundle_for_tamper(
    bundle_dir: Path,
    *,
    case: str,
) -> None:
    """Apply a single offline-bundle tamper mutation in-place (test helper)."""
    manifest_path = bundle_dir / "exact-replay-manifest.cjson"
    manifest = _load_json(manifest_path)

    if case == "candidate":
        req = _load_json(bundle_dir / "request.cjson")
        # Mutate a semantic field without updating hashes.
        if "target" in req and isinstance(req["target"], dict):
            terms = req["target"].get("terms")
            if isinstance(terms, list) and terms:
                terms[0] = deepcopy(terms[0])
                terms[0]["coefficient"] = int(terms[0].get("coefficient", 1)) + 1
        else:
            req["_tamper"] = True
        write_cjson(bundle_dir / "request.cjson", req)
    elif case == "generated_source":
        text = (bundle_dir / "generated-source.lean").read_text(encoding="utf-8")
        write_text_lf(bundle_dir / "generated-source.lean", text + "\n-- tampered\n")
    elif case == "artifact_delete":
        (bundle_dir / "certificate.cjson").unlink()
    elif case == "artifact_mutate":
        cert = _load_json(bundle_dir / "certificate.cjson")
        cert["_tamper"] = True
        write_cjson(bundle_dir / "certificate.cjson", cert)
    elif case == "manifest":
        manifest["generatedSourceHash"] = "sha256:" + ("e" * 64)
        write_cjson(manifest_path, manifest)
    elif case == "generator_version":
        manifest["generatorVersion"] = "9.9.9"
        write_cjson(manifest_path, manifest)
    elif case == "declaration_identity":
        ident = _load_json(bundle_dir / "expected-identity.cjson")
        ident["declarationName"] = "tampered_declaration"
        write_cjson(bundle_dir / "expected-identity.cjson", ident)
        # Keep manifest hash of expected-identity stale → tamper on hash check,
        # or update hash so declaration mismatch is the signal.
        hashes = dict(manifest.get("artifactHashes") or {})
        hashes["expected-identity.cjson"] = file_digest(
            bundle_dir / "expected-identity.cjson"
        )
        manifest["artifactHashes"] = hashes
        write_cjson(manifest_path, manifest)
    elif case == "toolchain_lock":
        manifest["dependencyLockDigest"] = "sha256:" + ("0" * 64)
        write_cjson(manifest_path, manifest)
    elif case == "capability_id":
        manifest["capabilityId"] = "algebra.rational_equality"
        write_cjson(manifest_path, manifest)
    elif case == "capability_version":
        # Alias kept for older callers; mutates capabilityId (not version).
        manifest["capabilityId"] = "algebra.rational_equality"
        write_cjson(manifest_path, manifest)
    else:
        raise ValueError(f"unknown tamper case: {case}")
