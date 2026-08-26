"""Regression coverage for formal-calculus exact request binding and proof mode."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.exact_replay.pipeline import generate_module


def _generate(operation: str, *, antiderivative: bool) -> str:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.formal_rational_calculus",
        "capabilityVersion": "0.1.0",
        "operation": operation,
        "variables": [{"name": "x", "type": "Rat"}],
        "independentVar": "x",
        "domainConditions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    if antiderivative:
        request["expr"] = {"tag": "var", "name": "x"}
        request["candidate"] = {
            "tag": "mul",
            "left": {"tag": "rat", "num": "1", "den": "2"},
            "right": {
                "tag": "pow",
                "base": {"tag": "var", "name": "x"},
                "exp": 2,
            },
        }
    else:
        request["expr"] = {
            "tag": "pow",
            "base": {"tag": "var", "name": "x"},
            "exp": 2,
        }
        request["candidate"] = {
            "tag": "mul",
            "left": {"tag": "int", "value": "2"},
            "right": {"tag": "var", "name": "x"},
        }

    bound = bind_request_digest(request)
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": bound["capability"],
        "capabilityVersion": bound["capabilityVersion"],
        "requestDigest": bound["requestDigest"],
        "operation": bound["operation"],
        "domainConditions": [],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    declaration = f"formal_{operation}_proof_mode_regression"
    module = generate_module(
        capability_id=bound["capability"],
        request=bound,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("c" * 64),
        module_name=f"MathEvidence.Generated.Replay.{declaration}",
        declaration_name=declaration,
    )
    return module.source_text


def _binding_and_theorem(source: str, declaration: str) -> tuple[str, str]:
    binding = f"theorem {declaration}_request_binding :"
    theorem = f"theorem {declaration} :"
    assert binding in source
    assert theorem in source
    binding_body = source.split(binding, 1)[1].split(theorem, 1)[0]
    theorem_body = source.split(theorem, 1)[1]
    return binding_body, theorem_body


def test_formal_antiderivative_uses_definitional_checker_reduction() -> None:
    declaration = "formal_antiderivative_candidate_proof_mode_regression"
    source = _generate("antiderivative_candidate", antiderivative=True)
    binding_body, theorem_body = _binding_and_theorem(source, declaration)

    # Candidate/request identity is definitional and must not depend on a native
    # evaluator. This projection theorem was the first Lean 4.14 failure mode.
    assert "\n  rfl\n" in binding_body
    assert "native_decide" not in binding_body

    # The rational antiderivative production fixture reduces the exact closed
    # checker proposition definitionally. `rfl` is therefore stricter than a
    # fixture or assumption: generation compiles only when checkBool is true.
    assert f"checkBool {declaration}_req {declaration}_cert" in theorem_body
    assert "by rfl" in theorem_body
    assert "native_decide" not in theorem_body
    assert "by decide" not in theorem_body


def test_formal_derivative_retains_validated_native_checker_path() -> None:
    declaration = "formal_derivative_candidate_proof_mode_regression"
    source = _generate("derivative_candidate", antiderivative=False)
    binding_body, theorem_body = _binding_and_theorem(source, declaration)

    assert "\n  rfl\n" in binding_body
    assert "native_decide" not in binding_body
    assert f"checkBool {declaration}_req {declaration}_cert" in theorem_body
    assert "by native_decide" in theorem_body
    assert "by decide" not in theorem_body
