#!/usr/bin/env python3
"""Ensure adversarial seed catalog meets TESTING_AND_CI.md §2.4 coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT / "benchmarks" / "adversarial" / "seed"
MANIFEST = SEED_DIR / "manifest.json"

REQUIRED_CATEGORIES = {
    "denominator_zero",
    "coercion_change",
    "inequality_strictness",
    "variable_shadowing",
    "swapped_matrix_dimensions",
    "transposed_indexing",
    "hidden_branch",
    "subdomain_candidate",
    "incomplete_solution_family",
    "approx_to_exact",
    "wrong_request_hash",
    "truncated_certificate",
    "duplicate_keys",
    "unknown_schema_version",
    "excessive_nesting",
    "oversized_integer",
    "path_traversal",
    "malicious_filename",
    "wrong_capability_certificate",
}


def main() -> int:
    if not MANIFEST.is_file():
        print(f"missing {MANIFEST}", file=sys.stderr)
        return 1
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    cats = {c.get("category") for c in cases}
    missing = sorted(REQUIRED_CATEGORIES - cats)
    if missing:
        print("missing adversarial categories:", ", ".join(missing), file=sys.stderr)
        return 1
    for case in cases:
        rel = case.get("path")
        if not rel or not (SEED_DIR / rel).is_file():
            print(f"missing seed file for {case}", file=sys.stderr)
            return 1
    print(f"adversarial seed ok ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
