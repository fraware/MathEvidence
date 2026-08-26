"""Regression coverage for formal-calculus exact request binding and proof mode."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.exact_replay.pipeline import generate_module


def test_formal_antiderivative_uses_definitional_binding_and_kernel_decide() -> None:
    request = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.formal_rational_calculus",
            "capabilityVersion": "0.1.0",
            "operation": "antiderivative_candidate",
            "variables": [{"name": "x", "type": "Rat"}],
            "independentVar": "x",
            "expr": {"tag": "var", "name": "x"},
            "candidate": {
                "tag": "mul",
                "left": {"tag": "rat", "num": "1", "den": "2"},
                "right": {
                    "tag": "pow",
                    "base": {"tag": "var", "name": "x"},
                    "exp": 2,
                },
            },
            "domainConditions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        }
    )
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "operation": request["operation"],
        "domainConditions": [],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }

    module = generate_module(
        capability_id=request["capability"],
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("c" * 64),
        module_name="MathEvidence.Generated.Replay.formal_antiderivative_binding_regression",
        declaration_name="formal_antiderivative_binding_regression",
    )
    source = module.source_text

    binding = "theorem formal_antiderivative_binding_regression_request_binding :"
    assert binding in source
    binding_body = source.split(binding, 1)[1].split(
        "theorem formal_antiderivative_binding_regression :", 1
    )[0]
    assert "\n  rfl\n" in binding_body
    assert "native_decide" not in binding_body

    # The substantive theorem still depends on the exact checker accepting the
    # exact generated request/certificate. `decide` asks the kernel to reduce
    # that closed proposition; it is not a fixture, assumption, or bypass.
    theorem_body = source.split(
        "theorem formal_antiderivative_binding_regression :", 1
    )[1]
    assert "checkBool formal_antiderivative_binding_regression_req" in theorem_body
    assert "by decide" in theorem_body
    assert "native_decide" not in theorem_body
