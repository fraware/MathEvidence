from __future__ import annotations

from adapters.common.exact_replay.plugins.rational_equality import (
    generate_exact_rational_equality_module,
)


def test_rational_exact_source_uses_native_decision_for_bound_request() -> None:
    digest = "sha256:" + ("a" * 64)
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [],
        "lhs": {"tag": "rat", "num": "1", "den": "2"},
        "rhs": {"tag": "rat", "num": "1", "den": "2"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": digest,
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }

    source = generate_exact_rational_equality_module(
        module_name="MathEvidence.Generated.Replay.rat_native_decision",
        declaration_name="rat_native_decision",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("b" * 64),
    )

    assert "Request.ofClaim! rat_native_decision_claim" in source
    assert "rat_native_decision_request_binding" in source
    assert "\n  native_decide\n" in source
    assert "(by native_decide : checkBool rat_native_decision_req rat_native_decision_cert = true)" in source
    assert "OfflineFixtures" not in source
