#!/usr/bin/env python3
"""Offline replay (Python side): schema + digest validation, no backends."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import iter_bundle_dirs, verify_bundle_offline  # noqa: E402

EVIDENCE_ROOTS = [
    ROOT / "evidence" / "examples",
    ROOT / "evidence" / "conformance",
]

# Intentional reject fixtures: checker or digest must fail; acceptance is an error.
# Note: rfc0001/false_identity is Lean-owned (Python offline only schema+digest).
EXPECTED_REJECT_MARKERS = (
    "hash_mismatch",
    "singular_inverse_rejected",
    "witness_type_mismatch",
    "out_of_domain_rejected",
)


def find_bundles() -> list[Path]:
    bundles: list[Path] = []
    for root in EVIDENCE_ROOTS:
        bundles.extend(iter_bundle_dirs(root))
    return sorted(set(bundles))


def _is_expected_reject(rel: Path) -> bool:
    s = str(rel).replace("\\", "/")
    return any(m in s for m in EXPECTED_REJECT_MARKERS)


def main() -> int:
    bundles = find_bundles()
    if not bundles:
        print("no evidence bundles found", file=sys.stderr)
        return 1
    errors = 0
    for bundle in bundles:
        rel = bundle.relative_to(ROOT)
        expect_reject = _is_expected_reject(rel)
        try:
            warnings = verify_bundle_offline(bundle)
            if expect_reject:
                if not warnings:
                    print(
                        f"FAIL {rel}: expected reject but offline verify had no warnings",
                        file=sys.stderr,
                    )
                    errors += 1
                else:
                    print(f"ok-expected-reject {rel}")
                    for w in warnings:
                        print(f"  warning: {w}")
                continue
            status = "ok"
            if warnings:
                status = "ok-with-warnings"
            print(f"{status} {rel}")
            for w in warnings:
                print(f"  warning: {w}")
                errors += 1
        except Exception as exc:  # noqa: BLE001
            if expect_reject:
                print(f"ok-expected-reject {rel}: {exc}")
            else:
                print(f"FAIL {rel}: {exc}", file=sys.stderr)
                errors += 1
    if errors:
        print(f"offline-replay failed ({errors} issues)", file=sys.stderr)
        return 1
    print(f"offline-replay ok ({len(bundles)} bundles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
