"""Forensic: mathevidence-replay theorem-produces for rational equality."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.replay import find_replay_exe, run_lean_replay

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-replay not built; run lake build mathevidence-replay",
)
def test_lean_replay_emits_claim_established_for_rational_example(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(EXAMPLE, dest)
    out = run_lean_replay(
        bundle_dir=dest,
        repo_root=ROOT,
        require_exe=True,
        goal_file=dest / "request.cjson",
    )
    assert out["ok"] is True, out.get("stderr")
    assert out["authority"] == "lean_exe"
    assert out["claimEstablished"] == "soundResult"
    assert out.get("resultStatus") == "soundness_verified"
    receipt_path = dest / "checker-receipt.cjson"
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["claimEstablished"] == "soundResult"
    assert receipt["resultStatus"] == "soundness_verified"
    assert receipt.get("contentDigestsVerified") is True


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-replay not built; run lake build mathevidence-replay",
)
def test_lean_replay_hard_fails_goal_mismatch(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(EXAMPLE, dest)
    bad_goal = tmp_path / "bad_goal.json"
    # Different claim: x = 0 vs example identity.
    bad_goal.write_text(
        json.dumps(
            {
                "schemaVersion": "0.1.0",
                "capability": "algebra.rational_equality",
                "capabilityVersion": "0.1.0",
                "variables": [{"name": "x", "type": "Rat"}],
                "lhs": {"tag": "var", "name": "x"},
                "rhs": {"tag": "int", "value": "0"},
                "knownAssumptions": [],
                "requestedClaim": "soundResult",
                "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
                "requestDigest": "sha256:" + "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    out = run_lean_replay(
        bundle_dir=dest,
        repo_root=ROOT,
        require_exe=True,
        goal_file=bad_goal,
    )
    assert out["ok"] is False
    assert "goal_mismatch" in (out.get("stderr") or "")
    assert out.get("claimEstablished") is None
