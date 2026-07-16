"""Foundry trained tool-selection baseline — acceptanceInfluence stays false."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.metrics.foundry_trained_selector import (  # noqa: E402
    WeightedTokenSelector,
    load_train_episodes,
    measure,
    trained_select,
)


def test_train_episodes_never_influence_acceptance() -> None:
    episodes = load_train_episodes()
    assert len(episodes) >= 3
    for ep in episodes:
        assert ep["acceptanceInfluence"] is False


def test_trained_selector_beats_or_matches_naive_on_suite() -> None:
    result = measure()
    assert result["claims"]["acceptance_influence"] is False
    assert result["claims"]["frontier_acceleration"] is False
    assert result["claims"]["funding_secured"] is False
    assert result["train"]["episodes"] >= 3
    assert result["eval"]["tasks"] == 8
    assert result["naive"]["accuracy"] == 0.375
    assert 0.0 <= result["trained"]["accuracy"] <= 1.0
    assert result["trained"]["passed"] >= result["naive"]["passed"]


def test_trained_select_refuses_unknown_capability() -> None:
    model = WeightedTokenSelector()
    model.fit(load_train_episodes())
    task = {
        "id": "tmp",
        "goal": "Handle unknown",
        "goalFeatures": ["unknown_capability", "honest_refusal"],
        "capabilityCandidates": ["fantasy.quantum_oracle", "system.shell"],
        "input": {"capability": "fantasy.quantum_oracle"},
        "expect": {"action": "refuse_or_unsupported"},
    }
    sel = trained_select(task, model)
    assert sel.get("action") == "refuse_or_unsupported"
    assert sel.get("selectedCapability") is None
