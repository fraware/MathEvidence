#!/usr/bin/env python3
"""Runner for ideal-membership value benchmark with generation/check timing."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.common.ideal_membership import (  # noqa: E402
    check_membership_python,
    propose_membership_witness,
)

SUITE = ROOT / "benchmarks" / "ideal_membership"


def main() -> int:
    manifest = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for rel in manifest["tasks"]:
        task = json.loads((SUITE / rel).read_text(encoding="utf-8"))
        target = task["target"]
        gens = task["generators"]
        expected = task.get("expectedMultipliers")
        expected_status = task.get("expectedStatus", "pass")

        native_start = time.perf_counter()
        proposed = propose_membership_witness(
            target=target, generators=gens, backend="sympy"
        )
        native_ms = (time.perf_counter() - native_start) * 1000.0

        check_ms = None
        lean_mirror_ok = None
        if expected is not None:
            check_start = time.perf_counter()
            lean_mirror_ok = check_membership_python(target, gens, expected)
            check_ms = (time.perf_counter() - check_start) * 1000.0

        if expected_status == "skip":
            status = "skip"
        elif expected_status == "xfail":
            # False membership: adapter must not accept an invented witness.
            status = (
                "xfail_ok"
                if not proposed.get("pythonMirrorAccepts")
                else "xfail_unexpected_accept"
            )
        elif lean_mirror_ok:
            status = "pass"
        else:
            status = "fail_or_missing_expected"

        rows.append(
            {
                "id": task["id"],
                "status": status,
                "expectedStatus": expected_status,
                "claimClass": task.get("claimClass"),
                "leanMirrorAcceptsExpected": lean_mirror_ok,
                "adapterPythonMirrorAccepts": proposed.get("pythonMirrorAccepts"),
                "adapterBackend": proposed.get("backend"),
                "nativeWitnessMs": round(native_ms, 3),
                "mathEvidenceCheckMs": None if check_ms is None else round(check_ms, 3),
                "asymmetryNote": (
                    None
                    if check_ms is None
                    else (
                        "generation_gt_check"
                        if native_ms > max(check_ms, 1e-9)
                        else "check_gte_generation"
                    )
                ),
            }
        )

    scored = [r for r in rows if r["status"] not in {"skip"}]
    passed = sum(1 for r in scored if r["status"] in {"pass", "xfail_ok"})
    native_times = [r["nativeWitnessMs"] for r in rows]
    check_times = [
        r["mathEvidenceCheckMs"] for r in rows if r["mathEvidenceCheckMs"] is not None
    ]
    gen_gt_check = sum(1 for r in rows if r.get("asymmetryNote") == "generation_gt_check")
    out = {
        "suite": manifest["suite"],
        "taskCount": len(rows),
        "scoredTasks": len(scored),
        "passed": passed,
        "skipped": sum(1 for r in rows if r["status"] == "skip"),
        "honestyNote": manifest.get("honestyNote"),
        "baselineSummary": {
            "nativeBackend": "sympy",
            "nativeWitnessTotalMs": round(sum(native_times), 3),
            "mathEvidenceCheckTotalMs": round(sum(check_times), 3),
            "nativeWitnessAvgMs": round(sum(native_times) / len(native_times), 3)
            if native_times
            else None,
            "mathEvidenceCheckAvgMs": round(sum(check_times) / len(check_times), 3)
            if check_times
            else None,
            "tasksWhereGenerationExceedsCheck": gen_gt_check,
            "timingAsymmetry": (
                "Witness generation (SymPy search) is timed separately from the "
                "Python mirror of Lean checkMembership; check is typically cheaper "
                "than search when expected multipliers are provided."
            ),
            "valueGateStatus": manifest.get("valueGate"),
        },
        "tasks": rows,
    }
    print(json.dumps(out, indent=2))
    return 0 if passed == len(scored) else 1


if __name__ == "__main__":
    raise SystemExit(main())
