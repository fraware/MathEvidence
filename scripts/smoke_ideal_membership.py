#!/usr/bin/env python3
"""Fast ideal-membership smoke for ``just check`` / ``lean.yml`` (ME-RV-073).

Candidate-only: propose + Python mirror of ``checkMembership``.
MUST NEVER claim ``soundness_verified`` / Certification Record authority.

Release-grade Certification Record scoring lives in
``scripts/run_ideal_membership_benchmark.py --tier release`` (nightly /
``benchmarks.yml``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.common.ideal_membership import (  # noqa: E402
    ArityError,
    check_membership_python,
    propose_membership_witness,
)

SUITE = ROOT / "benchmarks" / "ideal_membership"
SMOKE_TASKS = [
    "tasks/IM01_linear_combination_xy.json",
    "tasks/IM51_false_membership_xfail.json",
]


def _load_task(rel: str) -> dict:
    path = SUITE / rel
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if not (SUITE / "manifest.json").is_file():
        print("smoke_ideal_membership: missing benchmarks/ideal_membership", file=sys.stderr)
        return 1

    errors = 0
    for rel in SMOKE_TASKS:
        task = _load_task(rel)
        tid = task.get("id") or rel
        expect_xfail = str(task.get("expectedStatus") or "") == "xfail"
        target = task["target"]
        gens = task["generators"]
        try:
            proposed_payload = propose_membership_witness(
                target=target, generators=gens, backend="stub"
            )
            proposed = list(proposed_payload.get("multipliers") or [])
            ok = bool(proposed) and check_membership_python(target, gens, proposed)
        except ArityError as exc:
            print(f"FAIL {tid}: arity {exc}", file=sys.stderr)
            errors += 1
            continue
        except Exception as exc:  # noqa: BLE001
            if expect_xfail:
                print(f"ok {tid}: xfail raised {type(exc).__name__}")
                continue
            print(f"FAIL {tid}: {exc}", file=sys.stderr)
            errors += 1
            continue

        if expect_xfail:
            if ok or proposed_payload.get("pythonMirrorAccepts"):
                print(f"FAIL {tid}: xfail task unexpectedly accepted", file=sys.stderr)
                errors += 1
            else:
                print(f"ok {tid}: xfail rejected as expected")
            continue

        if not ok:
            print(f"FAIL {tid}: checkMembership(proposed) false", file=sys.stderr)
            errors += 1
        else:
            print(f"ok {tid}: propose+decode+check")

    if errors:
        print(f"smoke_ideal_membership: {errors} failed", file=sys.stderr)
        return 1
    print(
        f"smoke_ideal_membership ok ({len(SMOKE_TASKS)} tasks; "
        "candidate-only, no soundness_verified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
