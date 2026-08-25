"""Kernel replay driver (Wave 2 / exact-candidate trust repair).

The generic theorem-producing path is fail-closed and registry-driven.
Exact generation goes through ``adapters.common.exact_replay``. Other
capability OfflineFixtures remain available to explicit self-tests only and are
never Certification Record authority for arbitrary bundles.

For an exact replay this module performs:

    Candidate Bundle -> exact generated Lean theorem -> compile to .olean -> fresh
    Lean.Environment import -> declaration type/proof/axiom inspection -> strict
    Certification Record.

Python never supplies the theorem type or proof digest written to the record.
Generated replay files are transactional and candidate-namespaced; they are not
persistent source inputs to later certifications.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from adapters.common.bounded_process import EXECUTION_POLICY_ID, run_bounded
from adapters.common.bundle import (
    NA_SENTINEL,
    compute_bundle_digest,
    file_digest,
    find_role_path,
    load_role_json,
    verify_bundle_offline,
    write_certification_record,
)
from adapters.common.environment_lock import current_capability_environment_lock
from adapters.common.errors import AdapterError
from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.limits import ResourceLimits
from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SCHEMA_VERSION,
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    build_replay_target,
    environment_lock_digest,
    theorem_identity_payload,
    theorem_type_digest,
)
from agent.api.assurance_policy import (
    decide_exact_kernel_replay,
    exact_binding,
    map_claim_to_outcome,
    outcome_allowed,
)

ALLOWED_AXIOMS_DEFAULT = (
    "propext",
    "Quot.sound",
    "Classical.choice",
    "Lean.ofReduceBool",
    "Lean.trustCompiler",
)

# Live authority is the registry; this set tracks capabilities with exactBinding.supported.
EXACT_REPLAY_CAPABILITIES = frozenset(
    {
        "algebra.ideal_membership_witness",
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "analysis.analytic_calculus",
    }
)
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXECUTION_POLICY_ID = EXECUTION_POLICY_ID


def _load_script(filename: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(module_name, repo / "scripts" / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generate_from_target(target: dict[str, Any]) -> str:
    """Historical OfflineFixtures generator mirror; self-test use only."""
    return _load_script(
        "generate_replay_module.py", "generate_replay_module"
    ).generate_from_target(target)


def _generate_exact_source(
    *,
    capability_id: str,
    module_name: str,
    declaration_name: str,
    request: dict[str, Any],
    certificate: dict[str, Any],
    candidate_bundle_digest: str,
) -> tuple[str, dict[str, str]]:
    """Render via exact_replay framework; return source text + generator metadata."""
    module = generate_module(
        capability_id=capability_id,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=candidate_bundle_digest,
        module_name=module_name,
        declaration_name=declaration_name,
    )
    meta = {
        "generatorId": module.generator_id,
        "generatorVersion": module.generator_version,
        "grammarVersion": module.grammar_version,
        "generatedSourceHash": module.source_hash,
    }
    return module.source_text, meta


KERNEL_REPLAY_CODES = frozenset(
    {
        "bundle_not_found",
        "manifest_invalid",
        "content_digest_mismatch",
        "request_decode_failed",
        "certificate_decode_failed",
        "request_digest_mismatch",
        "goal_reification_failed",
        "goal_claim_mismatch",
        "checker_rejected",
        "side_condition_unresolved",
        "theorem_elaboration_failed",
        "kernel_rejected",
        "unexpected_axiom",
        "environment_mismatch",
        "resource_limit_exceeded",
        "replay_dependency_missing",
        "assurance_mode_unavailable",
    }
)

THEOREM_LEVEL_STATUSES = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "approximation_certified",
        "native_verified",
    }
)


class KernelReplayError(AdapterError):
    """Structured kernel-replay failure."""


def _kr_error(code: str, message: str, **details: Any) -> KernelReplayError:
    aliases = {
        "manifest_invalid": "manifest_schema_invalid",
        "request_decode_failed": "certificate_decode_failed",
        "checker_rejected": "certificate_rejected",
        "goal_reification_failed": "goal_mismatch",
        "goal_claim_mismatch": "goal_mismatch",
        "side_condition_unresolved": "side_condition_unproved",
        "theorem_elaboration_failed": "malformed_evidence",
        "kernel_rejected": "malformed_evidence",
        "unexpected_axiom": "axiom_policy_violation",
        "environment_mismatch": "assurance_mode_unavailable",
        "platform_link_failed": "replay_dependency_missing",
    }
    mapped = aliases.get(code, code)
    try:
        return KernelReplayError(
            code=mapped,
            message=f"{code}: {message}",
            details={"kernelCode": code, **details},
        )
    except ValueError:
        return KernelReplayError(
            code="malformed_evidence",
            message=f"{code}: {message}",
            details={"kernelCode": code, **details},
        )


def find_lake(repo_root: Path) -> Path | None:
    del repo_root
    which = shutil.which("lake")
    return Path(which) if which else None


def parse_print_axioms(stdout: str, declaration_name: str) -> list[str]:
    """Legacy parser kept for fixed executable/self-test compatibility."""
    axioms: list[str] = []
    for line in stdout.splitlines():
        if declaration_name in line and "axioms" in line.lower():
            match = re.search(r"\[([^\]]*)\]", line)
            if match:
                inner = match.group(1).strip()
                if inner:
                    axioms = [a.strip() for a in inner.split(",") if a.strip()]
            elif "depends on axioms: []" in line or "no axioms" in line.lower():
                axioms = []
    return axioms


def axiom_policy_ok(
    axioms: list[str], allowed: tuple[str, ...] = ALLOWED_AXIOMS_DEFAULT
) -> bool:
    allowed_set = set(allowed)
    return all(axiom in allowed_set for axiom in axioms)


def build_structural_theorem_type(
    *,
    var_names: list[str],
    claim_preview: str,
    constant_names: list[str] | None = None,
    binder_type: str = "Rat",
) -> dict[str, Any]:
    """Historical v0.3 vector helper; never Certification Record authority."""
    return {
        "schemaVersion": "0.3.0",
        "serializerVersion": "mathevidence-theorem-identity-0.3",
        "elaboratedSerialization": claim_preview,
        "universeParams": [],
        "binders": [
            {"name": name, "kind": "default", "typeSerialization": binder_type}
            for name in var_names
        ],
        "constantNames": constant_names or ["Rat", "Eq"],
    }


def _capability_replay_profile(request: dict[str, Any]) -> dict[str, Any]:
    """Exact capability defaults for theorem-producing kernel replay.

    Unknown or missing capability ids are preserved (not remapped) so
    ``decide_exact_kernel_replay`` can fail closed on the real id.
    """
    raw_cap = request.get("capability")
    cap = str(raw_cap) if isinstance(raw_cap, str) and raw_cap else ""
    if cap == "algebra.rational_equality":
        return {
            "capability_id": cap,
            "claim_class": "soundResult",
            "checker_package": "MathEvidence.Checkers.RationalEquality",
            "checker_module": "MathEvidence.Checkers.RationalEquality.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": "certified_rational_replay",
            "fixture": "basic_sympy",
        }
    if cap == "algebra.linear_algebra":
        op = str(request.get("operation") or "inverse_witness")
        fixture = {
            "inverse_witness": "inv",
            "system_solution": "sys",
            "kernel_vector": "ker",
            "det_identity": "det",
        }.get(op, "inv")
        claim_class = "soundResult" if op == "det_identity" else "witness"
        return {
            "capability_id": cap,
            "claim_class": claim_class,
            "checker_package": "MathEvidence.Checkers.LinearAlgebra",
            "checker_module": "MathEvidence.Checkers.LinearAlgebra.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": f"certified_linear_algebra_{fixture}",
            "fixture": fixture,
        }
    if cap == "logic.finite_counterexample":
        pred = request.get("predicate") or {}
        domains = pred.get("domains") if isinstance(pred, dict) else None
        fixture = "nat_eq0"
        if isinstance(domains, list) and len(domains) == 1:
            first = domains[0] if isinstance(domains[0], dict) else {}
            if str(first.get("ty") or "").lower() == "bool":
                fixture = "bool_false"
        return {
            "capability_id": cap,
            "claim_class": "refutation",
            "checker_package": "MathEvidence.Checkers.Counterexample",
            "checker_module": "MathEvidence.Checkers.Counterexample.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": f"certified_counterexample_{fixture}",
            "fixture": fixture,
        }
    if cap == "analysis.analytic_calculus":
        # Exact generators invoke Soundness.checkDeriv*_sound / checkODE_sound,
        # not OfflineFixtures.replaySound (fixture-only packaging).
        return {
            "capability_id": cap,
            "claim_class": "soundResult",
            "checker_package": "MathEvidence.Checkers.AnalyticCalculus",
            "checker_module": "MathEvidence.Checkers.AnalyticCalculus.Soundness",
            "soundness_theorem": "checkDeriv_sound",
            "declaration_default": "certified_analytic_replay_product",
            "fixture": "cert_product",
        }
    if cap == "algebra.ideal_membership_witness":
        requested = str(request.get("requestedClaim") or "witness")
        return {
            "capability_id": cap,
            "claim_class": requested if requested in {"witness", "soundResult"} else "candidate",
            "checker_package": "MathEvidence.Checkers.IdealMembership",
            "checker_module": "MathEvidence.Checkers.IdealMembership.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": "certified_ideal_membership_exact",
            "fixture": None,
        }
    if cap == "algebra.formal_rational_calculus":
        requested = str(request.get("requestedClaim") or "soundResult")
        return {
            "capability_id": cap,
            "claim_class": requested if requested in {"witness", "soundResult"} else "candidate",
            "checker_package": "MathEvidence.Checkers.Calculus",
            "checker_module": "MathEvidence.Checkers.Calculus.ReplaySound",
            "soundness_theorem": "replaySound",
            "declaration_default": "certified_formal_rational_calculus",
            "fixture": None,
        }
    # Preserve the caller-supplied id (or empty) so policy can fail closed honestly.
    return {
        "capability_id": cap or "unknown",
        "claim_class": "candidate",
        "checker_package": "n/a",
        "checker_module": "n/a",
        "soundness_theorem": "n/a",
        "declaration_default": "unconfigured_exact_replay",
        "fixture": None,
    }


def _safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned


def _candidate_declaration(base_name: str, candidate_digest: str) -> str:
    """Stable candidate-namespaced declaration, idempotent across replays."""
    base = _safe_ident(base_name)
    suffix = candidate_digest[7:23]
    marker = f"_{suffix}"
    return base if base.endswith(marker) else f"{base}{marker}"


def _source_revision(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
        value = (proc.stdout or "").strip()
        if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value):
            return value
    except (OSError, subprocess.SubprocessError):
        pass
    return "workspace"


def _run_process(
    command: list[str], *, root: Path, timeout: float = 600.0
) -> subprocess.CompletedProcess[str]:
    """Argv-only Lake/Lean invocation with bounded execution (no shell)."""
    limits = ResourceLimits(
        max_wall_time_ms=int(timeout * 1000),
        max_output_bytes=16_777_216,
    )
    try:
        result = run_bounded(
            command,
            cwd=root,
            limits=limits,
            # Preserve host toolchain env for Lake/elan; still argv-only, no shell.
            # Offline proxy/credential stripping remains in filter_environ for
            # callers that opt into use_env_allowlist=True (offline/security tests).
            use_env_allowlist=False,
            extra_env={"MATHEVIDENCE_OFFLINE": os.environ.get("MATHEVIDENCE_OFFLINE", "1")},
        )
    except AdapterError as exc:
        if exc.code == "resource_limit_exceeded":
            raise _kr_error(
                "resource_limit_exceeded",
                exc.message,
                **(exc.details or {}),
            ) from exc
        if exc.code == "replay_dependency_missing":
            raise _kr_error(
                "replay_dependency_missing",
                exc.message,
                **(exc.details or {}),
            ) from exc
        raise _kr_error("kernel_rejected", exc.message, **(exc.details or {})) from exc
    return subprocess.CompletedProcess(
        args=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )

@contextmanager
def _module_lock(root: Path, module_name: str, timeout: float = 600.0) -> Iterator[None]:
    """Cross-process lock for one deterministic generated replay module."""
    lock_root = root / ".lake" / "build" / "mathevidence-replay-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(module_name.encode("utf-8")).hexdigest()
    lock_path = lock_root / f"{key}.lock"
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                os.write(fd, f"pid={os.getpid()}\nmodule={module_name}\n".encode("utf-8"))
            finally:
                os.close(fd)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > max(1800.0, timeout * 2):
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise _kr_error(
                    "resource_limit_exceeded",
                    f"timed out waiting for replay module lock: {module_name}",
                )
            time.sleep(0.05)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _parse_identity_report(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("authority") == "Lean.Environment ConstantInfo":
            return value
    raise _kr_error(
        "kernel_rejected",
        "declaration identity inspector emitted no Lean.Environment report",
        stdout=stdout[-2000:],
    )


def _compile_and_inspect(
    *,
    root: Path,
    lake: Path,
    module_name: str,
    declaration_name: str,
    source_text: str,
    environment_lock_digest_value: str,
) -> tuple[dict[str, Any], str, str]:
    module_parts = module_name.split(".")
    source_path = root.joinpath(*module_parts).with_suffix(".lean")
    # Lake places package oleans under ``.lake/build/lib/<Module>/…`` (same root
    # as MathEvidence.*). Never use a ``lean/`` subdirectory here: on
    # case-insensitive filesystems that path shadows the toolchain ``Lean``
    # module in ``LEAN_PATH`` and makes ``lake env lean`` fail with missing
    # ``Lean.olean``.
    olean_path = (root / ".lake" / "build" / "lib").joinpath(*module_parts).with_suffix(
        ".olean"
    )
    source_path.parent.mkdir(parents=True, exist_ok=True)
    olean_path.parent.mkdir(parents=True, exist_ok=True)

    with _module_lock(root, module_name):
        source_path.write_text(source_text, encoding="utf-8", newline="\n")
        try:
            build = _run_process(
                [
                    str(lake),
                    "build",
                    "MathEvidenceCheckers",
                    "mathevidence-declaration-identity",
                ],
                root=root,
            )
            if build.returncode != 0:
                raise _kr_error(
                    "replay_dependency_missing",
                    f"failed to build replay dependencies (exit {build.returncode})",
                    stdout=(build.stdout or "")[-2000:],
                    stderr=(build.stderr or "")[-2000:],
                )

            compile_proc = _run_process(
                [str(lake), "env", "lean", "-o", str(olean_path), str(source_path)],
                root=root,
            )
            if compile_proc.returncode != 0:
                raise _kr_error(
                    "kernel_rejected",
                    f"lake env lean exit {compile_proc.returncode}; refusing theorem status",
                    stdout=(compile_proc.stdout or "")[-3000:],
                    stderr=(compile_proc.stderr or "")[-3000:],
                )

            inspect_proc = _run_process(
                [
                    str(lake),
                    "exe",
                    "mathevidence-declaration-identity",
                    # Lake 5 / Lean 4.14 forwards a bare ``--`` into the exe argv.
                    # DeclarationIdentity treats unknown flags as fatal (exit 2),
                    # so pass program flags directly after the exe name.
                    "--module",
                    module_name,
                    "--declaration",
                    declaration_name,
                    "--environment-lock-digest",
                    environment_lock_digest_value,
                ],
                root=root,
            )
            if inspect_proc.returncode != 0:
                raise _kr_error(
                    "kernel_rejected",
                    f"declaration identity inspection exit {inspect_proc.returncode}",
                    stdout=(inspect_proc.stdout or "")[-3000:],
                    stderr=(inspect_proc.stderr or "")[-3000:],
                )
            return (
                _parse_identity_report(inspect_proc.stdout or ""),
                (compile_proc.stdout or "") + (inspect_proc.stdout or ""),
                (compile_proc.stderr or "") + (inspect_proc.stderr or ""),
            )
        finally:
            source_path.unlink(missing_ok=True)
            olean_path.unlink(missing_ok=True)


def run_kernel_replay(
    *,
    bundle_dir: Path | str,
    repo_root: Path | None = None,
    declaration_name: str | None = None,
    source_revision: str | None = None,
    require_lean: bool = True,
    allowed_axioms: tuple[str, ...] = ALLOWED_AXIOMS_DEFAULT,
    out_record_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Produce a strict Certification Record for an exact supported candidate.

    ``require_lean`` is retained for API compatibility, but theorem-level output
    always requires Lean. Setting it false never enables a metadata-only success.
    """
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    path = Path(bundle_dir)
    if not path.is_dir():
        raise _kr_error("bundle_not_found", str(path))

    try:
        verify_bundle_offline(path, strict=True)
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        if "digest" in message.lower():
            raise _kr_error("content_digest_mismatch", message) from exc
        raise _kr_error("manifest_invalid", message) from exc

    request = load_role_json(path, "request")
    certificate = load_role_json(path, "certificate")
    if not isinstance(request, dict):
        raise _kr_error("request_decode_failed", "request role missing or invalid")
    if not isinstance(certificate, dict):
        raise _kr_error("certificate_decode_failed", "certificate role missing or invalid")

    request_digest = request.get("requestDigest")
    if not isinstance(request_digest, str) or _SHA256_RE.fullmatch(request_digest) is None:
        raise _kr_error("request_digest_mismatch", "requestDigest missing or non-canonical")

    profile = _capability_replay_profile(request)
    capability_id = str(profile["capability_id"])
    decision = decide_exact_kernel_replay(capability_id)
    if not decision.ok:
        raise _kr_error(
            decision.code or "assurance_mode_unavailable",
            decision.message,
            capability=capability_id,
            historicalFixture=profile.get("fixture"),
        )

    manifest_path = find_role_path(path, "manifest")
    if manifest_path is None:
        raise _kr_error("bundle_not_found", "missing manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_digest = manifest.get("bundleDigest") or compute_bundle_digest(manifest)
    if not isinstance(candidate_digest, str) or _SHA256_RE.fullmatch(candidate_digest) is None:
        raise _kr_error("manifest_invalid", "candidate bundleDigest missing or non-canonical")

    claim_class = str(profile["claim_class"])
    if claim_class not in {"witness", "soundResult", "refutation"}:
        raise _kr_error(
            "assurance_mode_unavailable",
            f"requested claim {claim_class!r} is not theorem-producing for {capability_id}",
        )

    base_declaration = declaration_name or str(profile["declaration_default"])
    decl = _candidate_declaration(base_declaration, candidate_digest)
    module_name = f"MathEvidence.Generated.Replay.{decl}"
    try:
        source_text, generator_meta = _generate_exact_source(
            capability_id=capability_id,
            module_name=module_name,
            declaration_name=decl,
            request=request,
            certificate=certificate,
            candidate_bundle_digest=candidate_digest,
        )
    except Exception as exc:  # noqa: BLE001
        raise _kr_error("certificate_decode_failed", str(exc)) from exc
    binding = exact_binding(decision.policy)
    for key in ("generatorId", "generatorVersion", "grammarVersion"):
        expected = binding.get(key)
        if isinstance(expected, str) and generator_meta.get(key) != expected:
            raise _kr_error(
                "assurance_mode_unavailable",
                f"generated {key} disagrees with registry exactBinding",
                expected=expected,
                actual=generator_meta.get(key),
            )

    try:
        lock = current_capability_environment_lock(root, capability_id)
    except Exception as exc:  # noqa: BLE001
        raise _kr_error("environment_mismatch", str(exc)) from exc
    lock_digest = environment_lock_digest(lock)

    locked_revision = str(lock.get("projectRevision") or "workspace")
    if source_revision is not None and source_revision != locked_revision:
        raise _kr_error(
            "environment_mismatch",
            "requested source revision disagrees with source-bound environment lock",
            requestedRevision=source_revision,
            lockedRevision=locked_revision,
        )
    source_rev = locked_revision
    if source_rev == "workspace":
        source_rev = _source_revision(root)

    lake = find_lake(root)
    if lake is None:
        raise _kr_error(
            "theorem_elaboration_failed",
            f"lake not found (require_lean={require_lean}); refusing theorem-level status",
        )

    identity_report, lean_stdout, lean_stderr = _compile_and_inspect(
        root=root,
        lake=lake,
        module_name=module_name,
        declaration_name=decl,
        source_text=source_text,
        environment_lock_digest_value=lock_digest,
    )

    if identity_report.get("declarationName") != decl:
        raise _kr_error("goal_claim_mismatch", "inspected declaration name mismatch")
    if identity_report.get("environmentLockDigest") != lock_digest:
        raise _kr_error("environment_mismatch", "Lean identity environment-lock mismatch")
    type_identity = identity_report.get("typeIdentity")
    if not isinstance(type_identity, dict):
        raise _kr_error("kernel_rejected", "Lean identity report missing typeIdentity")
    if type_identity.get("schemaVersion") != THEOREM_IDENTITY_SCHEMA_VERSION:
        raise _kr_error("kernel_rejected", "Lean theorem identity schema version mismatch")
    if type_identity.get("serializerVersion") != THEOREM_IDENTITY_SERIALIZER_VERSION:
        raise _kr_error("kernel_rejected", "Lean theorem identity serializer version mismatch")
    emitted_type_digest = identity_report.get("theoremTypeDigest")
    if theorem_type_digest(type_identity) != emitted_type_digest:
        raise _kr_error(
            "goal_claim_mismatch",
            "Python recomputation of Lean-emitted theorem type identity disagrees",
        )
    proof_digest = identity_report.get("proofDeclarationDigest")
    if not isinstance(proof_digest, str) or _SHA256_RE.fullmatch(proof_digest) is None:
        raise _kr_error("kernel_rejected", "Lean identity report missing proof digest")

    axioms_raw = identity_report.get("axioms")
    if not isinstance(axioms_raw, list) or not all(isinstance(a, str) for a in axioms_raw):
        raise _kr_error("kernel_rejected", "Lean identity report has invalid axiom set")
    axioms = sorted(set(axioms_raw))
    if not axiom_policy_ok(axioms, allowed_axioms):
        raise _kr_error(
            "unexpected_axiom",
            f"axioms {axioms} not subset of {list(allowed_axioms)}",
        )

    type_dig = str(emitted_type_digest)
    target = build_replay_target(
        module_name=module_name,
        declaration_name=decl,
        theorem_type_canonical=str(type_identity["elaboratedSerialization"]),
        theorem_type_digest_value=type_dig,
        source_revision=source_rev,
        source_file=f"MathEvidence/Generated/Replay/{decl}.lean",
        environment_lock_digest_value=lock_digest,
        request_digest=request_digest,
        capability_id=capability_id,
        capability_version=str(request.get("capabilityVersion") or "0.1.0"),
        candidate_bundle_digest=candidate_digest,
    )

    theorem_identity = theorem_identity_payload(
        declaration_name=decl,
        theorem_type_digest_value=type_dig,
        proof_declaration_digest=proof_digest,
        environment_lock_digest_value=lock_digest,
        environment_lock=lock,
        elaborated_serialization=str(type_identity["elaboratedSerialization"]),
        universe_params=list(type_identity.get("universeParams") or []),
        binders=list(type_identity.get("binders") or []),
        constant_names=list(type_identity.get("constantNames") or []),
    )

    checker = {
        "package": profile["checker_package"],
        "module": profile["checker_module"],
        "name": "checkBool",
        "version": "0.1.0",
        "soundnessTheorem": profile["soundness_theorem"],
    }
    checker_evaluation = {
        "schemaVersion": "0.3.0",
        "requestDigest": request_digest,
        "candidateBundleDigest": candidate_digest,
        "resultStatus": "soundness_verified",
        "assuranceMode": "kernel_replay",
        "claimEstablished": claim_class,
        "checker": checker,
        "detail": "exact candidate compiled; declaration identity read from Lean.Environment",
    }
    axiom_report = {
        "schemaVersion": "0.3.0",
        "status": "compiled",
        "declarationName": decl,
        "axioms": axioms,
        "allowedAxioms": list(allowed_axioms),
        "axiomDigests": [],
    }

    certificate_path = find_role_path(path, "certificate")
    if certificate_path is None:
        raise _kr_error("certificate_decode_failed", "candidate has no certificate role")
    outcome = map_claim_to_outcome(claim_class=claim_class, claim_established=claim_class)
    if outcome in {"proved", "refuted"} and not outcome_allowed(capability_id, outcome):
        raise _kr_error(
            "assurance_mode_unavailable",
            f"outcome {outcome!r} is not in registry allowedOutcomes for {capability_id}",
        )
    certification_receipt = {
        "schemaVersion": "0.4.0",
        "requestDigest": request_digest,
        "candidateBundleDigest": candidate_digest,
        "certificateContentDigest": file_digest(certificate_path),
        "capability": {
            "id": capability_id,
            "version": str(request.get("capabilityVersion") or "0.1.0"),
        },
        "checker": checker,
        "soundnessTheorem": profile["soundness_theorem"],
        "claimRequested": claim_class,
        "claimEstablished": claim_class,
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
        "outcome": outcome,
        "theoremTypeDigest": type_dig,
        "proofDeclarationDigest": proof_digest,
        "environmentLockDigest": lock_digest,
        "unresolvedObligations": [],
        "toolchain": {
            "leanVersion": lock["leanVersion"],
            "lakeVersion": lock["lakeVersion"],
            "mathlibVersion": lock["mathlibRevision"],
        },
        "canonicalClaimHash": request_digest,
        "candidateHash": candidate_digest,
        "generatorId": generator_meta["generatorId"],
        "generatorVersion": generator_meta["generatorVersion"],
        "grammarVersion": generator_meta["grammarVersion"],
        "generatedSourceHash": generator_meta["generatedSourceHash"],
        "theoremOrDeclarationIdentity": decl,
        "toolchainContractDigest": lock_digest,
        "dependencyLockDigest": lock_digest,
        "artifactHashes": {
            "certificate.cjson": file_digest(certificate_path),
            "theoremTypeDigest": type_dig,
            "proofDeclarationDigest": proof_digest,
            "generatedSourceHash": generator_meta["generatedSourceHash"],
        },
        "replayManifestHash": NA_SENTINEL,
        "executionPolicyId": _EXECUTION_POLICY_ID,
        "assuranceTier": "exact",
        "detail": "theorem/proof identity emitted by mathevidence-declaration-identity",
    }

    record_dir = Path(out_record_dir) if out_record_dir else (
        root / "evidence" / "store" / "certifications" / "_pending" / decl
    )
    if record_dir.exists():
        shutil.rmtree(record_dir)
    try:
        manifest_out = write_certification_record(
            record_dir,
            candidate_bundle_digest=candidate_digest,
            request_digest=request_digest,
            capability_id=capability_id,
            capability_version=str(request.get("capabilityVersion") or "0.1.0"),
            claim_class=claim_class,
            result_status="soundness_verified",
            assurance_mode="kernel_replay",
            replay_target=target,
            checker_evaluation=checker_evaluation,
            theorem_identity=theorem_identity,
            axiom_report=axiom_report,
            certification_receipt=certification_receipt,
        )
        verify_bundle_offline(record_dir, strict=True)
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(record_dir, ignore_errors=True)
        raise _kr_error(
            "manifest_invalid",
            f"generated Certification Record failed strict verification: {exc}",
        ) from exc

    cert_digest = manifest_out["certificationDigest"]
    return {
        "ok": True,
        "resultStatus": "soundness_verified",
        "assuranceMode": "kernel_replay",
        "claimEstablished": claim_class,
        "capability": capability_id,
        "candidateBundleDigest": candidate_digest,
        "certificationRecordDigest": cert_digest,
        "certificationId": f"cert_sha256_{cert_digest[7:]}",
        "theoremTypeDigest": type_dig,
        "proofDeclarationDigest": proof_digest,
        "environmentLockDigest": lock_digest,
        "declarationName": decl,
        "axioms": axioms,
        "leanOk": True,
        "identityAuthority": "Lean.Environment ConstantInfo",
        "recordDir": str(record_dir),
        "leanStdout": lean_stdout[-4000:],
        "leanStderr": lean_stderr[-4000:],
    }
