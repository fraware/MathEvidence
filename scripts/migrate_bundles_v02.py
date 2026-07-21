#!/usr/bin/env python3
"""Migrate committed v0.1 evidence bundles to Evidence Bundle v0.2 (.cjson).

Reads existing request/candidate/certificate (preferring .cjson then .json),
rewrites via ``write_bundle``, and removes legacy role ``.json`` files that
were superseded. Dual-read remains available for trees not listed here.

Preserves on-disk ``theorem.lean``, ``axiom-report``, and ``checker-receipt``
when present so content digests stay faithful to authored roles.

Usage:
  python scripts/migrate_bundles_v02.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import (  # noqa: E402
    VERIFIED_RESULT_STATUSES,
    find_role_path,
    load_role_json,
    verify_bundle_offline,
    write_bundle,
)

# Full Evidence Bundle trees (request + certificate + manifest). Case-only
# conformance dirs (case.json + request.json) and federation emit JSON are
# intentionally excluded — they are not theorem-binding bundle layouts.
MIGRATE: list[Path] = [
    # Examples — rational / LA / CEX (prior pass) + calculus / ideal
    ROOT / "evidence" / "examples" / "rational_equality_basic",
    ROOT / "evidence" / "examples" / "rational_equality_mathematica_offline",
    ROOT / "evidence" / "examples" / "linear_algebra_inverse_2x2",
    ROOT / "evidence" / "examples" / "finite_counterexample_nat_eq0",
    ROOT / "evidence" / "examples" / "calculus_antiderivative_x2",
    ROOT / "evidence" / "examples" / "calculus_derivative_mathematica_offline",
    ROOT / "evidence" / "examples" / "calculus_derivative_x2",
    ROOT / "evidence" / "examples" / "calculus_ode_y_eq_x",
    ROOT / "evidence" / "examples" / "calculus_recurrence_n",
    ROOT / "evidence" / "examples" / "ideal_membership_mathematica_offline_x2m1",
    ROOT / "evidence" / "examples" / "ideal_membership_mathematica_offline_xy",
    ROOT / "evidence" / "examples" / "ideal_membership_sage_offline_x2m1",
    ROOT / "evidence" / "examples" / "ideal_membership_sage_offline_xy",
    # rfc0001 conformance bundles
    ROOT / "evidence" / "conformance" / "rfc0001" / "valid_identity" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "redundant_condition" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "variable_permutation" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "large_coeffs" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "false_identity" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "hash_mismatch" / "bundle",
    ROOT / "evidence" / "conformance" / "rfc0001" / "missing_condition" / "bundle",
    # linear algebra conformance
    ROOT / "evidence" / "conformance" / "linear_algebra" / "inverse_witness_2x2" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "exact_system_solution" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "det_identity" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "kernel_vector" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "singular_inverse_rejected" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "hash_mismatch" / "bundle",
    # finite counterexample conformance
    ROOT / "evidence" / "conformance" / "finite_counterexample" / "simple_false_universal" / "bundle",
    ROOT / "evidence" / "conformance" / "finite_counterexample" / "out_of_domain_rejected" / "bundle",
    ROOT / "evidence" / "conformance" / "finite_counterexample" / "witness_type_mismatch" / "bundle",
    ROOT / "evidence" / "conformance" / "finite_counterexample" / "hash_mismatch" / "bundle",
    # symbolic calculus conformance
    ROOT / "evidence" / "conformance" / "symbolic_calculus" / "calculus_antiderivative_x2" / "bundle",
    ROOT / "evidence" / "conformance" / "symbolic_calculus" / "calculus_derivative_x2" / "bundle",
    ROOT / "evidence" / "conformance" / "symbolic_calculus" / "calculus_ode_y_eq_x" / "bundle",
    ROOT / "evidence" / "conformance" / "symbolic_calculus" / "calculus_recurrence_n" / "bundle",
]

# Bundles whose requestDigest is intentionally forged (adversarial fixtures).
SKIP_VERIFY = {
    ROOT / "evidence" / "conformance" / "rfc0001" / "hash_mismatch" / "bundle",
    ROOT / "evidence" / "conformance" / "linear_algebra" / "hash_mismatch" / "bundle",
    ROOT / "evidence" / "conformance" / "finite_counterexample" / "hash_mismatch" / "bundle",
}

LEGACY_ROLE_STEMS = (
    "request",
    "candidate",
    "certificate",
    "manifest",
    "checker-receipt",
    "axiom-report",
)


def migrate_one(bundle_dir: Path) -> None:
    if not bundle_dir.is_dir():
        raise FileNotFoundError(bundle_dir)
    request = load_role_json(bundle_dir, "request")
    certificate = load_role_json(bundle_dir, "certificate")
    candidate_path = find_role_path(bundle_dir, "candidate")
    if candidate_path is None:
        candidate: dict = {}
    else:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        if not isinstance(candidate, dict):
            candidate = {"value": candidate}

    # Preserve prior resultStatus when honest (write_bundle coerces verified).
    manifest_path = find_role_path(bundle_dir, "manifest")
    result_status = "computed"
    claim_class = "candidate"
    assurance_mode = "kernel_replay"
    lean_version = "4.x-pending"
    library_revision = "workspace"
    checker_version = "0.1.0"
    if manifest_path is not None:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        result_status = str(old.get("resultStatus", result_status))
        claim_class = str(old.get("claimClass", claim_class))
        assurance_mode = str(old.get("assuranceMode", assurance_mode))
        prov = old.get("provenance") or {}
        lean_version = str(prov.get("leanVersion", lean_version))
        library_revision = str(prov.get("libraryRevision", library_revision))
        checker_version = str(prov.get("checkerVersion", checker_version))

    readme = None
    readme_path = bundle_dir / "README.md"
    if readme_path.is_file():
        readme = readme_path.read_text(encoding="utf-8")

    theorem_lean = None
    theorem_path = bundle_dir / "theorem.lean"
    if theorem_path.is_file():
        theorem_lean = theorem_path.read_text(encoding="utf-8")

    axiom_report = None
    if find_role_path(bundle_dir, "axiom-report") is not None:
        axiom_report = load_role_json(bundle_dir, "axiom-report")

    checker_receipt = None
    if find_role_path(bundle_dir, "checker-receipt") is not None:
        checker_receipt = load_role_json(bundle_dir, "checker-receipt")
        # Lean replay may have written a receipt after a prior migrate; honor it.
        established = checker_receipt.get("claimEstablished")
        receipt_status = checker_receipt.get("resultStatus")
        if (
            established
            and isinstance(receipt_status, str)
            and receipt_status in VERIFIED_RESULT_STATUSES
        ):
            result_status = receipt_status
            claim_class = str(established)

    write_bundle(
        bundle_dir,
        request=request,
        candidate=candidate,
        certificate=certificate,
        result_status=result_status,
        claim_class=claim_class,
        assurance_mode=assurance_mode,
        lean_version=lean_version,
        library_revision=library_revision,
        checker_version=checker_version,
        readme=readme,
        theorem_lean=theorem_lean,
        axiom_report=axiom_report,
        checker_receipt=checker_receipt,
    )

    # Drop superseded legacy role JSON (cjson is authoritative).
    for stem in LEGACY_ROLE_STEMS:
        legacy = bundle_dir / f"{stem}.json"
        if legacy.is_file() and (bundle_dir / f"{stem}.cjson").is_file():
            legacy.unlink()

    if bundle_dir in SKIP_VERIFY:
        print(
            f"OK {bundle_dir.relative_to(ROOT).as_posix()} "
            "(skip verify: adversarial digest)"
        )
        return

    warnings = verify_bundle_offline(bundle_dir)
    print(f"OK {bundle_dir.relative_to(ROOT).as_posix()} warnings={warnings}")


def main() -> int:
    for path in MIGRATE:
        migrate_one(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
