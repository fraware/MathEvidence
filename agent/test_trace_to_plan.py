"""Tests for Trace-to-Plan (Product 05) — Wave 6 certification gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.common.bundle import write_candidate_bundle, write_certification_record
from adapters.common.theorem_identity import (
    default_rational_environment_lock,
    environment_lock_digest,
)
from adapters.common.canonical import bind_request_digest, sha256_digest
from agent.trace_to_plan import (
    check_plan_soundness,
    classify_trace_item,
    direct_proof_evidence_ok,
    hints_never_advance,
    plan_from_traces,
    reconstruct_from_receipt,
    reconstruction_has_verified_receipt,
    validate_plan_invariants,
)


def _digest() -> str:
    return sha256_digest({"wave6": "ttp"})


def _minimal_rational_request() -> dict:
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "lhs": {"tag": "int", "value": "1"},
            "rhs": {"tag": "int", "value": "1"},
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
        "denominatorFactors": [],
        "factorization": {"method": "test", "notes": "fixture"},
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }


def _write_legacy_certification_fixture(tmp_path: Path) -> Path:
    """Write the historical metadata-only fixture; it must never certify."""
    request = _minimal_rational_request()
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    d = _digest()
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
            "detail": "wave6_ttp",
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


def test_classify_defaults_unknown_to_search_hint() -> None:
    assert classify_trace_item({"id": "a", "rawKind": "mystery", "content": {}}) == "search_hint"


def test_hints_do_not_advance_proof_status() -> None:
    plan = plan_from_traces(
        target_theorem="∀ x, p x",
        traces=[
            {"id": "h1", "rawKind": "smt_hint", "content": {"claim": "try subst"}},
            {"id": "d1", "rawKind": "timing", "content": {"ms": 12}},
        ],
    )
    assert hints_never_advance(plan)
    for node in plan["nodes"]:
        if node["stepKind"] in {"search_hint", "diagnostic_metadata"}:
            assert node["advancesProofStatus"] is False
            assert node["status"] == "proposed"


def test_hint_cannot_advance() -> None:
    with pytest.raises(ValueError, match="non-reconstructible|hints"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "h",
                        "stepKind": "search_hint",
                        "status": "proposed",
                        "advancesProofStatus": True,
                    }
                ],
                "edges": [],
            }
        )


def test_reconstructible_without_receipt_does_not_advance() -> None:
    bare = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {"claim": "poly equal", "capability": "algebra.rational_equality"},
            }
        ],
    )
    node = next(n for n in bare["nodes"] if n["id"] == "n_c1")
    assert node["stepKind"] == "reconstructible_computation"
    assert node["advancesProofStatus"] is False
    assert "c1" in bare["unresolvedNodes"]

    verified_no_receipt = plan_from_traces(
        target_theorem="lhs = rhs",
        traces=[
            {
                "id": "c1",
                "rawKind": "certificate",
                "content": {"claim": "poly equal", "capability": "algebra.rational_equality"},
            }
        ],
        reconstructions={
            "c1": {
                "method": "RationalEquality.checkBool",
                "resultStatus": "soundness_verified",
                "bundleRef": "evidence/examples/...",
            }
        },
    )
    vnode = next(n for n in verified_no_receipt["nodes"] if n["id"] == "n_c1")
    assert vnode["advancesProofStatus"] is False
    assert "c1" in verified_no_receipt["unresolvedNodes"]
    assert not reconstruction_has_verified_receipt(vnode["reconstruction"])


def test_checker_receipt_alone_cannot_advance() -> None:
    """Structural / certificate-only receipt bindings never authorize advancement."""
    bad = reconstruct_from_receipt(
        trace_id="c1",
        receipt={
            "requestDigest": "sha256:" + "ab" * 32,
            "resultStatus": "soundness_verified",
            "claimEstablished": "soundResult",
            "bundleDigest": "sha256:" + "cd" * 32,
        },
    )
    assert bad is None


def test_direct_step_without_theorem_digest_cannot_advance() -> None:
    plan = plan_from_traces(
        target_theorem="goal",
        traces=[
            {
                "id": "d1",
                "rawKind": "direct",
                "content": {"claim": "step"},
            }
        ],
        reconstructions={
            "d1": {
                "method": "handwave",
                "resultStatus": "proved",
                "theoremDeclaration": "foo",
                # missing theoremTypeDigest / environmentLockDigest / axiom
            }
        },
    )
    node = next(n for n in plan["nodes"] if n["id"] == "n_d1")
    assert node["advancesProofStatus"] is False
    assert not direct_proof_evidence_ok(node["reconstruction"])


def test_direct_step_with_full_evidence_advances() -> None:
    d = _digest()
    env_lock = environment_lock_digest(default_rational_environment_lock())
    recon = {
        "method": "existing_declaration",
        "resultStatus": "kernel_certified",
        "theoremDeclaration": "MathEvidence.Demo.thm",
        "theoremTypeDigest": d,
        "environmentLockDigest": d,
        "axiomReportDigest": d,
    }
    plan = plan_from_traces(
        target_theorem="goal",
        traces=[{"id": "d1", "rawKind": "direct", "content": {"claim": "step"}}],
        reconstructions={"d1": recon},
    )
    node = next(n for n in plan["nodes"] if n["id"] == "n_d1")
    assert node["advancesProofStatus"] is True
    assert node["status"] == "kernel_certified"


def test_legacy_certification_record_cannot_advance_reconstruction(tmp_path: Path) -> None:
    cert_dir = _write_legacy_certification_fixture(tmp_path)
    good = reconstruct_from_receipt(
        trace_id="c1",
        certification_record_dir=cert_dir,
        candidate_dir=tmp_path / "cand",
    )
    assert good is None


def test_cycle_rejected() -> None:
    plan = plan_from_traces(target_theorem="goal", traces=[])
    plan["edges"].append({"from": "target", "to": "target", "kind": "depends_on"})
    with pytest.raises(ValueError, match="cycle"):
        validate_plan_invariants(plan)


def test_dangling_edge_rejected() -> None:
    with pytest.raises(ValueError, match="missing node"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "a",
                        "stepKind": "lemma_candidate",
                        "status": "proposed",
                        "advancesProofStatus": False,
                    }
                ],
                "edges": [{"from": "a", "to": "missing", "kind": "depends_on"}],
            }
        )


def test_plan_invariants_reject_reconstructible_advance_without_receipt() -> None:
    with pytest.raises(ValueError, match="Certification Record|receiptGate"):
        validate_plan_invariants(
            {
                "nodes": [
                    {
                        "id": "c",
                        "stepKind": "reconstructible_computation",
                        "status": "kernel_certified",
                        "advancesProofStatus": True,
                        "reconstruction": {
                            "method": "handwave",
                            "resultStatus": "soundness_verified",
                        },
                    }
                ],
                "edges": [],
            }
        )


def test_plan_soundness_rejects_proved_without_evidence() -> None:
    with pytest.raises(ValueError, match="theorem digest|Certification Record"):
        check_plan_soundness(
            {
                "nodes": [
                    {
                        "id": "c",
                        "stepKind": "direct_proof_step",
                        "status": "kernel_certified",
                        "advancesProofStatus": True,
                        "reconstruction": {"method": "status_only"},
                    }
                ],
                "edges": [],
            }
        )
