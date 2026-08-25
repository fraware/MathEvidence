"""Exact replay framework + ideal membership plugin tests."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from adapters.common.exact_replay import (
    bind,
    parse_and_validate,
    render,
    to_replay_ir,
    verify,
)
from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.exact_replay.plugins.ideal_membership import (
    generate_exact_ideal_membership_module,
)

ROOT = Path(__file__).resolve().parents[2]


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


def test_ideal_pipeline_determinism() -> None:
    request, certificate = _request_and_certificate()
    kwargs = dict(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("3" * 64),
        module_name="MathEvidence.Generated.Replay.exact_xy",
        declaration_name="exact_xy",
    )
    a = generate_module(**kwargs)
    b = generate_module(**kwargs)
    assert a.source_text == b.source_text
    assert a.source_hash == b.source_hash
    assert a.source_text == generate_exact_ideal_membership_module(
        module_name=kwargs["module_name"],
        declaration_name=kwargs["declaration_name"],
        request=request,
        certificate=certificate,
        candidate_bundle_digest=kwargs["candidate_bundle_digest"],
    )


def test_ideal_golden_obligation_markers() -> None:
    request, certificate = _request_and_certificate()
    text = generate_exact_ideal_membership_module(
        module_name="MathEvidence.Generated.Replay.exact_xy",
        declaration_name="exact_xy",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("3" * 64),
    )
    assert "OfflineFixtures" not in text
    assert "Claim.proposition" in text
    assert "Request.ofWireFields!" in text
    assert "exact_xy_request_binding" in text
    assert "replaySound" in text
    assert "native_decide" in text
    assert request["requestDigest"] in text
    assert "generatorId = mathevidence.exact_ideal_membership" in text


def test_mutation_of_coefficient_changes_source_hash() -> None:
    request, certificate = _request_and_certificate()
    base = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("a" * 64),
        module_name="MathEvidence.Generated.Replay.mut_base",
        declaration_name="mut_base",
    )
    mutated_req = copy.deepcopy(request)
    mutated_req["target"]["terms"][0]["coefficient"] = 2
    mutated_cert = copy.deepcopy(certificate)
    mutated_cert["target"] = mutated_req["target"]
    with pytest.raises(ValueError):
        # certificate must match request target exactly
        generate_module(
            capability_id="algebra.ideal_membership_witness",
            request=mutated_req,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("a" * 64),
            module_name="MathEvidence.Generated.Replay.mut_bad",
            declaration_name="mut_bad",
        )
    mutated_cert["target"] = mutated_req["target"]
    other = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=mutated_req,
        certificate=mutated_cert,
        candidate_bundle_digest="sha256:" + ("a" * 64),
        module_name="MathEvidence.Generated.Replay.mut_ok",
        declaration_name="mut_ok",
    )
    assert other.source_hash != base.source_hash


def test_injection_raw_lean_in_notes_is_string_escaped() -> None:
    request, certificate = _request_and_certificate()
    request["notes"] = ['"; import Evil', "theorem fake : True := trivial"]
    text = generate_exact_ideal_membership_module(
        module_name="MathEvidence.Generated.Replay.inject_notes",
        declaration_name="inject_notes",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("b" * 64),
    )
    # Notes are JSON-string escaped into Lean string literals, not raw fragments.
    assert not any(line.strip().startswith("import Evil") for line in text.splitlines())
    assert 'import MathEvidence.Checkers.IdealMembership.ReplaySound' in text
    assert 'import MathEvidence.Checkers.IdealMembership.Wire' in text
    assert "theorem fake" in text  # only inside the notes string payload
    assert "theorem fake : True := trivial" not in [
        line.strip() for line in text.splitlines() if line.strip().startswith("theorem ")
    ]


def test_no_raw_lean_fragment_api() -> None:
    request, certificate = _request_and_certificate()
    canonical = parse_and_validate(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("c" * 64),
    )
    ir = to_replay_ir(
        canonical,
        module_name="MathEvidence.Generated.Replay.typed_only",
        declaration_name="typed_only",
    )
    assert not hasattr(ir, "lean_fragment")
    module = render(ir)
    assert verify(module).ok is True
    evidence = bind(module, capability_id="algebra.ideal_membership_witness")
    assert evidence.generator_id == "mathevidence.exact_ideal_membership"
    assert evidence.verifier == "mathevidence-declaration-identity"


def test_unsafe_module_name_rejected() -> None:
    request, certificate = _request_and_certificate()
    with pytest.raises(ValueError, match="unsafe|non-canonical"):
        generate_module(
            capability_id="algebra.ideal_membership_witness",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("d" * 64),
            module_name="../Evil",
            declaration_name="evil",
        )
