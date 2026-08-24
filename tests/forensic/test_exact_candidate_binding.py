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
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    return request, certificate


def test_exact_ideal_generator_has_no_fixture_authority() -> None:
    request, certificate = _request_and_certificate()
    text = _generator().generate_exact_ideal_membership_module(
        module_name="MathEvidence.Generated.Replay.exact_xy",
        declaration_name="exact_xy",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("34" * 32),
    )
    assert "OfflineFixtures" not in text
    assert "req_xy" not in text
    assert "cert_xy" not in text
    assert "Claim.proposition" in text
    assert request["requestDigest"] in text
    # Exact target xy and exact multiplier y occur in generated source.
    assert "Monomial.ofList! 2 [1, 1]" in text
    assert "Monomial.ofList! 2 [0, 1]" in text


def test_same_profile_different_claim_changes_theorem_source() -> None:
    request_a, certificate_a = _request_and_certificate()
    text_a = _generator().generate_exact_ideal_membership_module(
        module_name="MathEvidence.Generated.Replay.claim_a",
        declaration_name="claim_a",
        request=request_a,
        certificate=certificate_a,
        candidate_bundle_digest="sha256:" + ("aa" * 32),
    )

    request_b = json.loads(json.dumps(request_a))
    certificate_b = json.loads(json.dumps(certificate_a))
    # Same capability and arity, different mathematical target: x instead of xy.
    request_b["target"] = _poly(2, 1, [1, 0])
    request_b["requestDigest"] = "sha256:" + ("56" * 32)
    certificate_b["target"] = request_b["target"]
    certificate_b["requestDigest"] = request_b["requestDigest"]
    certificate_b["multipliers"] = [
        _poly(2, 1, [0, 0]),
        {"varCount": 2, "terms": []},
    ]
    text_b = _generator().generate_exact_ideal_membership_module(
        module_name="MathEvidence.Generated.Replay.claim_b",
        declaration_name="claim_b",
        request=request_b,
        certificate=certificate_b,
        candidate_bundle_digest="sha256:" + ("bb" * 32),
    )

    assert text_a != text_b
    assert "Monomial.ofList! 2 [1, 1]" in text_a
    assert "Monomial.ofList! 2 [1, 1]" not in text_b


def test_certificate_semantic_copy_mismatch_rejected_before_lean() -> None:
    request, certificate = _request_and_certificate()
    certificate["target"] = _poly(2, 1, [0, 0])
    with pytest.raises(ValueError, match="certificate target"):
        _generator().generate_exact_ideal_membership_module(
            module_name="MathEvidence.Generated.Replay.bad_copy",
            declaration_name="bad_copy",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("78" * 32),
        )


def test_candidate_only_claim_cannot_be_promoted_to_theorem() -> None:
    request, certificate = _request_and_certificate()
    request["requestedClaim"] = "candidate"
    certificate["claimClass"] = "candidate"
    with pytest.raises(ValueError, match="requires requestedClaim"):
        _generator().generate_exact_ideal_membership_module(
            module_name="MathEvidence.Generated.Replay.candidate_only",
            declaration_name="candidate_only",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("90" * 32),
        )


def test_generic_rational_bundle_replay_fails_closed() -> None:
    """A capability-selected OfflineFixture may no longer mint a generic record."""
    example = ROOT / "evidence" / "examples" / "rational_equality_basic"
    with pytest.raises(KernelReplayError) as exc:
        run_kernel_replay(
            bundle_dir=example,
            repo_root=ROOT,
            require_lean=False,
        )
    assert "assurance_mode_unavailable" in str(exc.value)
