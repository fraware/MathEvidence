"""Forensic: Wave 0 operational verify-bundle (ME-RV-001).

Formerly asserted theorem-producing `claimEstablished` / `soundness_verified`.
That overclaim is removed; see `test_verify_bundle_no_theorem_status.py`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.replay import THEOREM_LEVEL_STATUSES, find_replay_exe, run_lean_replay

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-verify-bundle not built; run lake build mathevidence-verify-bundle",
)
def test_lean_verify_emits_checker_accepted_not_theorem_status(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(EXAMPLE, dest)
    for name in ("checker-receipt.cjson", "checker-receipt.json"):
        p = dest / name
        if p.is_file():
            p.unlink()
    out = run_lean_replay(
        bundle_dir=dest,
        repo_root=ROOT,
        require_exe=True,
        goal_file=dest / "request.cjson",
    )
    assert out["ok"] is True, out.get("stderr")
    assert out["authority"] == "lean_operational"
    assert out["claimEstablished"] is None
    assert out.get("resultStatus") == "checker_accepted"
    assert out.get("resultStatus") not in THEOREM_LEVEL_STATUSES
    # Wave 0: stdout-only evaluation — never mutate the Candidate Bundle.
    assert not (dest / "checker-receipt.cjson").is_file()
    assert not (dest / "checker-receipt.json").is_file()
    receipt = out.get("envelope") or json.loads(out.get("stdout") or "{}")
    assert receipt.get("claimEstablished") is None
    assert receipt.get("resultStatus") == "checker_accepted"
    assert receipt.get("assuranceMode") == "native_checked"


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-verify-bundle not built; run lake build mathevidence-verify-bundle",
)
def test_lean_replay_hard_fails_goal_mismatch(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(EXAMPLE, dest)
    bad_goal = tmp_path / "bad_goal.json"
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
