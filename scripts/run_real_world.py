#!/usr/bin/env python3
"""Validate and smoke-run real-world bottleneck obligations (TESTING_AND_CI §5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RW = ROOT / "benchmarks" / "real_world"
MANIFEST = RW / "manifest.json"

REQUIRED_FIELDS = {
    "id",
    "bottleneckRef",
    "domain",
    "capability",
    "summary",
    "leanOnlyApproach",
    "whyExternal",
    "expectedClaimStrength",
    "permittedAssumptions",
    "contaminationStatus",
}


def main() -> int:
    if not MANIFEST.is_file():
        print(f"missing {MANIFEST}", file=sys.stderr)
        return 1
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if len(cases) < 10:
        print(f"need ≥10 real-world cases, found {len(cases)}", file=sys.stderr)
        return 1
    errors = 0
    for case in cases:
        missing = sorted(REQUIRED_FIELDS - set(case))
        if missing:
            print(f"{case.get('id')}: missing {missing}", file=sys.stderr)
            errors += 1
            continue
        rel = case.get("path")
        if not rel or not (RW / rel).is_file():
            print(f"{case.get('id')}: missing path {rel}", file=sys.stderr)
            errors += 1
            continue
        payload: dict[str, Any] = json.loads((RW / rel).read_text(encoding="utf-8"))
        if payload.get("id") != case["id"]:
            print(f"{case['id']}: id mismatch in {rel}", file=sys.stderr)
            errors += 1
    if errors:
        print(f"real-world suite failed ({errors})", file=sys.stderr)
        return 1
    print(f"real-world suite ok ({len(cases)} obligations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
