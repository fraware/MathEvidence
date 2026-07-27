"""Forensic: Wave 0 verify-bundle must not emit theorem-level statuses (ME-RV-001)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from adapters.common.replay import (
    THEOREM_LEVEL_STATUSES,
    find_replay_exe,
    run_lean_replay,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "evidence" / "examples" / "rational_equality_basic"


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-verify-bundle not built; run lake build mathevidence-verify-bundle",
)
def test_verify_bundle_cannot_emit_theorem_level_statuses(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    shutil.copytree(EXAMPLE, dest)
    # Drop any residual receipt so the exe writes a fresh operational evaluation.
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
    assert out["claimEstablished"] is None
    assert out.get("resultStatus") == "checker_accepted"
    assert out.get("assuranceMode") == "native_checked"
    assert out["authority"] == "lean_operational"
    assert out.get("resultStatus") not in THEOREM_LEVEL_STATUSES

    # Wave 0: evaluation is stdout-only — never mutate the Candidate Bundle.
    assert not (dest / "checker-receipt.cjson").is_file()
    assert not (dest / "checker-receipt.json").is_file()
    receipt = out.get("envelope") or {}
    assert isinstance(receipt, dict) and receipt
    assert receipt.get("claimEstablished") is None
    assert receipt.get("resultStatus") == "checker_accepted"
    assert receipt.get("assuranceMode") == "native_checked"
    assert receipt.get("resultStatus") not in THEOREM_LEVEL_STATUSES
    assert receipt.get("assuranceMode") != "kernel_replay"
    # Prefer declared v0.3 bundleDigest; never the request digest alone.
    bundle_dig = receipt.get("bundleDigest") or ""
    req_dig = receipt.get("requestDigest") or ""
    if bundle_dig and req_dig:
        assert bundle_dig != req_dig or bundle_dig == ""


@pytest.mark.skipif(
    find_replay_exe(ROOT) is None,
    reason="mathevidence-verify-bundle not built; run lake build mathevidence-verify-bundle",
)
def test_verify_bundle_hard_fails_goal_mismatch(tmp_path: Path) -> None:
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


def test_python_adapter_never_promotes_theorem_status_without_exe() -> None:
    """Missing exe → tested/preview only; never soundness_verified."""
    out = run_lean_replay(
        bundle_dir=EXAMPLE,
        repo_root=ROOT,
        require_exe=False,
    )
    if out.get("leanExeMissing"):
        assert out["claimEstablished"] is None
        assert out.get("resultStatus") in (None, "tested", "checker_accepted")
        assert out.get("resultStatus") not in THEOREM_LEVEL_STATUSES
        assert out["authority"] == "python_preview"
