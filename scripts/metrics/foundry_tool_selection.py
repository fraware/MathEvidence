#!/usr/bin/env python3
"""Foundry tool-selection: naive baseline vs reference policy accuracy."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_tool_selection_benchmark import (  # noqa: E402
    reference_select,
    score_selection,
)

MANIFEST = ROOT / "benchmarks" / "tool_selection" / "manifest.json"


def naive_baseline(task: dict[str, Any]) -> dict[str, Any]:
    """Frequency-blind baseline: always pick rational equality + soundResult.

    Intentionally weak — used only to quantify reference-policy lift on the
    harness. Not a trained model; held-out model uplift remains OPEN.
    """
    return {
        "selectedCapability": "algebra.rational_equality",
        "requestedClaim": "soundResult",
        "toolCalls": 1,
        "refused": [],
    }


def measure() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tasks: list[dict[str, Any]] = []
    for rel in manifest["tasks"]:
        tasks.append(json.loads((MANIFEST.parent / rel).read_text(encoding="utf-8")))

    def score_policy(policy_name: str, fn) -> dict[str, Any]:
        ok = 0
        rows = []
        for task in tasks:
            sel = fn(task)
            passed, msg = score_selection(task, sel)
            if passed:
                ok += 1
            rows.append({"id": task["id"], "pass": passed, "msg": msg})
        total = len(tasks)
        return {
            "policy": policy_name,
            "passed": ok,
            "total": total,
            "accuracy": round(ok / total, 4) if total else 0.0,
            "rows": rows,
        }

    baseline = score_policy("naive_always_rational", naive_baseline)
    reference = score_policy("reference", reference_select)
    lift = round(reference["accuracy"] - baseline["accuracy"], 4)
    return {
        "metric": "tool_selection_baseline_vs_reference",
        "baseline": {k: v for k, v in baseline.items() if k != "rows"},
        "reference": {k: v for k, v in reference.items() if k != "rows"},
        "accuracy_lift_reference_minus_baseline": lift,
        "baseline_rows": baseline["rows"],
        "reference_rows": reference["rows"],
        "claims": {
            "harness_self_check": True,
            "trained_model_held_out_uplift": False,
            "frontier_acceleration": False,
        },
        "notes": (
            "Reference policy validates the harness. Measured lift vs naive "
            "baseline is engineering-only; Milestone 6 model uplift stays OPEN."
        ),
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"tool_selection: baseline={result['baseline']['accuracy']:.1%} "
        f"reference={result['reference']['accuracy']:.1%} "
        f"lift={result['accuracy_lift_reference_minus_baseline']:+.1%}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
