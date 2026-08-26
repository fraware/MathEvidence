#!/usr/bin/env python3
"""Release gate: execute the CR exact matrix through the production Lean path.

The case/coverage matrix lives in ``run_cr_exact_lean_e2e`` and is derived from
registry maturity plus production plugin operation whitelists. This executor
intentionally uses the same source staging, ``lake env lean -o`` compilation,
and Lean.Environment declaration inspection primitive as production
``kernel_replay``. A standalone /tmp Lean invocation is not equivalent for
Lean 4.14 ``native_decide`` modules and must not be used as release authority.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import adapters.common.exact_replay.plugins  # noqa: F401
from adapters.common.canonical import (
    bind_request_digest,
    canonical_dumps,
    request_binding_payload,
    verify_request_digest,
)
from adapters.common.environment_lock import current_capability_environment_lock
from adapters.common.exact_replay.pipeline import generate_module, verify
from adapters.common.kernel_replay import (
    ALLOWED_AXIOMS_DEFAULT,
    KernelReplayError,
    _compile_and_inspect,
    _run_process,
    axiom_policy_ok,
    find_lake,
)
from adapters.common.theorem_identity import environment_lock_digest

ROOT = Path(__file__).resolve().parents[2]


def _load_matrix() -> ModuleType:
    """Load the checked-in case matrix explicitly, independent of package install layout."""
    path = ROOT / "scripts" / "ci" / "run_cr_exact_lean_e2e.py"
    module_name = "mathevidence_cr_exact_matrix"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load exact E2E matrix from {path}")

    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
        raise
    return module


matrix = _load_matrix()
BUNDLE_DIGEST = matrix.BUNDLE_DIGEST


def _canonical_case_payload(case: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind synthetic matrix fixtures exactly as a real Candidate Bundle request.

    Matrix cases use deterministic placeholder digests to keep fixture construction
    readable. Release execution must not compile those placeholders: production
    Candidate Bundles bind ``requestDigest`` to the canonical request payload before
    exact replay. Recompute that binding here and synchronize the certificate so the
    E2E gate exercises the same semantic contract rather than an invalid fixture.
    """
    request = bind_request_digest(case.request)
    request_digest = verify_request_digest(request)
    certificate = dict(case.certificate)
    certificate["requestDigest"] = request_digest
    return request, certificate


def _rational_binding_diagnostic_source(case: Any, module: Any) -> str | None:
    """Build a non-authoritative companion that prints Lean's reconstructed binding.

    The production theorem source is attempted first and remains the only acceptance
    path. This companion is generated only for diagnostics after a failure. It stops
    before the first theorem and therefore cannot establish or inspect a theorem.
    """
    if case.capability != "algebra.rational_equality":
        return None
    decl = module.declaration_name
    marker = f"theorem {decl}_request_binding :"
    prefix, found, _ = module.source_text.partition(marker)
    if not found:
        return None
    return (
        prefix
        + f"""
/- Diagnostic-only companion: never Certification Record authority. -/
#eval do
  match MathEvidence.Core.JsonCanonical.canonicalString
      (MathEvidence.Checkers.RationalEquality.Wire.claimToRequestJson {decl}_claim) with
  | .ok s => IO.println ("MATHEVIDENCE_DIAG_CANONICAL=" ++ s)
  | .error e => IO.println ("MATHEVIDENCE_DIAG_CANONICAL_ERROR=" ++ toString e)

#eval IO.println ("MATHEVIDENCE_DIAG_DIGEST=" ++ {decl}_req.requestDigest.value)
"""
    )


def _extract_prefixed_line(stdout: str, prefix: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _rational_binding_diagnostic(
    *, case: Any, module: Any, request: dict[str, Any], lake: Path
) -> dict[str, Any]:
    """Run a failure-only Lean/Python binding comparison with no theorem authority."""
    source = _rational_binding_diagnostic_source(case, module)
    if source is None:
        return {"status": "diagnostic_unavailable", "reason": "source_marker_missing"}

    diagnostic_module = f"MathEvidence.Generated.Replay.diagnostic_{case.name}"
    source_path = ROOT.joinpath(*diagnostic_module.split(".")).with_suffix(".lean")
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8", newline="\n")
    try:
        proc = _run_process([str(lake), "env", "lean", str(source_path)], root=ROOT)
    finally:
        source_path.unlink(missing_ok=True)

    lean_canonical = _extract_prefixed_line(
        proc.stdout or "", "MATHEVIDENCE_DIAG_CANONICAL="
    )
    lean_digest = _extract_prefixed_line(proc.stdout or "", "MATHEVIDENCE_DIAG_DIGEST=")
    python_canonical = canonical_dumps(request_binding_payload(request))
    python_digest = str(request["requestDigest"])
    return {
        "status": "diagnostic_only_non_authoritative",
        "returnCode": proc.returncode,
        "leanCanonical": lean_canonical,
        "pythonCanonical": python_canonical,
        "canonicalMatch": (
            lean_canonical == python_canonical if lean_canonical is not None else None
        ),
        "leanRequestDigest": lean_digest,
        "pythonRequestDigest": python_digest,
        "digestMatch": lean_digest == python_digest if lean_digest is not None else None,
        "stdoutTail": (proc.stdout or "")[-3000:],
        "stderrTail": (proc.stderr or "")[-3000:],
    }


def _execute(case: Any) -> dict[str, Any]:
    matrix._assert_policy(case)
    request, certificate = _canonical_case_payload(case)
    module = generate_module(
        capability_id=case.capability,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE_DIGEST,
        module_name=f"MathEvidence.Generated.Replay.release_{case.name}",
        declaration_name=f"release_{case.name}",
    )
    metadata = verify(module)
    if not metadata.ok:
        raise RuntimeError(
            f"{case.capability}::{case.form}: generated module metadata failed: "
            f"{metadata.detail}"
        )
    if "OfflineFixtures" in module.source_text:
        raise RuntimeError(
            f"{case.capability}::{case.form}: generated exact source references OfflineFixtures"
        )

    lake = find_lake(ROOT)
    if lake is None:
        raise RuntimeError("lake is unavailable; exact release E2E cannot run")

    lock = current_capability_environment_lock(ROOT, case.capability)
    lock_digest = environment_lock_digest(lock)
    try:
        report, lean_stdout, lean_stderr = _compile_and_inspect(
            root=ROOT,
            lake=lake,
            module_name=module.module_name,
            declaration_name=module.declaration_name,
            source_text=module.source_text,
            environment_lock_digest_value=lock_digest,
        )
    except KernelReplayError as exc:
        diagnostics: dict[str, Any] = {}
        if case.capability == "algebra.rational_equality":
            try:
                diagnostics = _rational_binding_diagnostic(
                    case=case,
                    module=module,
                    request=request,
                    lake=lake,
                )
            except Exception as diagnostic_exc:  # noqa: BLE001
                diagnostics = {
                    "status": "diagnostic_failed",
                    "error": f"{type(diagnostic_exc).__name__}: {diagnostic_exc}",
                }

        # Preserve the structured Lean/Lake failure context in CI. Diagnostics
        # are explicitly non-authoritative and run only after acceptance failed.
        print(
            json.dumps(
                {
                    "schemaVersion": "0.2.0",
                    "status": "exact_e2e_failure",
                    "case": case.name,
                    "capability": case.capability,
                    "form": case.form,
                    "requestDigest": request["requestDigest"],
                    "errorCode": exc.code,
                    "message": exc.message,
                    "details": exc.details or {},
                    "diagnostics": diagnostics,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise

    if report.get("authority") != "Lean.Environment ConstantInfo":
        raise RuntimeError(
            f"{case.capability}::{case.form}: declaration inspector authority mismatch"
        )
    if report.get("declarationName") != module.declaration_name:
        raise RuntimeError(
            f"{case.capability}::{case.form}: declaration identity mismatch: "
            f"{report.get('declarationName')!r}"
        )
    if report.get("environmentLockDigest") != lock_digest:
        raise RuntimeError(
            f"{case.capability}::{case.form}: environment-lock identity mismatch"
        )

    axioms = report.get("axioms")
    if not isinstance(axioms, list) or not all(isinstance(a, str) for a in axioms):
        raise RuntimeError(f"{case.capability}::{case.form}: invalid axiom report")
    axioms = sorted(set(axioms))
    if not axiom_policy_ok(axioms, ALLOWED_AXIOMS_DEFAULT):
        raise RuntimeError(
            f"{case.capability}::{case.form}: unexpected axioms {axioms}"
        )

    theorem_type_digest = report.get("theoremTypeDigest")
    proof_digest = report.get("proofDeclarationDigest")
    if not isinstance(theorem_type_digest, str) or not theorem_type_digest.startswith("sha256:"):
        raise RuntimeError(
            f"{case.capability}::{case.form}: missing Lean theorem type digest"
        )
    if not isinstance(proof_digest, str) or not proof_digest.startswith("sha256:"):
        raise RuntimeError(
            f"{case.capability}::{case.form}: missing Lean proof declaration digest"
        )

    return {
        "case": case.name,
        "capability": case.capability,
        "form": case.form,
        "declaration": module.declaration_name,
        "sourceHash": module.source_hash,
        "generatorId": module.generator_id,
        "generatorVersion": module.generator_version,
        "grammarVersion": module.grammar_version,
        "requestDigest": module.request_digest,
        "candidateBundleDigest": module.candidate_bundle_digest,
        "environmentLockDigest": lock_digest,
        "theoremTypeDigest": theorem_type_digest,
        "proofDeclarationDigest": proof_digest,
        "axioms": axioms,
        "identityAuthority": report.get("authority"),
        "leanOutputBytes": len((lean_stdout + lean_stderr).encode("utf-8")),
        "status": "lean_candidate_identity_verified",
    }


def main() -> int:
    cases = matrix._cases()
    matrix._assert_coverage(cases)

    results: list[dict[str, Any]] = []
    for case in cases:
        result = _execute(case)
        results.append(result)
        print(
            f"[exact-e2e-production] {case.capability}::{case.form}: "
            f"OK ({result['theoremTypeDigest']})"
        )

    print(json.dumps({"schemaVersion": "0.3.0", "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
