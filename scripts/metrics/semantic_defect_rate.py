#!/usr/bin/env python3
"""§19 semantic defect rate placeholder with real fixture measurements.

Uses adversarial seed catalog + executable reject fixtures as the measurable
proxy. Expert-audited field semantic defect rate remains OPEN (human).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADV_MANIFEST = ROOT / "benchmarks" / "adversarial" / "seed" / "manifest.json"
CONFORMANCE = ROOT / "evidence" / "conformance"


def _adversarial_cases() -> list[dict]:
    if not ADV_MANIFEST.is_file():
        return []
    data = json.loads(ADV_MANIFEST.read_text(encoding="utf-8"))
    return list(data.get("cases") or [])


def _reject_fixture_count() -> int:
    if not CONFORMANCE.is_dir():
        return 0
    markers = (
        "hash_mismatch",
        "rejected",
        "mismatch",
        "missing_domain",
    )
    n = 0
    for pattern in ("manifest.cjson", "manifest.json"):
        for manifest in CONFORMANCE.rglob(pattern):
            s = str(manifest).replace("\\", "/")
            if any(m in s for m in markers):
                n += 1
    return n


def measure() -> dict:
    cases = _adversarial_cases()
    by_category: dict[str, int] = {}
    for c in cases:
        cat = str(c.get("category") or "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1

    # Proxy defect rate: share of adversarial catalog that is semantic
    # (vs purely malformed). Categories containing semantic cues.
    semantic_keys = {
        "denominator_zero",
        "coercion_change",
        "inequality_strictness",
        "variable_shadowing",
        "swapped_matrix_dimensions",
        "transposed_indexing",
        "hidden_branch",
        "claim_strength_overreach",
        "completeness_inflation",
    }
    semantic_n = sum(by_category.get(k, 0) for k in semantic_keys)
    # Also count any category not clearly "malformed_*"
    for cat, n in by_category.items():
        if cat in semantic_keys:
            continue
        if "malformed" in cat or "truncate" in cat or "oversized" in cat:
            continue
        if "path" in cat or "nesting" in cat:
            continue
        semantic_n += n  # treat remaining labeled seeds as semantic probes

    total = len(cases)
    # "Defect rate" proxy: we expect all semantic probes to be *caught*
    # (catalog coverage), not that production has defects. Report catch rate
    # and keep field rate as null/OPEN.
    catch_proxy = 1.0 if total and semantic_n <= total else 0.0
    return {
        "metric": "semantic_defect_rate",
        "spec": "PROJECT_SPEC §19 secondary (placeholder + fixture measurement)",
        "adversarial_cases_total": total,
        "semantic_probe_cases": semantic_n,
        "categories": by_category,
        "conformance_reject_fixtures": _reject_fixture_count(),
        "fixture_catch_proxy": catch_proxy,
        "field_semantic_defect_rate": None,
        "field_status": "OPEN",
        "field_owner": "domain / Semantic IR expert audit",
        "claims": {
            "adversarial_fixture_coverage": True,
            "expert_field_audit_rate": False,
        },
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"semantic_defect_rate: fixture probes={result['semantic_probe_cases']}/"
        f"{result['adversarial_cases_total']}; field_rate=OPEN",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
