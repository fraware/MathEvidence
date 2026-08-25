"""P0 regression tests for exact Candidate Bundle -> theorem binding."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from adapters.common.kernel_replay import KernelReplayError, run_kernel_replay

ROOT = Path(__file__).resolve().parents[2]


def _generator():
    path = ROOT / "scripts" / "generate_exact_ideal_replay_module.py"
    spec = importlib.util.spec_from_file_location("exact_ideal_generator", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _poly(m: int, coefficient: int, exponents: list[int]) -> dict:
    return {
        "varCount": m,
        "terms": [{"coefficient": coefficient, "exponents": exponents}],
    }


def _request_and_certificate() -> tuple[dict, dict]:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.ideal_membership_witness",
        "capabilityVersion": "0.1.0",
        "target": _poly(2, 1, [1, 1]),
        "generators": [_poly(2, 1, [1, 0]), _poly(2, 1, [0, 1])],
        "requestedClaim": "witness",
        "requestDigest": "sha256:" + ("12" * 32),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": request["capabilityVersion"],
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    return request, certificate


def _generate(request: dict, certificate: dict, *, name: str, digest_byte: str) -> str:
    return _generator().generate_exact_ideal_membership_module(
        module_name=f"MathEvidence.Generated.Replay.{name}",
        declaration_name=name,
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + (digest_byte * 64),
    )


def test_exact_ideal_generator_has_no_fixture_authority() -> None:
    request, certificate = _request_and_certificate()
    text = _generate(request, certificate, name="exact_xy", digest_byte="3")
    assert "OfflineFixtures" not in text
    assert "req_xy" not in text
    assert "cert_xy" not in text
    assert "Claim.proposition" in text
    assert request["requestDigest"] in text
    assert f'version := "{request["capabilityVersion"]}"' in text
    assert "Request.ofWireFields!" in text
    assert "exact_xy_request_binding" in text
    assert "resourcePolicy := defaultResourcePolicy" not in text
    assert "Monomial.ofList! 2 [1, 1]" in text
    assert "Monomial.ofList! 2 [0, 1]" in text


def test_request_notes_are_part_of_lean_wire_binding() -> None:
    request, certificate = _request_and_certificate()
    request["notes"] = ["semantic note", "second note"]
    text = _generate(request, certificate, name="notes_bound", digest_byte="4")
    assert 'some ["semantic note", "second note"]' in text
    assert "Request.ofWireFields!" in text
    assert "notes_bound_request_binding" in text


def test_wrong_request_schema_version_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    request["schemaVersion"] = "0.2.0"
    certificate["schemaVersion"] = "0.2.0"
    with pytest.raises(ValueError, match="request schemaVersion"):
        _generate(request, certificate, name="bad_schema", digest_byte="5")


def test_same_profile_different_claim_changes_theorem_source() -> None:
    request_a, certificate_a = _request_and_certificate()
    text_a = _generate(request_a, certificate_a, name="claim_a", digest_byte="a")

    request_b = json.loads(json.dumps(request_a))
    certificate_b = json.loads(json.dumps(certificate_a))
    request_b["target"] = _poly(2, 1, [1, 0])
    request_b["requestDigest"] = "sha256:" + ("56" * 32)
    certificate_b["target"] = request_b["target"]
    certificate_b["requestDigest"] = request_b["requestDigest"]
    certificate_b["multipliers"] = [
        _poly(2, 1, [0, 0]),
        {"varCount": 2, "terms": []},
    ]
    text_b = _generate(request_b, certificate_b, name="claim_b", digest_byte="b")

    assert text_a != text_b
    assert "Monomial.ofList! 2 [1, 1]" in text_a
    assert "Monomial.ofList! 2 [1, 1]" not in text_b


def test_certificate_semantic_copy_mismatch_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    certificate["target"] = _poly(2, 1, [0, 0])
    with pytest.raises(ValueError, match="certificate target"):
        _generate(request, certificate, name="bad_copy", digest_byte="7")


def test_cross_version_certificate_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    certificate["capabilityVersion"] = "0.2.0"
    with pytest.raises(ValueError, match="capabilityVersion"):
        _generate(request, certificate, name="bad_version", digest_byte="8")


def test_noncanonical_bundle_digest_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    with pytest.raises(ValueError, match="candidateBundleDigest"):
        _generator().generate_exact_ideal_membership_module(
            module_name="MathEvidence.Generated.Replay.bad_digest",
            declaration_name="bad_digest",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:not-a-digest",
        )


def test_fractional_sparse_integer_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    request["target"]["terms"][0]["coefficient"] = 1.5
    certificate["target"] = request["target"]
    with pytest.raises(ValueError, match="must be an integer"):
        _generate(request, certificate, name="fractional", digest_byte="9")


def test_candidate_only_claim_cannot_be_promoted_to_theorem() -> None:
    request, certificate = _request_and_certificate()
    request["requestedClaim"] = "candidate"
    certificate["claimClass"] = "candidate"
    with pytest.raises(ValueError, match="requires requestedClaim"):
        _generate(request, certificate, name="candidate_only", digest_byte="9")


def test_generic_rational_bundle_replay_never_uses_offline_fixtures() -> None:
    """Exact generator is enabled; OfflineFixtures must never mint a CR."""
    example = ROOT / "evidence" / "examples" / "rational_equality_basic"
    try:
        result = run_kernel_replay(
            bundle_dir=example,
            repo_root=ROOT,
            declaration_name="forensic_exact_rational_binding",
            require_lean=False,
        )
    except KernelReplayError as exc:
        assert "OfflineFixtures" not in str(exc.message)
        return
    assert result["ok"] is True
    assert "OfflineFixtures" not in (result.get("detail") or "")
    assert result.get("identityAuthority") == "Lean.Environment ConstantInfo"
