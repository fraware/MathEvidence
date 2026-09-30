#!/usr/bin/env python3
"""Audit richer-feedback aliasing on the frozen P02 MATH-AI evidence.

This is a post-review descriptive analysis. It does not alter the frozen
classifier, corpus, intervention categories, or primary 32-state/80-edge
results. It asks whether each masked-active repair that preserves the coarse
operational class also preserves the stored native diagnostic/probe payload.

The comparison removes only run-specific metadata that is not part of the
diagnostic content presented by Lean: process command paths, elapsed time,
case identifiers, and generated temporary .lean file paths. Return codes,
timeouts, spawn errors, stdout, stderr, source-empty status, declaration-probe
results, and target-probe results are retained.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_BASELINE_RAW_DIGEST = (
    "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
)
EXPECTED_REPAIR_RAW_DIGEST = (
    "sha256:40b4c6a1397edb126774cf38ff06cbc54c73b216e9dbe4ef9c8a81d3e2fe4857"
)
EXPECTED_TRANSITION_DIGEST = (
    "sha256:0b44d509271db2cbfff53d2bf1f83121681a372d4431f329529e4b070b1eb68c"
)
EXPECTED_MASKED_EDGES = 34
EXPECTED_PRIMARY_CLASS_PRESERVED = 34

_TMP_LEAN_PATH_RE = re.compile(r"/tmp/[^\s:'\"\n]+\.lean")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(payload)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == "INTEGRITY_MANIFEST.json":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return rows


def verify_bundle(root: Path, expected_digest: str, label: str) -> None:
    manifest = read_json(root / "INTEGRITY_MANIFEST.json")
    files = inventory(root)
    if manifest.get("files") != files:
        raise RuntimeError(f"{label}: inventory differs from integrity manifest")
    observed = canonical_digest({"files": files})
    if manifest.get("bundle_digest") != observed:
        raise RuntimeError(f"{label}: integrity-manifest digest mismatch")
    if observed != expected_digest:
        raise RuntimeError(
            f"{label}: unexpected bundle digest {observed}; expected {expected_digest}"
        )


def normalize_text(text: str | None) -> str | None:
    if text is None:
        return None
    return _TMP_LEAN_PATH_RE.sub("<CANDIDATE>.lean", text)


def process_payload(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "returncode": value.get("returncode"),
        "spawn_error": value.get("spawn_error"),
        "stdout": normalize_text(value.get("stdout")),
        "stderr": normalize_text(value.get("stderr")),
        "timed_out": value.get("timed_out"),
    }


def feedback_payload(observation: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_empty": observation.get("source_empty"),
        "candidate": process_payload(observation.get("candidate")),
        "declaration_probe": process_payload(observation.get("declaration_probe")),
        "target_probe": process_payload(observation.get("target_probe")),
    }


def changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for top in ("source_empty", "candidate", "declaration_probe", "target_probe"):
        if before.get(top) == after.get(top):
            continue
        if top == "source_empty" or before.get(top) is None or after.get(top) is None:
            changed.append(top)
            continue
        for key in ("returncode", "spawn_error", "stdout", "stderr", "timed_out"):
            if before[top].get(key) != after[top].get(key):
                changed.append(f"{top}.{key}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--math-evidence-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    evidence_root = args.math_evidence_root.resolve() / "evidence" / "p02_native_v2"
    baseline_root = evidence_root / "raw_first_full"
    repair_root = evidence_root / "repair_raw_first_full"
    transition_root = evidence_root / "transition_analysis_first_full"

    verify_bundle(baseline_root, EXPECTED_BASELINE_RAW_DIGEST, "baseline raw")
    verify_bundle(repair_root, EXPECTED_REPAIR_RAW_DIGEST, "repair raw")
    verify_bundle(transition_root, EXPECTED_TRANSITION_DIGEST, "transition analysis")

    edge_table = transition_root / "REPAIR_EDGE_TABLE.csv"
    with edge_table.open("r", encoding="utf-8", newline="") as handle:
        edges = list(csv.DictReader(handle))

    masked = [row for row in edges if row["category"] == "masked_later_repair"]
    if len(masked) != EXPECTED_MASKED_EDGES:
        raise RuntimeError(
            f"masked-edge cardinality changed: {len(masked)} != {EXPECTED_MASKED_EDGES}"
        )
    if sum(row["class_changed"] == "False" for row in masked) != EXPECTED_PRIMARY_CLASS_PRESERVED:
        raise RuntimeError("primary masked-edge class-preservation result changed")

    rows: list[dict[str, Any]] = []
    by_mechanism: dict[str, Counter[str]] = defaultdict(Counter)
    by_before_class: dict[str, Counter[str]] = defaultdict(Counter)

    for edge in masked:
        baseline_case_id = edge["baseline_case_id"]
        edge_id = edge["edge_id"]
        before_obs = read_json(
            baseline_root / "cases" / baseline_case_id / "observations.json"
        )
        after_obs = read_json(repair_root / "cases" / edge_id / "observations.json")
        before_payload = feedback_payload(before_obs)
        after_payload = feedback_payload(after_obs)
        same = before_payload == after_payload
        fields = changed_fields(before_payload, after_payload)
        row = {
            "edge_id": edge_id,
            "baseline_case_id": baseline_case_id,
            "repair_mechanism": edge["repair_mechanism"],
            "before_class": edge["before_class"],
            "after_class": edge["after_class"],
            "operational_class_preserved": edge["class_changed"] == "False",
            "normalized_feedback_identical": same,
            "changed_fields": fields,
        }
        rows.append(row)

        status = "identical" if same else "different"
        by_mechanism[edge["repair_mechanism"]]["n"] += 1
        by_mechanism[edge["repair_mechanism"]][status] += 1
        by_before_class[edge["before_class"]]["n"] += 1
        by_before_class[edge["before_class"]][status] += 1

    identical = sum(bool(row["normalized_feedback_identical"]) for row in rows)
    summary = {
        "schema_version": "p02_mathai_raw_feedback_aliasing_postreview_v1",
        "analysis_role": "post_review_descriptive_audit",
        "publication_claim_eligible": False,
        "primary_evidence_unchanged": True,
        "comparison_definition": {
            "included": [
                "source_empty",
                "candidate returncode/spawn_error/stdout/stderr/timed_out",
                "declaration-probe returncode/spawn_error/stdout/stderr/timed_out",
                "target-probe returncode/spawn_error/stdout/stderr/timed_out",
            ],
            "excluded": [
                "process command",
                "elapsed_seconds",
                "case_id",
            ],
            "normalization": [
                "replace generated /tmp/.../*.lean paths in stdout/stderr with <CANDIDATE>.lean"
            ],
        },
        "evidence_digests": {
            "baseline_raw": EXPECTED_BASELINE_RAW_DIGEST,
            "repair_raw": EXPECTED_REPAIR_RAW_DIGEST,
            "transition_analysis": EXPECTED_TRANSITION_DIGEST,
        },
        "masked_active_edges": {
            "n": len(rows),
            "operational_class_preserved": sum(
                bool(row["operational_class_preserved"]) for row in rows
            ),
            "normalized_feedback_identical": identical,
            "normalized_feedback_different": len(rows) - identical,
        },
        "by_repair_mechanism": {
            key: dict(value) for key, value in sorted(by_mechanism.items())
        },
        "by_before_class": {
            key: dict(value) for key, value in sorted(by_before_class.items())
        },
        "non_claims": [
            "This audit was designed and executed after reviewer feedback; it is not preregistered.",
            "Exact equality of this stored payload is not equality of Lean internal state.",
            "The result does not estimate prevalence in natural Lean developments or agent trajectories.",
            "A richer or different observation interface may distinguish additional edges.",
        ],
        "rows": rows,
    }

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "RAW_FEEDBACK_ALIASING_AUDIT.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (out / "RAW_FEEDBACK_ALIASING_EDGES.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "edge_id",
                "baseline_case_id",
                "repair_mechanism",
                "before_class",
                "after_class",
                "operational_class_preserved",
                "normalized_feedback_identical",
                "changed_fields",
            ],
        )
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            flat["changed_fields"] = "+".join(row["changed_fields"])
            writer.writerow(flat)

    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
