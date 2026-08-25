"""Tests for Product 03/04 orchestration helpers (Wave 6 epistemology)."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.common.bundle import write_candidate_bundle, write_certification_record
from adapters.common.theorem_identity import (
    default_rational_environment_lock,
    environment_lock_digest,
)
from adapters.common.canonical import bind_request_digest, sha256_digest
from adapters.common.hypothesis_util import find_counterexample, propose_conditions_from_request
from adapters.common.lean_mirrors import check_finite_counterexample, check_linear_algebra
from agent.hypothesis import (
    build_condition_lattice,
    certify_sufficient_set,
    delete_hypothesis_python,
    minimality_allowed,
)
from foundry.capture import capture_episode


def _minimal_rational_request() -> dict:
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "lhs": {
                "tag": "div",
                "num": {
                    "tag": "sub",
                    "left": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
                    "right": {"tag": "int", "value": "1"},
                },
                "den": {
                    "tag": "sub",
                    "left": {"tag": "var", "name": "x"},
                    "right": {"tag": "int", "value": "1"},
                },
            },
            "rhs": {
                "tag": "add",
                "left": {"tag": "var", "name": "x"},
                "right": {"tag": "int", "value": "1"},
            },
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
            "variables": [{"name": "x", "type": "Rat"}],
        }
    )


def _minimal_certificate(request_digest: str) -> dict:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": request_digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [
            {
                "expr": {
                    "tag": "sub",
                    "left": {"tag": "var", "name": "x"},
                    "right": {"tag": "int", "value": "1"},
                },
                "role": "original_division",
                "multiplicity": 1,
            }
        ],
        "factorization": {"method": "test", "notes": "fixture"},
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }


def _write_legacy_certification_fixture(tmp_path: Path, request: dict) -> Path:
    """Write the historical metadata-only fixture; it must never certify."""
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    d = sha256_digest({"k": "wave6"})
    env_lock = environment_lock_digest(default_rational_environment_lock())
    cert_path = next(
        e["digest"] for e in cand_manifest["files"] if e["path"] == "certificate.cjson"
    )
    receipt = {
        "schemaVersion": "0.3.0",
        "candidateBundleDigest": cand_manifest["bundleDigest"],
        "certificationRecordDigest": d,
        "requestDigest": request["requestDigest"],
        "certificateContentDigest": cert_path,
        "replayTargetDigest": d,
        "theoremTypeDigest": d,
        "proofDeclarationDigest": d,
        "axiomReportDigest": d,
        "environmentLockDigest": env_lock,
        "capability": {"id": "algebra.rational_equality", "version": "0.1.0"},
        "checker": {
            "package": "MathEvidence.Checkers.RationalEquality",
            "module": "Check",
            "name": "checkBool",
            "version": "0.1.0",
            "soundnessTheorem": "checkBool_sound",
        },
        "soundnessTheorem": "checkBool_sound",
        "claimRequested": "soundResult",
        "claimEstablished": "soundResult",
        "unresolvedObligations": [],
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
        "toolchain": {"leanVersion": "4.14.0", "lakeVersion": "lake"},
    }
    cert_dir = tmp_path / "cert"
    write_certification_record(
        cert_dir,
        candidate_bundle_digest=cand_manifest["bundleDigest"],
        request_digest=request["requestDigest"],
        capability_id="algebra.rational_equality",
        capability_version="0.1.0",
        claim_class="soundResult",
        result_status="soundness_verified",
        assurance_mode="kernel_replay",
        replay_target={
            "schemaVersion": "0.3.0",
            "candidateBundleDigest": cand_manifest["bundleDigest"],
            "detail": "wave6_test",
        },
        checker_evaluation={
            "schemaVersion": "0.3.0",
            "resultStatus": "checker_accepted",
            "assuranceMode": "native_checked",
        },
        theorem_identity={
            "schemaVersion": "0.3.0",
            "theoremTypeDigest": d,
            "proofDeclarationDigest": d,
            "environmentLockDigest": env_lock,
        },
        axiom_report={
            "schemaVersion": "0.3.0",
            "status": "compiled",
            "axiomDigests": [],
            "allowedAxioms": ["propext"],
        },
        certification_receipt=receipt,
    )
    return cert_dir


def test_propose_conditions_from_div() -> None:
    req = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "int", "value": "1"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "0"},
    }
    props = propose_conditions_from_request(req)
    assert props
    assert props[0]["source"] == "backend_proposed"


def test_delete_marks_necessity_open() -> None:
    request = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "int", "value": "1"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "1"},
    }
    conditions = [
        {
            "id": "c0",
            "expr": {"tag": "var", "name": "x"},
            "source": "backend_proposed",
            "status": "proposed",
        }
    ]
    out = delete_hypothesis_python(request, conditions, "c0", poly_zero=True)
    assert out["result"] == "not_redundant"
    assert out["necessity"] == "open"
    assert out["authorityStatus"] == "python_checker_mirror"


def test_lattice_claims_minimal_false() -> None:
    request = _minimal_rational_request()
    lattice = build_condition_lattice(artifact_id="t", request=request)
    assert lattice["claimsMinimal"] is False
    assert lattice["authorityStatus"] == "python_checker_mirror"
    assert lattice["sufficientSets"]
    assert lattice["sufficientSetsCertified"] == []
    assert lattice["sufficiencyPreview"]["outcome"] == "mirror_accepted"


def test_mirror_accepted_never_enters_certified_set(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    lattice = build_condition_lattice(artifact_id="t", request=request)
    assert lattice["sufficientSets"]
    assert lattice["sufficientSetsCertified"] == []
    cert_dir = _write_legacy_certification_fixture(tmp_path, request)
    ids = lattice["sufficientSets"][0]
    with pytest.raises(ValueError, match="Certification Record not verified"):
        certify_sufficient_set(
            lattice, ids, certification_record_dir=cert_dir, candidate_dir=tmp_path / "cand"
        )
    assert lattice["sufficientSetsCertified"] == []


def test_minimality_refuses_incomplete_necessity() -> None:
    assert (
        minimality_allowed(
            certified_condition_ids=["a", "b"],
            necessity_proofs=[{"conditionId": "a", "kind": "certified_counterexample"}],
        )
        is False
    )
    assert (
        minimality_allowed(
            certified_condition_ids=["a"],
            necessity_proofs=[{"conditionId": "a", "kind": "necessity_theorem"}],
        )
        is True
    )


def test_prove_sufficient_lean_authoritative() -> None:
    from agent.hypothesis import (
        SUFFICIENCY_CHECKER_DECL,
        SUFFICIENCY_THEOREM_DECL,
        prove_sufficient_python,
    )

    request = _minimal_rational_request()
    conds = propose_conditions_from_request(request)
    out = prove_sufficient_python(
        request,
        conds,
        receipt_ref={"receiptId": "recv-test-1"},
        axiom_report_id="axiom-report-demo",
    )
    assert out["authorityStatus"] == "python_checker_mirror"
    assert out["outcome"] == "mirror_accepted"
    assert out["mirrorSufficient"] is True
    assert out["evidence"]["theoremDecl"] == SUFFICIENCY_THEOREM_DECL
    assert out["evidence"]["checkerDecl"] == SUFFICIENCY_CHECKER_DECL
    assert out["evidence"]["receiptId"] == "recv-test-1"
    assert out["evidence"]["axiomReportId"] == "axiom-report-demo"


def test_prove_sufficient_refuses_denom_coverage_alone() -> None:
    """Coverage of denoms must not mark sufficiency when poly identity fails."""
    from agent.hypothesis import prove_sufficient_python

    request = {
        "lhs": {
            "tag": "div",
            "num": {"tag": "var", "name": "x"},
            "den": {"tag": "var", "name": "x"},
        },
        "rhs": {"tag": "int", "value": "2"},
    }
    conditions = [
        {
            "id": "c0",
            "expr": {"tag": "var", "name": "x"},
            "role": "original_division",
            "source": "backend_proposed",
            "status": "proposed",
        }
    ]
    out = prove_sufficient_python(request, conditions)
    assert out["denominatorsCovered"] is True
    assert out["mirrorSufficient"] is False
    assert out["outcome"] == "rejected"
    assert out["evidence"]["detail"] == "poly_identity_failed_despite_denom_coverage"
    assert any("denom coverage alone" in n for n in out["notes"])


def test_family_campaign_theorem_ref_cannot_set_formally_proved() -> None:
    from agent.conjecture import run_family_campaign

    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    campaign = run_family_campaign(
        family_id="finite.nat_le_3",
        candidates=[
            {"pred": req["predicate"]["pred"], "request": req},
            {
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "var", "idx": 0},
                },
                "outcome": "formally_proved",
                "theoremRef": "eq_refl_on_nat3",
            },
            {
                "pred": {
                    "tag": "le",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "var", "idx": 0},
                },
                "outcome": "open",
                "openDetail": "See conjecture-open-problem-nat-le-family.md",
                "searchBound": 4,
            },
        ],
    )
    acc = campaign["precisionAccounting"]
    assert acc["proposed"] == 3
    # Mirror preview does not count as falsified.
    assert acc["falsified"] == 0
    assert acc["mirrorAcceptedPreview"] == 1
    assert acc["formallyProved"] == 0
    assert "refutationRate" in acc
    assert "precisionRate" not in acc
    # Bare theoremRef cannot set formally_proved — becomes open refusal.
    assert any(
        e.get("state") == "open" and "formally_proved refused" in str(e.get("notes"))
        for e in campaign["episodes"]
    )


def test_forged_refutation_receipt_does_not_set_falsified(tmp_path: Path) -> None:
    from agent.conjecture import certify_refutation, new_episode, to_candidate

    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    cert = find_counterexample(req)
    assert cert is not None
    ep = to_candidate(new_episode(family_id="t", pred=req["predicate"]["pred"]))
    # Mirror-only path.
    preview = certify_refutation(
        ep, request=req, certificate=cert, refutation_id="cex"
    )
    assert preview["state"] == "candidate_statement"
    assert preview["refutationPreview"] == "mirror_accepted"
    # Forged / missing certification dir.
    forged = tmp_path / "forged"
    forged.mkdir()
    (forged / "manifest.cjson").write_text("{}", encoding="utf-8")
    out = certify_refutation(
        ep,
        request=req,
        certificate=cert,
        refutation_id="cex",
        certification_record_dir=forged,
    )
    assert out["state"] != "falsified"


def test_mark_formally_proved_rejects_positional_string() -> None:
    from agent.conjecture import mark_formally_proved, new_episode

    ep = new_episode(family_id="t", pred={"tag": "true"})
    with pytest.raises(TypeError):
        mark_formally_proved(ep, "arbitrary_theorem_ref")  # type: ignore[misc]


def test_foundry_capture_never_accepts() -> None:
    ep = capture_episode(
        kind="hypothesis_lattice",
        payload={"demo": True},
        episode_dir=__import__("pathlib").Path("foundry/episodes"),
    )
    assert ep["acceptanceInfluence"] is False
    path = __import__("pathlib").Path(ep["_path"])
    assert path.is_file()
    path.unlink()


def test_finite_cex_mirror() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    cert = find_counterexample(req)
    assert cert is not None
    assert check_finite_counterexample(req, cert)


def test_la_inverse_mirror() -> None:
    def rat(n: int, d: int = 1) -> dict:
        return {"tag": "rat", "num": str(n), "den": str(d)}

    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[rat(1, 2), rat(0)], [rat(0), rat(2)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": req["requestDigest"],
        "operation": "inverse_witness",
        "inverse": {
            "tag": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [[rat(2), rat(0)], [rat(0), rat(1, 2)]],
        },
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    assert check_linear_algebra(req, cert)


def test_make_condition_node_typed_kinds() -> None:
    from agent.hypothesis import CONDITION_NODE_KINDS, make_condition_node

    node = make_condition_node(
        node_id="c0",
        kind="nonzero_denominator",
        expr={"tag": "var", "name": "x"},
        lean_prop_hint="x ≠ 0",
    )
    assert node["kind"] in CONDITION_NODE_KINDS
    assert node["leanPropHint"] == "x ≠ 0"
    assert node["sufficiencyRequires"] == "lean_proof_and_receipt"
    try:
        make_condition_node(node_id="bad", kind="not_a_kind", expr={})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
