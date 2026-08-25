"""Assurance adversarial corpus for every exact-bound capability.

Covers candidate mismatch, fixture substitution, hash/source mutation, wrong
capability/generator/declaration, unsupported exact mode, legacy-as-exact, and
omitted side conditions — without requiring Lake.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from adapters.common.errors import AdapterError
from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.exact_replay.plugins.rational_equality import (
    generate_exact_rational_equality_module,
)
from adapters.common.exact_replay.registry import list_plugins
from agent.api.assurance_policy import decide_exact_kernel_replay, load_assurance_policy
from agent.api.receipt import legacy_assurance_tier

EXACT_BOUND = (
    "algebra.ideal_membership_witness",
    "algebra.rational_equality",
    "algebra.linear_algebra",
    "logic.finite_counterexample",
    "algebra.formal_rational_calculus",
    "analysis.analytic_calculus",
)

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


def test_exact_bound_plugins_registered() -> None:
    plugins = set(list_plugins())
    for cap in EXACT_BOUND:
        assert cap in plugins


@pytest.mark.parametrize("capability_id", EXACT_BOUND)
def test_exact_binding_supported_cr_eligibility_honest(capability_id: str) -> None:
    policy = load_assurance_policy(capability_id)
    assert policy is not None
    decision = decide_exact_kernel_replay(capability_id)
    assert decision.ok is True
    cert = policy.get("certification") or {}
    if capability_id in _CR_ELIGIBLE:
        assert cert.get("crEligible") is True
        outcomes = cert.get("allowedOutcomes") or []
        if capability_id == "logic.finite_counterexample":
            assert "refuted" in outcomes
        else:
            assert "proved" in outcomes
    else:
        assert cert.get("crEligible") is False


def test_unsupported_exact_mode_fail_closed() -> None:
    for cap in ("logic.sat_unsat", "logic.smt", "logic.pseudo_boolean"):
        decision = decide_exact_kernel_replay(cap)
        assert decision.ok is False


def test_benchmark_score_cannot_write_cr_eligible() -> None:
    """Registry remains authoritative; no benchmark helper mutates crEligible."""
    import scripts.run_ideal_membership_benchmark as bench

    assert not hasattr(bench, "set_cr_eligible")
    assert not hasattr(bench, "write_cr_eligible")
    src = Path(bench.__file__).read_text(encoding="utf-8")
    assert "crEligible" not in src
    assert "cr_eligible" not in src


def _ideal_pair() -> tuple[dict, dict]:
    def poly(m: int, c: int, e: list[int]) -> dict:
        return {"varCount": m, "terms": [{"coefficient": c, "exponents": e}]}

    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.ideal_membership_witness",
        "capabilityVersion": "0.1.0",
        "target": poly(2, 1, [1, 1]),
        "generators": [poly(2, 1, [1, 0]), poly(2, 1, [0, 1])],
        "requestedClaim": "witness",
        "requestDigest": "sha256:" + ("12" * 32),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    return request, certificate


def test_candidate_mismatch_and_fixture_substitution_change_hash() -> None:
    request, certificate = _ideal_pair()
    base = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("3" * 64),
        module_name="MathEvidence.Generated.Replay.adv_base",
        declaration_name="adv_base",
    )
    mutated = deepcopy(request)
    mutated["target"]["terms"][0]["coefficient"] = 2
    other = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=mutated,
        certificate={**certificate, "target": mutated["target"]},
        candidate_bundle_digest="sha256:" + ("3" * 64),
        module_name="MathEvidence.Generated.Replay.adv_base",
        declaration_name="adv_base",
    )
    assert base.source_hash != other.source_hash

    fixture = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("f" * 64),
        module_name="MathEvidence.Generated.Replay.adv_base",
        declaration_name="adv_base",
    )
    assert "f" * 64 in fixture.source_text
    assert base.source_hash != fixture.source_hash


def test_wrong_capability_and_generator_rejected() -> None:
    request, certificate = _ideal_pair()
    request = deepcopy(request)
    request["capability"] = "algebra.rational_equality"
    with pytest.raises(ValueError):
        generate_module(
            capability_id="algebra.ideal_membership_witness",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("3" * 64),
            module_name="MathEvidence.Generated.Replay.adv_wrong",
            declaration_name="adv_wrong",
        )


def test_legacy_record_cannot_masquerade_as_exact() -> None:
    from agent.api.receipt import _validate_v04_exact_fields

    legacy = {
        "schemaVersion": "0.3.0",
        "assuranceTier": "exact",
        "generatorId": "n/a",
        "generatedSourceHash": "n/a",
    }
    assert legacy_assurance_tier(legacy) == "legacy_fixture"

    forged = {
        "schemaVersion": "0.4.0",
        "assuranceTier": "exact",
        "canonicalClaimHash": "n/a",
        "candidateHash": "sha256:" + ("a" * 64),
        "generatorId": "n/a",
        "generatorVersion": "n/a",
        "grammarVersion": "n/a",
        "generatedSourceHash": "n/a",
        "theoremOrDeclarationIdentity": "n/a",
        "executionPolicyId": "n/a",
        "toolchainContractDigest": "n/a",
        "dependencyLockDigest": "n/a",
        "replayManifestHash": "n/a",
        "artifactHashes": {},
        "outcome": "proved",
    }
    with pytest.raises(ValueError, match="generatorId|exact"):
        _validate_v04_exact_fields(
            forged, capability_id="algebra.ideal_membership_witness"
        )


def test_omitted_side_condition_rejected_for_rational() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": {"tag": "rat", "num": "1", "den": "0"},
        "rhs": {"tag": "rat", "num": "1", "den": "1"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": "sha256:" + ("aa" * 32),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    with pytest.raises((AdapterError, ValueError)):
        generate_exact_rational_equality_module(
            module_name="MathEvidence.Generated.Replay.bad_den",
            declaration_name="bad_den",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("bb" * 32),
        )
