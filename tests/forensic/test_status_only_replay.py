"""Forensic: mathevidence replay must prove the original proposition.

P0-3 — Status-only replay that requires `True` and closes with `True.intro`
is forbidden for theorem-producing replay.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TACTIC = ROOT / "MathEvidence" / "Tactic" / "Mathevidence.lean"


def test_replay_does_not_require_true_goal() -> None:
    text = TACTIC.read_text(encoding="utf-8")
    assert "tgt.isConstOf ``True" not in text, (
        "P0-3 status-only replay still present: mathevidence replay requires "
        "goal True. See docs/security/KNOWN_TRUST_GAPS.md."
    )


def test_replay_does_not_close_with_true_intro() -> None:
    text = TACTIC.read_text(encoding="utf-8")
    assert "True.intro" not in text, (
        "P0-3: mathevidence replay must not close goals with True.intro"
    )
