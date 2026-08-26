#!/usr/bin/env python3
"""Post-classification transition analysis for the sealed P02 native v2 campaign.

This script is intentionally downstream of classification. It joins construction/
repair metadata only after both baseline and repair observations have been
classified by the frozen classifier. It does not modify or re-run classification.

The analysis derives each mechanism's native signature from its single-fault
control, uses the frozen classifier pipeline order to predict the visible class
for every mechanism subset, and then checks all 32 lattice states, all 80
one-mechanism repair edges, and the five-step cumulative repair trajectory.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import p02_classify_native_v2_raw as frozen

SCHEMA_VERSION = "p02_native_transition_analysis_v2"
EXPECTED_BASELINE_RAW_DIGEST = "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
EXPECTED_BASELINE_CLASSIFIED_DIGEST = "sha256:7de9a7fabbb8fb6ab104c7bbdb63f3b7b3d5bf41a64ed1ffac6d8328c3c12de3"
EXPECTED_REPAIR_RAW_DIGEST = "sha256:40b4c6a1397edb126774cf38ff06cbc54c73b216e9dbe4ef9c8a81d3e2fe4857"
EXPECTED_REPAIR_CLASSIFIED_DIGEST = "sha256:96fc867e07e6b130fbd4cf3217a2c555c61f08b42f9506ac370a2b3b11233782"
EXPECTED_PLAN_DIGEST = "sha256:0b610ed6bd984acf6403046e5adf56ed5f8ae0d9a6fbce4178c6a8ede4e20565"
EXPECTED_CORPUS_DIGEST = "sha256:fe356ed2f5d4bcf653c5cedaa37922e2248547434fe30b746fbcf10ca73bc199"

# This is the decision progression encoded by the already-frozen classifier.
# SOURCE_EMPTY and UNKNOWN are deliberately excluded from the progression and
# cause this analysis to fail closed if they occur in lattice/repair states.
PIPELINE_CLASSES: tuple[str, ...] = (
    "FRONTEND_REJECT",
    "ENVIRONMENT_OR_ELAB_REJECT",
    "TOOLCHAIN_ACCEPT_POLICY_REJECT",
    "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
    "TOOLCHAIN_ACCEPT_TARGET_MATCH",
)
PIPELINE_RANK = {name: i for i, name in enumerate(PIPELINE_CLASSES)}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_bundle(root: Path, expected_digest: str, label: str) -> str:
    manifest = read_json(root / "INTEGRITY_MANIFEST.json")
    files = frozen.inventory(root)
    if manifest.get("files") != files:
        raise RuntimeError(f"{label} inventory mismatch")
    digest = frozen.canonical_digest({"files": files})
    if manifest.get("bundle_digest") != digest:
        raise RuntimeError(f"{label} manifest digest mismatch")
    if digest != expected_digest:
        raise RuntimeError(f"{label} unexpected digest: {digest} != {expected_digest}")
    return digest


def class_for(root: Path, case_id: str) -> str:
    row = read_json(root / "cases" / case_id / "classification.json")
    observed = row.get("derived_native_class")
    if observed not in frozen.NATIVE_CLASSES:
        raise RuntimeError(f"invalid class for {case_id}: {observed}")
    return str(observed)


def predict_class(mechanisms: Iterable[str], signatures: dict[str, str], clean_class: str) -> str:
    classes = [signatures[m] for m in mechanisms]
    if not classes:
        return clean_class
    for cls in classes:
        if cls not in PIPELINE_RANK:
            raise RuntimeError(f"non-pipeline mechanism signature: {cls}")
    return min(classes, key=PIPELINE_RANK.__getitem__)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def safe_rate(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-raw", type=Path, required=True)
    parser.add_argument("--baseline-classified", type=Path, required=True)
    parser.add_argument("--repair-raw", type=Path, required=True)
    parser.add_argument("--repair-classified", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    baseline_raw = args.baseline_raw.resolve()
    baseline_classified = args.baseline_classified.resolve()
    repair_raw = args.repair_raw.resolve()
    repair_classified = args.repair_classified.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"analysis output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    identities = {
        "baseline_raw_bundle_digest": verify_bundle(baseline_raw, EXPECTED_BASELINE_RAW_DIGEST, "baseline raw"),
        "baseline_classified_bundle_digest": verify_bundle(baseline_classified, EXPECTED_BASELINE_CLASSIFIED_DIGEST, "baseline classified"),
        "repair_raw_bundle_digest": verify_bundle(repair_raw, EXPECTED_REPAIR_RAW_DIGEST, "repair raw"),
        "repair_classified_bundle_digest": verify_bundle(repair_classified, EXPECTED_REPAIR_CLASSIFIED_DIGEST, "repair classified"),
    }

    corpus = read_json(baseline_raw / "CORPUS_MANIFEST.json")
    if corpus.get("observed_corpus_digest") != EXPECTED_CORPUS_DIGEST:
        raise RuntimeError("corpus digest mismatch")
    lattice_cases = [
        row for row in corpus.get("cases", [])
        if row.get("role") in {"clean_control", "single_fault", "compound_fault"}
    ]
    if len(lattice_cases) != 32:
        raise RuntimeError(f"expected 32 lattice cases, found {len(lattice_cases)}")

    subset_to_case: dict[frozenset[str], str] = {}
    baseline_classes: dict[str, str] = {}
    for row in lattice_cases:
        case_id = str(row["case_id"])
        subset = frozenset(str(x) for x in row.get("mechanisms", []))
        if subset in subset_to_case:
            raise RuntimeError(f"duplicate mechanism subset in corpus: {sorted(subset)}")
        subset_to_case[subset] = case_id
        baseline_classes[case_id] = class_for(baseline_classified, case_id)

    clean_id = subset_to_case.get(frozenset())
    if clean_id is None:
        raise RuntimeError("clean lattice control missing")
    clean_class = baseline_classes[clean_id]
    if clean_class != "TOOLCHAIN_ACCEPT_TARGET_MATCH":
        raise RuntimeError(f"clean control is not native target-match: {clean_class}")

    single_fault_rows = [row for row in lattice_cases if row.get("role") == "single_fault"]
    if len(single_fault_rows) != 5:
        raise RuntimeError(f"expected five single-fault controls, found {len(single_fault_rows)}")
    signatures: dict[str, str] = {}
    single_fault_case_ids: dict[str, str] = {}
    for row in single_fault_rows:
        mechanisms = [str(x) for x in row.get("mechanisms", [])]
        if len(mechanisms) != 1:
            raise RuntimeError(f"invalid single-fault metadata: {row}")
        mechanism = mechanisms[0]
        case_id = str(row["case_id"])
        signature = baseline_classes[case_id]
        if signature not in PIPELINE_RANK:
            raise RuntimeError(f"single-fault signature outside pipeline: {mechanism} -> {signature}")
        signatures[mechanism] = signature
        single_fault_case_ids[mechanism] = case_id
    if len(signatures) != 5:
        raise RuntimeError("single-fault mechanism cardinality mismatch")

    inert_mechanisms = sorted(m for m, cls in signatures.items() if cls == clean_class)
    active_mechanisms = sorted(m for m, cls in signatures.items() if cls != clean_class)

    state_rows: list[dict[str, Any]] = []
    state_violations: list[dict[str, Any]] = []
    for row in lattice_cases:
        case_id = str(row["case_id"])
        mechanisms = [str(x) for x in row.get("mechanisms", [])]
        observed = baseline_classes[case_id]
        if observed not in PIPELINE_RANK:
            raise RuntimeError(f"lattice state outside pipeline: {case_id} -> {observed}")
        predicted = predict_class(mechanisms, signatures, clean_class)
        item = {
            "case_id": case_id,
            "role": row.get("role"),
            "mechanisms": "+".join(mechanisms),
            "n_mechanisms": len(mechanisms),
            "observed_class": observed,
            "predicted_class": predicted,
            "model_match": observed == predicted,
        }
        state_rows.append(item)
        if not item["model_match"]:
            state_violations.append(item)

    repair_plan = read_json(repair_raw / "REPAIR_PLAN.json")
    if repair_plan.get("plan_digest") != EXPECTED_PLAN_DIGEST:
        raise RuntimeError("repair plan digest mismatch")
    edges = repair_plan.get("edges", [])
    if len(edges) != 80:
        raise RuntimeError(f"expected 80 repair edges, found {len(edges)}")

    edge_rows: list[dict[str, Any]] = []
    edge_violations: list[dict[str, Any]] = []
    per_mechanism = defaultdict(lambda: Counter(total=0, class_changed=0, class_preserved=0, model_match=0))
    category_counts = Counter()
    category_matches = Counter()

    for edge in edges:
        edge_id = str(edge["edge_id"])
        before_case_id = str(edge["case_id"])
        repair_mechanism = str(edge["repair_mechanism"])
        before_mechanisms = [str(x) for x in edge.get("mechanisms_before", [])]
        after_mechanisms = [str(x) for x in edge.get("mechanisms_after", [])]
        before_class = baseline_classes[before_case_id]
        after_class = class_for(repair_classified, edge_id)
        if before_class not in PIPELINE_RANK or after_class not in PIPELINE_RANK:
            raise RuntimeError(f"repair edge outside pipeline: {edge_id}: {before_class} -> {after_class}")

        predicted_before = predict_class(before_mechanisms, signatures, clean_class)
        predicted_after = predict_class(after_mechanisms, signatures, clean_class)
        after_subset = frozenset(after_mechanisms)
        independent_after_id = subset_to_case.get(after_subset)
        if independent_after_id is None:
            raise RuntimeError(f"no independent lattice state for {edge_id}")
        independent_after_class = baseline_classes[independent_after_id]

        active_before = [m for m in before_mechanisms if signatures[m] != clean_class]
        if repair_mechanism in inert_mechanisms:
            category = "inert_mechanism_repair"
        else:
            best_rank = min(PIPELINE_RANK[signatures[m]] for m in active_before)
            repair_rank = PIPELINE_RANK[signatures[repair_mechanism]]
            n_best = sum(PIPELINE_RANK[signatures[m]] == best_rank for m in active_before)
            if repair_rank == best_rank and n_best == 1:
                category = "visible_blocker_repair"
            elif repair_rank == best_rank:
                category = "co_visible_blocker_repair"
            else:
                category = "masked_later_repair"

        class_changed = after_class != before_class
        model_match = (
            before_class == predicted_before
            and after_class == predicted_after
            and after_class == independent_after_class
        )
        expected_change = predicted_after != predicted_before
        change_pattern_match = class_changed == expected_change

        item = {
            "edge_id": edge_id,
            "baseline_case_id": before_case_id,
            "repair_mechanism": repair_mechanism,
            "category": category,
            "mechanisms_before": "+".join(before_mechanisms),
            "mechanisms_after": "+".join(after_mechanisms),
            "before_class": before_class,
            "after_class": after_class,
            "predicted_before_class": predicted_before,
            "predicted_after_class": predicted_after,
            "independent_after_case_id": independent_after_id,
            "independent_after_class": independent_after_class,
            "class_changed": class_changed,
            "expected_class_change": expected_change,
            "change_pattern_match": change_pattern_match,
            "model_match": model_match,
        }
        edge_rows.append(item)
        if not model_match or not change_pattern_match:
            edge_violations.append(item)

        bucket = per_mechanism[repair_mechanism]
        bucket["total"] += 1
        bucket["class_changed" if class_changed else "class_preserved"] += 1
        bucket["model_match"] += int(model_match and change_pattern_match)
        category_counts[category] += 1
        category_matches[category] += int(model_match and change_pattern_match)

    if set(per_mechanism) != set(signatures):
        raise RuntimeError("repair mechanism coverage mismatch")
    for mechanism, counts in per_mechanism.items():
        if counts["total"] != 16:
            raise RuntimeError(f"expected 16 edges for {mechanism}, found {counts['total']}")

    cumulative_dirs = sorted(
        p for p in (repair_raw / "cases").iterdir()
        if p.is_dir() and read_json(p / "repair_meta.json").get("role") == "cumulative_repair"
    )
    cumulative_meta = [read_json(p / "repair_meta.json") for p in cumulative_dirs]
    cumulative_meta.sort(key=lambda x: int(x["step"]))
    if [int(x["step"]) for x in cumulative_meta] != [1, 2, 3, 4, 5]:
        raise RuntimeError("cumulative repair steps are not exactly 1..5")

    full_subset = frozenset(signatures)
    full_case_id = subset_to_case.get(full_subset)
    if full_case_id is None:
        raise RuntimeError("full five-mechanism lattice state missing")
    cumulative_rows: list[dict[str, Any]] = []
    cumulative_violations: list[dict[str, Any]] = []
    previous_class = baseline_classes[full_case_id]
    previous_mechanisms = sorted(full_subset)
    for meta in cumulative_meta:
        step = int(meta["step"])
        repair_mechanism = str(meta["repair_mechanism"])
        case_id = f"ND2-CUMULATIVE-{step}-{repair_mechanism}"
        after_class = class_for(repair_classified, case_id)
        remaining = [str(x) for x in meta.get("mechanisms_after", [])]
        predicted_before = predict_class(previous_mechanisms, signatures, clean_class)
        predicted_after = predict_class(remaining, signatures, clean_class)
        item = {
            "step": step,
            "case_id": case_id,
            "repair_mechanism": repair_mechanism,
            "mechanisms_before": "+".join(previous_mechanisms),
            "mechanisms_after": "+".join(remaining),
            "before_class": previous_class,
            "after_class": after_class,
            "predicted_before_class": predicted_before,
            "predicted_after_class": predicted_after,
            "class_changed": after_class != previous_class,
            "expected_class_change": predicted_after != predicted_before,
            "model_match": previous_class == predicted_before and after_class == predicted_after,
        }
        cumulative_rows.append(item)
        if not item["model_match"] or item["class_changed"] != item["expected_class_change"]:
            cumulative_violations.append(item)
        previous_class = after_class
        previous_mechanisms = remaining

    per_mechanism_summary = {
        mechanism: {
            "native_single_fault_signature": signatures[mechanism],
            "native_inert": mechanism in inert_mechanisms,
            **dict(counts),
            "class_change_rate": safe_rate(counts["class_changed"], counts["total"]),
            "model_match_rate": safe_rate(counts["model_match"], counts["total"]),
        }
        for mechanism, counts in sorted(per_mechanism.items())
    }

    def category_metric(name: str) -> dict[str, Any]:
        n = category_counts[name]
        matched = category_matches[name]
        rows = [r for r in edge_rows if r["category"] == name]
        changed = sum(bool(r["class_changed"]) for r in rows)
        preserved = n - changed
        return {
            "n": n,
            "model_match": matched,
            "model_match_rate": safe_rate(matched, n),
            "class_changed": changed,
            "class_preserved": preserved,
            "class_change_rate": safe_rate(changed, n),
        }

    state_matches = len(state_rows) - len(state_violations)
    edge_matches = len(edge_rows) - len(edge_violations)
    cumulative_matches = len(cumulative_rows) - len(cumulative_violations)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "POSTCLASSIFICATION_ANALYZED_NOT_ADVERSARIAL_REVIEWED",
        "publication_claim_eligible": False,
        "classifier_version": "p02_native_observation_classifier_v1",
        "frozen_classifier_blob_sha": "681309212d1b045558277b167a99dc28c45bef71",
        "analysis_uses_metadata_only_after_classification": True,
        "pipeline_class_order": list(PIPELINE_CLASSES),
        "clean_class": clean_class,
        "mechanism_native_signatures": dict(sorted(signatures.items())),
        "active_mechanisms": active_mechanisms,
        "native_inert_mechanisms": inert_mechanisms,
        "baseline_lattice": {
            "n_states": len(state_rows),
            "model_matches": state_matches,
            "model_violations": len(state_violations),
            "exact_match_rate": safe_rate(state_matches, len(state_rows)),
        },
        "counterfactual_repairs": {
            "n_edges": len(edge_rows),
            "model_matches": edge_matches,
            "model_violations": len(edge_violations),
            "exact_match_rate": safe_rate(edge_matches, len(edge_rows)),
            "by_category": {
                name: category_metric(name)
                for name in (
                    "visible_blocker_repair",
                    "co_visible_blocker_repair",
                    "masked_later_repair",
                    "inert_mechanism_repair",
                )
            },
            "by_mechanism": per_mechanism_summary,
        },
        "cumulative_repair": {
            "n_steps": len(cumulative_rows),
            "model_matches": cumulative_matches,
            "model_violations": len(cumulative_violations),
            "exact_match_rate": safe_rate(cumulative_matches, len(cumulative_rows)),
            "start_class": baseline_classes[full_case_id],
            "end_class": cumulative_rows[-1]["after_class"],
            "observed_path": [baseline_classes[full_case_id]] + [r["after_class"] for r in cumulative_rows],
            "repair_order": [r["repair_mechanism"] for r in cumulative_rows],
        },
        "violations": {
            "baseline_states": state_violations,
            "counterfactual_edges": edge_violations,
            "cumulative_steps": cumulative_violations,
        },
        **identities,
        "plan_digest": EXPECTED_PLAN_DIGEST,
        "corpus_digest": EXPECTED_CORPUS_DIGEST,
        "non_claims": [
            "Exact rates here are exhaustive finite checks over this constructed 32-state corpus, not population estimates.",
            "A model match does not establish proof-generation capability or semantic correctness beyond the declared target-match predicate.",
            "Native-inert mechanisms are reported separately and are not counted as masked active blockers.",
            "No S6 semantic-admissibility automation or claim is made.",
            "Publication eligibility remains false pending adversarial review and manuscript-level claim audit."
        ],
    }

    frozen.json_dump(out / "TRANSITION_ANALYSIS.json", summary)
    write_csv(
        out / "STATE_TABLE.csv",
        state_rows,
        ["case_id", "role", "mechanisms", "n_mechanisms", "observed_class", "predicted_class", "model_match"],
    )
    write_csv(
        out / "REPAIR_EDGE_TABLE.csv",
        edge_rows,
        [
            "edge_id", "baseline_case_id", "repair_mechanism", "category",
            "mechanisms_before", "mechanisms_after", "before_class", "after_class",
            "predicted_before_class", "predicted_after_class", "independent_after_case_id",
            "independent_after_class", "class_changed", "expected_class_change",
            "change_pattern_match", "model_match",
        ],
    )
    write_csv(
        out / "CUMULATIVE_TRAJECTORY.csv",
        cumulative_rows,
        [
            "step", "case_id", "repair_mechanism", "mechanisms_before", "mechanisms_after",
            "before_class", "after_class", "predicted_before_class", "predicted_after_class",
            "class_changed", "expected_class_change", "model_match",
        ],
    )

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_native_transition_analysis_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
