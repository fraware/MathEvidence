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
from adapters.common.environment_lock import current_capability_environment_lock
from adapters.common.exact_replay.pipeline import generate_module, verify
from adapters.common.kernel_replay import (
    ALLOWED_AXIOMS_DEFAULT,
    _compile_and_inspect,
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


def _execute(case: Any) -> dict[str, Any]:
    matrix._assert_policy(case)
    module = generate_module(
        capability_id=case.capability,
        request=case.request,
        certificate=case.certificate,
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
    report, lean_stdout, lean_stderr = _compile_and_inspect(
        root=ROOT,
        lake=lake,
        module_name=module.module_name,
        declaration_name=module.declaration_name,
        source_text=module.source_text,
        environment_lock_digest_value=lock_digest,
    )

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
