#!/usr/bin/env python3
"""§19 open replay rate — measured over committed evidence bundles."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import verify_bundle_offline  # noqa: E402

EVIDENCE_ROOTS = [
    ROOT / "evidence" / "examples",
    ROOT / "evidence" / "conformance",
]

EXPECTED_REJECT_MARKERS = (
    "hash_mismatch",
    "singular_inverse_rejected",
    "witness_type_mismatch",
    "out_of_domain_rejected",
    "missing_domain_rejection",
)


def find_bundles() -> list[Path]:
    bundles: list[Path] = []
    for root in EVIDENCE_ROOTS:
        if not root.is_dir():
            continue
        for manifest in root.rglob("manifest.json"):
            bundles.append(manifest.parent)
    return sorted(bundles)


def _is_expected_reject(rel: Path) -> bool:
    s = str(rel).replace("\\", "/")
    return any(m in s for m in EXPECTED_REJECT_MARKERS)


def measure() -> dict:
    bundles = find_bundles()
    accept_ok = 0
    accept_fail = 0
    reject_ok = 0
    reject_fail = 0
    failures: list[str] = []

    for bundle in bundles:
        rel = bundle.relative_to(ROOT)
        expect_reject = _is_expected_reject(rel)
        try:
            warnings = verify_bundle_offline(bundle)
            if expect_reject:
                if warnings:
                    reject_ok += 1
                else:
                    reject_fail += 1
                    failures.append(f"{rel}: expected reject had no warnings")
            else:
                if warnings:
                    accept_fail += 1
                    failures.append(f"{rel}: {warnings[0]}")
                else:
                    accept_ok += 1
        except Exception as exc:  # noqa: BLE001
            if expect_reject:
                reject_ok += 1
            else:
                accept_fail += 1
                failures.append(f"{rel}: {exc}")

    total = len(bundles)
    # Open replay rate: accept-path bundles that replay cleanly.
    accept_total = accept_ok + accept_fail
    rate = (accept_ok / accept_total) if accept_total else 0.0
    return {
        "metric": "open_replay_rate",
        "spec": "PROJECT_SPEC §19 secondary",
        "bundles_total": total,
        "accept_ok": accept_ok,
        "accept_fail": accept_fail,
        "expected_reject_ok": reject_ok,
        "expected_reject_fail": reject_fail,
        "open_replay_rate": round(rate, 4),
        "failures_sample": failures[:10],
        "claims": {
            "committed_offline_bundles": True,
            "live_backend_regeneration": False,
        },
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"open_replay_rate: {result['open_replay_rate']:.1%} "
        f"({result['accept_ok']}/{result['accept_ok'] + result['accept_fail']} accept-path)",
        file=sys.stderr,
    )
    # Soft metric: do not fail CI on measurement; foundry/just metrics stay informative.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
