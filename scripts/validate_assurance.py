#!/usr/bin/env python3
"""Validate Product 06 algorithm assurance contract JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.schema_validate import SchemaStore  # noqa: E402

ASSURANCE_DIR = ROOT / "registry" / "assurance"
OWNED_CAPABILITIES = {
    "algebra.rational_equality",
    "algebra.linear_algebra",
    "logic.finite_counterexample",
    "analysis.symbolic_calculus",
}


def main() -> int:
    if not ASSURANCE_DIR.is_dir():
        print("registry/assurance missing", file=sys.stderr)
        return 1

    store = SchemaStore()
    errors = 0
    files = sorted(ASSURANCE_DIR.glob("assurance.*.json"))
    if len(files) < 3:
        print("expected ≥3 assurance contract files for owned checkers", file=sys.stderr)
        return 1

    seen_caps: set[str] = set()
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            store.validate("algorithm-contract.schema.json", data)
            if data.get("assuranceLevel") != "verified_reference_algorithm":
                raise ValueError("MVP contracts must declare verified_reference_algorithm")
            if data.get("completeness") is not None:
                raise ValueError("MVP must not claim completeness")
            cap = data["capabilityId"]
            if cap not in OWNED_CAPABILITIES:
                raise ValueError(f"unexpected capabilityId {cap!r}")
            seen_caps.add(cap)
            lean = data.get("leanContract") or {}
            for key in ("package", "module", "referenceAlgorithm"):
                if not lean.get(key):
                    raise ValueError(f"leanContract.{key} required")
            print(f"ok {path.name} ({cap})")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path.name}: {exc}", file=sys.stderr)
            errors += 1

    missing = OWNED_CAPABILITIES - seen_caps
    if missing:
        print(f"FAIL missing contracts for {sorted(missing)}", file=sys.stderr)
        errors += 1

    if errors:
        return 1
    print(f"assurance-validate ok ({len(files)} contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
