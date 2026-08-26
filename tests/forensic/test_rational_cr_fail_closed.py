from __future__ import annotations

import json
from pathlib import Path

from agent.api.assurance_policy import (
    ASSURANCE_MODE_UNAVAILABLE,
    cr_eligible,
    decide_exact_kernel_replay,
    exact_binding_supported,
    load_assurance_policy,
)

ROOT = Path(__file__).resolve().parents[2]


def test_rational_theorem_certification_fails_closed_under_pinned_release_policy() -> None:
    capability = "algebra.rational_equality"
    policy = load_assurance_policy(capability)
    assert policy is not None

    certification = policy.get("certification") or {}
    maturity = policy.get("maturity") or {}

    assert certification.get("crEligible") is False
    assert certification.get("allowedOutcomes") == []
    assert policy.get("supportedAssuranceModes") == []
    assert exact_binding_supported(capability) is False
    assert cr_eligible(capability) is False

    # The capability is not deleted: checker/soundness/bridge maturity remains
    # explicit while theorem-level Certification Record promotion is disabled.
    assert maturity.get("adapterExists") is True
    assert maturity.get("checkerExists") is True
    assert maturity.get("leanSoundnessExists") is True
    assert maturity.get("bridgeReplayExists") is True
    assert maturity.get("exactCandidateBindingExists") is False

    decision = decide_exact_kernel_replay(capability)
    assert decision.ok is False
    assert decision.code == ASSURANCE_MODE_UNAVAILABLE
    assert "crEligible" in decision.message

    inventory = json.loads(
        (ROOT / "registry" / "maturity-inventory.json").read_text(encoding="utf-8")
    )
    row = next(
        entry for entry in inventory["capabilities"] if entry["id"] == capability
    )
    assert row["adapter_exists"] is True
    assert row["checker_exists"] is True
    assert row["lean_soundness_exists"] is True
    assert row["bridge_replay_exists"] is True
    assert row["exact_candidate_binding_exists"] is False
    assert row["cr_eligible"] is False
    assert row["supported_assurance_modes"] == []
    assert row["allowed_certification_outcomes"] == []
    assert row["exactBinding"] == {"supported": False}
