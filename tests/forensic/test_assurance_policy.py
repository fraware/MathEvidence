"""Assurance policy registry and fail-closed differential tests."""

from __future__ import annotations

import copy
import json
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
from adapters.common.kernel_replay import EXACT_REPLAY_CAPABILITIES, KernelReplayError, run_kernel_replay
from adapters.common.schema_validate import SchemaStore

ROOT = Path(__file__).resolve().parents[2]

_CR_ELIGIBLE = frozenset(
    {
        "algebra.ideal_membership_witness",
        "algebra.rational_equality",
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


def test_exact_binding_phase2_set() -> None:
    supported = {cid for cid, p in load_all_assurance_policies().items() if p["exactBinding"]["supported"]}
    assert supported == set(historical_exact_replay_capabilities())
    assert exact_binding_supported("algebra.ideal_membership_witness") is True
    assert exact_binding_supported("algebra.rational_equality") is True
    assert exact_binding_supported("logic.smt") is False


def test_differential_matches_historical_exact_set() -> None:
    historical = historical_exact_replay_capabilities()
    assert historical == EXACT_REPLAY_CAPABILITIES
    registry_exact = {
        cid
        for cid, policy in load_all_assurance_policies().items()
        if decide_exact_kernel_replay(cid).ok
    }
    assert registry_exact == set(historical)


@pytest.mark.parametrize(
    "capability_id",
    sorted(
        cid
        for cid in load_all_assurance_policies()
        if cid not in historical_exact_replay_capabilities()
    ),
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
    errors = validate_assurance_policy_object(
        policy, capability_id="logic.smt"
    )
    assert any("crEligible=true" in message for message in errors)


def test_exact_mode_without_binding_metadata_rejected() -> None:
    policy = copy.deepcopy(load_assurance_policy("algebra.ideal_membership_witness"))
    assert policy is not None
    policy["exactBinding"] = {"supported": True}
    errors = validate_assurance_policy_object(
        policy, capability_id="algebra.ideal_membership_witness"
    )
    assert any("exactBinding.supported requires fields" in message for message in errors)


def test_kernel_replay_rational_uses_exact_generator_not_fixtures() -> None:
    """Exact binding is enabled; OfflineFixtures must never be the authority."""
    example = ROOT / "evidence" / "examples" / "rational_equality_basic"
    decision = decide_exact_kernel_replay("algebra.rational_equality")
    assert decision.ok is True
    try:
        result = run_kernel_replay(
            bundle_dir=example,
            repo_root=ROOT,
            declaration_name="forensic_exact_rational",
            require_lean=False,
        )
    except KernelReplayError as exc:
        assert "OfflineFixtures" not in str(exc.message)
        return
    assert result["ok"] is True
    assert "OfflineFixtures" not in (result.get("detail") or "")
    assert result.get("identityAuthority") == "Lean.Environment ConstantInfo"


def test_validate_registry_accepts_phase1_policies() -> None:
    import importlib.util

    path = ROOT / "scripts" / "validate_registry.py"
    spec = importlib.util.spec_from_file_location("validate_registry_phase1", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
