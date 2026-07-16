#!/usr/bin/env python3
"""Offline replay (Python side): schema + digest validation, no backends."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import verify_bundle_offline  # noqa: E402

EVIDENCE_ROOTS = [
    ROOT / "evidence" / "examples",
    ROOT / "evidence" / "conformance",
]


def find_bundles() -> list[Path]:
    bundles: list[Path] = []
    for root in EVIDENCE_ROOTS:
        if not root.is_dir():
            continue
        for manifest in root.rglob("manifest.json"):
            bundles.append(manifest.parent)
    return sorted(bundles)


def main() -> int:
    bundles = find_bundles()
    if not bundles:
        print("no evidence bundles found", file=sys.stderr)
        return 1
    errors = 0
    for bundle in bundles:
        rel = bundle.relative_to(ROOT)
        try:
            warnings = verify_bundle_offline(bundle)
            status = "ok"
            if warnings:
                status = "ok-with-warnings"
            print(f"{status} {rel}")
            for w in warnings:
                print(f"  warning: {w}")
                # Intentional mismatch fixtures live under conformance/*/hash_mismatch
                if "hash_mismatch" not in str(rel).replace("\\", "/"):
                    errors += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {rel}: {exc}", file=sys.stderr)
            # hash_mismatch and malformed adversarial-style fixtures may fail hard
            if "hash_mismatch" in str(rel).replace("\\", "/"):
                print(f"  (expected failure class for hash_mismatch)")
            else:
                errors += 1
    if errors:
        print(f"offline-replay failed ({errors} issues)", file=sys.stderr)
        return 1
    print(f"offline-replay ok ({len(bundles)} bundles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
