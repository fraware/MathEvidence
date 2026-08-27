from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

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


def test_release_exact_matrix_is_exactly_live_cr_eligible_set() -> None:
    """A disabled theorem path must disappear from release execution coverage."""
    path = ROOT / "scripts" / "ci" / "run_cr_exact_lean_e2e.py"
    module_name = "mathevidence_test_cr_exact_matrix"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        cases = module._cases()
        module._assert_coverage(cases)
        covered = {case.capability for case in cases}
        expected = module._inventory_cr_eligible()
    finally:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous

    assert covered == expected
    assert "algebra.rational_equality" not in covered
    assert len(covered) == 5
