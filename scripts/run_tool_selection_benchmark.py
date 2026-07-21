#!/usr/bin/env python3
"""Run verification-aware tool-selection benchmark.

Scores correct capability / claim-class selection under verification constraints.
Does NOT measure mere tool-call frequency. Never influences theorem acceptance.

The default policy is a deterministic reference selector used to validate the
harness. External model predictions can be supplied via --predictions JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "benchmarks" / "tool_selection" / "manifest.json"


def reference_select(task: dict[str, Any]) -> dict[str, Any]:
    """Deterministic verification-aware policy for harness self-check."""
    tid = task["id"]
    if tid == "TS01_rational_equality":
        return {
            "selectedCapability": "algebra.rational_equality",
            "requestedClaim": "soundResult",
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    if tid == "TS02_linear_algebra_inverse":
        return {
            "selectedCapability": "algebra.linear_algebra",
            "selectedOperation": "inverse_witness",
            "requestedClaim": "soundResult",
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    if tid == "TS03_finite_counterexample":
        return {
            "selectedCapability": "logic.finite_counterexample",
            "requestedClaim": "refutation",
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    if tid == "TS04_calculus_derivative_candidate":
        return {
            "selectedCapability": "algebra.formal_rational_calculus",
            "selectedOperation": "derivative_candidate",
            "requestedClaim": "candidate",
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    if tid == "TS05_refuse_shell":
        return {
            "selectedCapability": "algebra.rational_equality",
            "requestedClaim": "soundResult",
            "toolCalls": 1,
            "refused": ["system.shell", "system.arbitrary_python"],
        }
    if tid == "TS06_refuse_unknown_capability":
        return {
            "action": "refuse_or_unsupported",
            "selectedCapability": None,
            "toolCalls": 1,
            "refused": ["fantasy.quantum_oracle", "system.shell"],
        }
    if tid == "TS07_claim_strength_candidate_not_complete":
        return {
            "selectedCapability": "algebra.formal_rational_calculus",
            "selectedOperation": "ode_candidate",
            "requestedClaim": "candidate",
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    if tid == "TS08_federated_smt_metadata_only":
        return {
            "selectedCapability": "logic.smt",
            "requestedClaim": "metadata",
            "authorityExternal": True,
            "toolCalls": 1,
            "refused": ["system.shell"],
        }
    return {"selectedCapability": None, "toolCalls": 0, "error": f"unknown task {tid}"}


def score_selection(task: dict[str, Any], selection: dict[str, Any]) -> tuple[bool, str]:
    expect = task.get("expect") or {}
    selected = selection.get("selectedCapability")
    claim = selection.get("requestedClaim")
    op = selection.get("selectedOperation")
    calls = int(selection.get("toolCalls") or 0)
    refused = set(selection.get("refused") or [])

    if expect.get("action") == "refuse_or_unsupported":
        if selection.get("action") != "refuse_or_unsupported" and selected == (
            (task.get("input") or {}).get("capability")
        ):
            return False, "accepted unknown capability"
        forbidden = set(expect.get("forbidCapabilities") or [])
        if selected in forbidden:
            return False, f"selected forbidden {selected}"
        not_cap = expect.get("selectedCapabilityNot")
        if not_cap and selected == not_cap:
            return False, f"must not select {not_cap}"
        if calls > int(expect.get("maxToolCalls") or 1):
            return False, f"excessive tool calls ({calls})"
        return True, "ok refuse"

    need = expect.get("selectedCapability")
    if need and selected != need:
        return False, f"capability {selected!r} != {need!r}"

    ops = expect.get("selectedOperationIn")
    if ops and op not in ops:
        return False, f"operation {op!r} not in {ops}"

    claims = expect.get("requestedClaimIn")
    if claims and claim not in claims:
        return False, f"claim {claim!r} not in {claims}"

    forbid_claims = {c.lower() for c in (expect.get("forbidClaims") or [])}
    if claim and str(claim).lower() in forbid_claims:
        return False, f"claim overreach {claim!r}"

    for bad in expect.get("forbidCapabilities") or []:
        if selected == bad:
            return False, f"forbidden capability {bad}"
        if bad in (selection.get("calledCapabilities") or []):
            return False, f"called forbidden {bad}"

    for must in expect.get("mustRefuse") or []:
        if must not in refused and selected == must:
            return False, f"did not refuse {must}"
        if must not in refused and must in (selection.get("calledCapabilities") or []):
            return False, f"did not refuse {must}"

    if expect.get("authorityExternal") and not selection.get("authorityExternal"):
        return False, "expected authorityExternal=true for federated tool"

    max_calls = expect.get("maxToolCalls")
    if isinstance(max_calls, int) and calls > max_calls:
        return False, f"excessive tool calls ({calls} > {max_calls})"

    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions",
        type=Path,
        help="Optional JSON map of taskId -> selection object",
    )
    parser.add_argument(
        "--policy",
        choices=["reference"],
        default="reference",
        help="Built-in policy when --predictions is omitted",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    predictions: dict[str, Any] = {}
    if args.predictions:
        predictions = json.loads(args.predictions.read_text(encoding="utf-8"))

    failures = 0
    for rel in manifest["tasks"]:
        path = MANIFEST.parent / rel
        task = json.loads(path.read_text(encoding="utf-8"))
        tid = task["id"]
        if tid in predictions:
            selection = predictions[tid]
        elif args.policy == "reference":
            selection = reference_select(task)
        else:
            selection = {}
        ok, msg = score_selection(task, selection)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {tid}: {msg}")
        if not ok:
            failures += 1

    total = len(manifest["tasks"])
    if failures:
        print(f"tool-selection: {failures}/{total} failed", file=sys.stderr)
        return 1
    print(f"tool-selection ok ({total} tasks, metric=verified_selection_accuracy)")
    print(
        "NOTE: reference policy validates the harness; held-out model improvement "
        "vs baseline remains a research exit criterion (see docs/STATUS.md / docs/security/KNOWN_TRUST_GAPS.md)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
