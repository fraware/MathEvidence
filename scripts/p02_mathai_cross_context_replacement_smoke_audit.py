#!/usr/bin/env python3
"""Audit MATH-AI cross-context replacement feasibility-smoke evidence.

This analysis is post-classification. It may read construction metadata because
the frozen v2 classifier has already assigned classes without those labels.
Transferred signatures remain fixed from the original P02 study.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import p02_classify_native_v2_raw as v1

EXPECTED_SIGNATURES = {
    "SOURCE_CORRUPTION": "FRONTEND_REJECT",
    "INVALID_PROOF": "ENVIRONMENT_OR_ELAB_REJECT",
    "PROHIBITED_PLACEHOLDER": "TOOLCHAIN_ACCEPT_POLICY_REJECT",
    "WRONG_TARGET": "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
}
CLEAN_CLASS = "TOOLCHAIN_ACCEPT_TARGET_MATCH"
CONTEXTS = ("RX1", "RX2", "RX3")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def observed_class(classified_root: Path, case_id: str) -> str:
    row = read_json(classified_root / "cases" / case_id / "classification.json")
    return str(row["derived_native_class"])


def candidate_returncode(raw_root: Path, case_id: str) -> int | None:
    row = read_json(raw_root / "cases" / case_id / "observations.json")
    candidate = row.get("candidate") or {}
    return candidate.get("returncode")


def target_returncode(raw_root: Path, case_id: str) -> int | None:
    row = read_json(raw_root / "cases" / case_id / "observations.json")
    target = row.get("target_probe")
    return None if target is None else target.get("returncode")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--classified", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    raw = args.raw.resolve()
    classified = args.classified.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"audit output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    raw_integrity = read_json(raw / "INTEGRITY_MANIFEST.json")
    raw_files = v1.inventory(raw)
    raw_digest = v1.canonical_digest({"files": raw_files})
    if raw_integrity.get("files") != raw_files:
        raise RuntimeError("raw inventory mismatch")
    if raw_integrity.get("bundle_digest") != raw_digest:
        raise RuntimeError("raw digest mismatch")

    classified_integrity = read_json(classified / "INTEGRITY_MANIFEST.json")
    classified_files = v1.inventory(classified)
    classified_digest = v1.canonical_digest({"files": classified_files})
    if classified_integrity.get("files") != classified_files:
        raise RuntimeError("classified inventory mismatch")
    if classified_integrity.get("bundle_digest") != classified_digest:
        raise RuntimeError("classified digest mismatch")

    construction = read_json(raw / "CONSTRUCTION_CHECKS.json")
    if not construction.get("all_singleton_local"):
        raise RuntimeError("construction locality check failed")
    if not construction.get("all_pairwise_repairs_commute"):
        raise RuntimeError("repair commutativity check failed")

    context_rows: list[dict[str, Any]] = []
    all_feasible = True
    for ctx in CONTEXTS:
        clean_id = f"{ctx}-SMOKE-CLEAN"
        clean_class = observed_class(classified, clean_id)
        clean_native_ok = candidate_returncode(raw, clean_id) == 0
        clean_target_ok = target_returncode(raw, clean_id) == 0

        singleton_rows: list[dict[str, Any]] = []
        repair_rows: list[dict[str, Any]] = []
        for mechanism, expected in EXPECTED_SIGNATURES.items():
            case_id = f"{ctx}-SMOKE-{mechanism}"
            repair_id = f"{case_id}__REPAIR"
            observed = observed_class(classified, case_id)
            repaired = observed_class(classified, repair_id)

            candidate_rc = candidate_returncode(raw, case_id)
            target_rc = target_returncode(raw, case_id)
            mutation_operational = (
                candidate_rc != 0
                if mechanism in {"SOURCE_CORRUPTION", "INVALID_PROOF"}
                else observed == expected
            )
            if mechanism == "WRONG_TARGET":
                mutation_operational = candidate_rc == 0 and target_rc not in (None, 0)
            if mechanism == "PROHIBITED_PLACEHOLDER":
                mutation_operational = candidate_rc == 0 and observed == expected

            singleton_rows.append(
                {
                    "mechanism": mechanism,
                    "expected_transferred_class": expected,
                    "observed_class": observed,
                    "transferred_signature_match": observed == expected,
                    "candidate_returncode": candidate_rc,
                    "target_probe_returncode": target_rc,
                    "mutation_operational": mutation_operational,
                }
            )
            repair_rows.append(
                {
                    "mechanism": mechanism,
                    "observed_repair_class": repaired,
                    "repair_returns_clean_class": repaired == CLEAN_CLASS,
                    "repair_candidate_returncode": candidate_returncode(raw, repair_id),
                    "repair_target_probe_returncode": target_returncode(raw, repair_id),
                }
            )

        wrong = next(
            row for row in singleton_rows if row["mechanism"] == "WRONG_TARGET"
        )
        context_feasible = (
            clean_native_ok
            and clean_target_ok
            and clean_class == CLEAN_CLASS
            and all(row["mutation_operational"] for row in singleton_rows)
            and all(row["repair_returns_clean_class"] for row in repair_rows)
            and wrong["observed_class"] == "TOOLCHAIN_ACCEPT_TARGET_MISMATCH"
        )
        all_feasible = all_feasible and context_feasible
        context_rows.append(
            {
                "context_id": ctx,
                "feasible": context_feasible,
                "clean_class": clean_class,
                "clean_candidate_returncode": candidate_returncode(raw, clean_id),
                "clean_target_probe_returncode": target_returncode(raw, clean_id),
                "transferred_singleton_matches": sum(
                    bool(row["transferred_signature_match"])
                    for row in singleton_rows
                ),
                "singleton_checks": singleton_rows,
                "inverse_repair_checks": repair_rows,
            }
        )

    summary = {
        "schema_version": "p02_mathai_cross_context_replacement_smoke_audit_v1",
        "status": "FEASIBILITY_SMOKE_AUDITED",
        "publication_claim_eligible": False,
        "all_three_contexts_feasible": all_feasible,
        "transferred_prediction_modified": False,
        "expected_transferred_signatures": EXPECTED_SIGNATURES,
        "raw_bundle_digest": raw_digest,
        "classified_bundle_digest": classified_digest,
        "contexts": context_rows,
        "full_compound_lattice_executed": False,
        "non_claims": [
            "Feasibility does not establish compound-state transfer.",
            "Singleton disagreements, if any, are retained as transfer failures.",
            "No context is removed for producing an unfavorable transferred signature.",
            "No 48-state or 96-edge replication claim is made from smoke evidence.",
        ],
    }
    v1.json_dump(out / "SMOKE_AUDIT.json", summary)

    files = v1.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_replacement_smoke_audit_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": v1.canonical_digest({"files": files}),
    }
    v1.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))

    return 0 if all_feasible else 2


if __name__ == "__main__":
    raise SystemExit(main())
