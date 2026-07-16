"""Multi-step Trace-to-Plan demo vs final-answer-only baseline (Product 05)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.trace_to_plan import plan_from_traces  # noqa: E402
from adapters.common.schema_validate import SchemaStore  # noqa: E402

DEMO = ROOT / "benchmarks" / "trace_to_plan" / "multistep_rational_demo.json"


def _score_plan(plan: dict) -> dict[str, int | bool]:
    advanced = [n for n in plan["nodes"] if n.get("advancesProofStatus")]
    hints_advanced = any(
        n.get("advancesProofStatus")
        and n.get("stepKind") in {"search_hint", "diagnostic_metadata"}
        for n in plan["nodes"]
    )
    return {
        "advanceableNodes": len(advanced),
        "reconstructibleProved": sum(
            1
            for n in advanced
            if n.get("stepKind") == "reconstructible_computation" and n.get("status") == "proved"
        ),
        "hintsAdvancedIllegally": hints_advanced,
        "unresolved": len(plan.get("unresolvedNodes") or []),
    }


def final_answer_only_baseline(target: str, final_trace: dict) -> dict:
    """Baseline: only the final CAS answer, no intermediate reconstructions."""
    return plan_from_traces(
        target_theorem=target,
        traces=[final_trace],
        reconstructions={},  # no reconstruction ⇒ cannot advance
    )


def reconstructible_demo(payload: dict) -> dict:
    return plan_from_traces(
        target_theorem=payload["targetTheorem"],
        traces=payload["traces"],
        reconstructions=payload.get("reconstructions") or {},
    )


def main() -> int:
    payload = json.loads(DEMO.read_text(encoding="utf-8"))
    baseline = final_answer_only_baseline(
        payload["targetTheorem"], payload["finalAnswerOnlyTrace"]
    )
    demo = reconstructible_demo(payload)
    SchemaStore().validate("proof-plan.schema.json", demo)
    SchemaStore().validate("proof-plan.schema.json", baseline)

    b_score = _score_plan(baseline)
    d_score = _score_plan(demo)

    if b_score["hintsAdvancedIllegally"] or d_score["hintsAdvancedIllegally"]:
        print("FAIL: hints advanced proof status", file=sys.stderr)
        return 1
    if d_score["reconstructibleProved"] <= b_score["reconstructibleProved"]:
        print(
            "FAIL: reconstructible demo did not beat final-answer-only baseline",
            file=sys.stderr,
        )
        print(f"  baseline={b_score} demo={d_score}", file=sys.stderr)
        return 1
    if d_score["advanceableNodes"] < 2:
        print("FAIL: expected multi-step reconstructible advances", file=sys.stderr)
        return 1

    print("ok product05_trace_to_plan_demo")
    print(f"  baseline={b_score}")
    print(f"  reconstructible={d_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
