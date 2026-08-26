"""Assurance policy registry and fail-closed differential tests."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from agent.api.assurance_policy import (
    ASSURANCE_MODE_UNAVAILABLE,
    decide_exact_kernel_replay,
    exact_binding_supported,
    historical_exact_replay_capabilities,
    load_all_assurance_policies,
    load_assurance_policy,
    validate_assurance_policy_object,
)
from adapters.common.kernel_replay import EXACT_REPLAY_CAPABILITIES
from adapters.common.schema_validate import SchemaStore

ROOT = Path(__file__).resolve().parents[2]

# Release-authorized theorem/CR cohort. Rational equality deliberately remains
# candidate-only until its exact candidate-identity representation is closed.
_CR_ELIGIBLE = frozenset(
    {
        "algebra.ideal_membership_witness",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "analysis.analytic_calculus",
    }
)


def test_all_capabilities_have_assurance_policy() -> None:
    policies = load_all_assurance_policies()
    cap_files = sorted((ROOT / "registry" / "capabilities").glob("*.json"))
    assert len(policies) == len(cap_files)
    store = SchemaStore()
    for cap_id, policy in policies.items():
        store.validate("assurance-policy.schema.json", policy)
        assert not validate_assurance_policy_object(policy, capability_id=cap_id)
        cr = policy["certification"]["crEligible"]
        if cap_id in _CR_ELIGIBLE:
            assert cr is True
            outcomes = policy["certification"]["allowedOutcomes"]
            if cap_id == "logic.finite_counterexample":
                assert "refuted" in outcomes
            else:
                assert "proved" in outcomes
        else:
            assert cr is False


def test_exact_binding_current_and_historical_sets_are_distinct() -> None:
    policies = load_all_assurance_policies()
    supported = {
        cid for cid, policy in policies.items() if policy["exactBinding"]["supported"]
    }
    historical = set(historical_exact_replay_capabilities())

    assert supported == set(_CR_ELIGIBLE)
    assert historical == set(EXACT_REPLAY_CAPABILITIES)
    assert supported < historical
    assert historical - supported == {"algebra.rational_equality"}

    assert exact_binding_supported("algebra.ideal_membership_witness") is True
    assert exact_binding_supported("algebra.rational_equality") is False
    assert exact_binding_supported("logic.smt") is False


def test_policy_decisions_match_current_release_cohort() -> None:
    current = {
        cid
        for cid in load_all_assurance_policies()
        if decide_exact_kernel_replay(cid).ok
    }
    assert current == set(_CR_ELIGIBLE)

    # The compatibility cohort records implementation history only; it is not
    # release authority and may therefore be a strict superset of current CR.
    historical = historical_exact_replay_capabilities()
    assert historical == EXACT_REPLAY_CAPABILITIES
    assert "algebra.rational_equality" in historical
    assert "algebra.rational_equality" not in current


@pytest.mark.parametrize(
    "capability_id",
    sorted(cid for cid in load_all_assurance_policies() if cid not in _CR_ELIGIBLE),
)
def test_unsupported_exact_is_assurance_mode_unavailable(capability_id: str) -> None:
    decision = decide_exact_kernel_replay(capability_id)
    assert decision.ok is False
    assert decision.code == ASSURANCE_MODE_UNAVAILABLE


def test_unknown_capability_fail_closed() -> None:
    decision = decide_exact_kernel_replay("algebra.does_not_exist")
    assert decision.ok is False
    assert decision.code == ASSURANCE_MODE_UNAVAILABLE
    assert "unknown capability" in decision.message


def test_cr_eligible_without_generator_rejected_by_policy_validator() -> None:
    policy = copy.deepcopy(load_assurance_policy("logic.smt"))
    assert policy is not None
    policy["certification"]["crEligible"] = True
    errors = validate_assurance_policy_object(policy, capability_id="logic.smt")
    assert any("crEligible=true" in message for message in errors)


def test_exact_mode_without_binding_metadata_rejected() -> None:
    policy = copy.deepcopy(load_assurance_policy("algebra.ideal_membership_witness"))
    assert policy is not None
    policy["exactBinding"] = {"supported": True}
    errors = validate_assurance_policy_object(
        policy, capability_id="algebra.ideal_membership_witness"
    )
    assert any("exactBinding.supported requires fields" in message for message in errors)


def test_rational_theorem_replay_is_explicitly_fail_closed() -> None:
    policy = load_assurance_policy("algebra.rational_equality")
    assert policy is not None
    assert policy["exactBinding"]["supported"] is False
    assert policy["certification"]["crEligible"] is False
    assert policy["certification"]["allowedOutcomes"] == []
    assert policy["supportedAssuranceModes"] == []

    decision = decide_exact_kernel_replay("algebra.rational_equality")
    assert decision.ok is False
    assert decision.code == ASSURANCE_MODE_UNAVAILABLE
    assert "crEligible" in decision.message


def test_validate_registry_accepts_current_policies() -> None:
    import importlib.util

    path = ROOT / "scripts" / "validate_registry.py"
    spec = importlib.util.spec_from_file_location("validate_registry_release", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
