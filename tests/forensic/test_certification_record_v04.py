"""Certification Record v0.4 and legacy v0.3 mapping tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.common.bundle import (
    CERTIFICATION_RECORD_VERSION,
    CERTIFICATION_RECORD_VERSION_LEGACY,
    NA_SENTINEL,
    write_candidate_bundle,
    write_certification_record,
)
from adapters.common.canonical import sha256_digest
from adapters.common.schema_validate import SchemaStore
from adapters.common.theorem_identity import (
    build_replay_target,
    default_rational_environment_lock,
    environment_lock_digest,
)
from agent.api.receipt import legacy_assurance_tier, verify_certification_record

ROOT = Path(__file__).resolve().parents[2]


def _zero_digest() -> str:
    return "sha256:" + ("00" * 32)


def _minimal_rational_request() -> dict:
    from adapters.common.canonical import bind_request_digest

    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": {
            "tag": "add",
            "left": {"tag": "var", "name": "x"},
            "right": {"tag": "int", "value": "0"},
        },
        "rhs": {"tag": "var", "name": "x"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def _minimal_certificate(request_digest: str) -> dict:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": request_digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": [],
        "factorization": {"method": "test", "notes": "unit"},
        "provenance": {
            "backendId": "test",
            "backendVersion": "0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-21T00:00:00Z",
            "deterministic": True,
        },
    }


def test_write_certification_record_emits_v04_fields(tmp_path: Path) -> None:
    request = _minimal_rational_request()
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    d = sha256_digest({"k": "v04"})
    lock = environment_lock_digest(default_rational_environment_lock())
    cert_digest = next(
        e["digest"] for e in cand_manifest["files"] if e["path"] == "certificate.cjson"
    )
    receipt = {
        "schemaVersion": "0.3.0",
        "candidateBundleDigest": cand_manifest["bundleDigest"],
        "certificationRecordDigest": d,
        "requestDigest": request["requestDigest"],
        "certificateContentDigest": cert_digest,
        "replayTargetDigest": d,
        "theoremTypeDigest": d,
        "proofDeclarationDigest": d,
        "axiomReportDigest": d,
        "environmentLockDigest": lock,
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
    target = build_replay_target(
        module_name="MathEvidence.Generated.Replay.forensic_v04",
        declaration_name="forensic_v04",
        theorem_type_canonical="True",
        theorem_type_digest_value=d,
        source_revision="workspace",
        source_file="MathEvidence/Generated/Replay/forensic_v04.lean",
        environment_lock_digest_value=lock,
        request_digest=request["requestDigest"],
        capability_id="algebra.rational_equality",
        capability_version="0.1.0",
        candidate_bundle_digest=cand_manifest["bundleDigest"],
    )
    manifest = write_certification_record(
        tmp_path / "cert",
        candidate_bundle_digest=cand_manifest["bundleDigest"],
        request_digest=request["requestDigest"],
        capability_id="algebra.rational_equality",
        capability_version="0.1.0",
        claim_class="soundResult",
        result_status="soundness_verified",
        assurance_mode="kernel_replay",
        replay_target=target,
        checker_evaluation={"schemaVersion": "0.3.0", "resultStatus": "checker_accepted"},
        theorem_identity={
            "schemaVersion": "0.3.0",
            "declarationName": "forensic_v04",
            "theoremTypeDigest": d,
            "proofDeclarationDigest": d,
            "environmentLockDigest": lock,
            "elaboratedSerialization": "True",
            "serializerVersion": "mathevidence-theorem-identity-0.3",
            "universeParams": [],
            "binders": [],
            "constantNames": [],
        },
        axiom_report={"schemaVersion": "0.3.0", "status": "compiled", "axiomDigests": []},
        certification_receipt=receipt,
    )
    assert manifest["bundleVersion"] == CERTIFICATION_RECORD_VERSION
    assert manifest["outcome"] == "proved"
    assert manifest["generatorId"] == NA_SENTINEL
    assert manifest["generatedSourceHash"] == NA_SENTINEL
    store = SchemaStore()
    store.validate("certification-record.schema.json", manifest)
    written_receipt = json.loads(
        (tmp_path / "cert" / "certification-receipt.cjson").read_text(encoding="utf-8")
    )
    store.validate("certification-receipt.schema.json", written_receipt)
    assert written_receipt["schemaVersion"] == CERTIFICATION_RECORD_VERSION
    assert written_receipt["outcome"] == "proved"


def test_legacy_v03_receipt_maps_to_lower_assurance() -> None:
    receipt = {
        "schemaVersion": CERTIFICATION_RECORD_VERSION_LEGACY,
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
    }
    assert legacy_assurance_tier(receipt) == "legacy_fixture"


def test_never_synthesize_missing_exact_generator_identity() -> None:
    receipt = {
        "schemaVersion": CERTIFICATION_RECORD_VERSION,
        "assuranceTier": "exact",
        "generatorId": NA_SENTINEL,
        "generatedSourceHash": NA_SENTINEL,
    }
    assert legacy_assurance_tier(receipt) == "exact"
    # Validator path rejects exact tier without real generator id.
    from agent.api.receipt import _validate_v04_exact_fields

    full = {
        "schemaVersion": "0.4.0",
        "outcome": "proved",
        "claimRequested": "soundResult",
        "claimEstablished": "soundResult",
        "canonicalClaimHash": _zero_digest(),
        "candidateHash": _zero_digest(),
        "generatorId": NA_SENTINEL,
        "generatorVersion": NA_SENTINEL,
        "grammarVersion": NA_SENTINEL,
        "generatedSourceHash": NA_SENTINEL,
        "theoremOrDeclarationIdentity": "n/a",
        "toolchainContractDigest": NA_SENTINEL,
        "dependencyLockDigest": NA_SENTINEL,
        "artifactHashes": {},
        "replayManifestHash": NA_SENTINEL,
        "executionPolicyId": NA_SENTINEL,
        "assuranceTier": "exact",
    }
    with pytest.raises(ValueError, match="never synthesize|requires real generatorId"):
        _validate_v04_exact_fields(full, capability_id="algebra.ideal_membership_witness")


def test_refutation_must_not_mint_proved() -> None:
    from agent.api.receipt import _validate_v04_exact_fields

    full = {
        "schemaVersion": "0.4.0",
        "outcome": "proved",
        "claimRequested": "refutation",
        "claimEstablished": "refutation",
        "canonicalClaimHash": _zero_digest(),
        "candidateHash": _zero_digest(),
        "generatorId": NA_SENTINEL,
        "generatorVersion": NA_SENTINEL,
        "grammarVersion": NA_SENTINEL,
        "generatedSourceHash": NA_SENTINEL,
        "theoremOrDeclarationIdentity": "n/a",
        "toolchainContractDigest": NA_SENTINEL,
        "dependencyLockDigest": NA_SENTINEL,
        "artifactHashes": {},
        "replayManifestHash": NA_SENTINEL,
        "executionPolicyId": "policy",
        "assuranceTier": "evidence_only",
    }
    with pytest.raises(ValueError, match="refutation|disagrees with claim mapping"):
        _validate_v04_exact_fields(full, capability_id="logic.finite_counterexample")


def test_outcome_must_match_claim_mapping() -> None:
    from agent.api.receipt import _validate_v04_exact_fields

    full = {
        "schemaVersion": "0.4.0",
        "outcome": "refuted",
        "claimRequested": "soundResult",
        "claimEstablished": "soundResult",
        "canonicalClaimHash": _zero_digest(),
        "candidateHash": _zero_digest(),
        "generatorId": NA_SENTINEL,
        "generatorVersion": NA_SENTINEL,
        "grammarVersion": NA_SENTINEL,
        "generatedSourceHash": NA_SENTINEL,
        "theoremOrDeclarationIdentity": "n/a",
        "toolchainContractDigest": NA_SENTINEL,
        "dependencyLockDigest": NA_SENTINEL,
        "artifactHashes": {},
        "replayManifestHash": NA_SENTINEL,
        "executionPolicyId": "policy",
        "assuranceTier": "evidence_only",
    }
    with pytest.raises(ValueError, match="disagrees with claim mapping"):
        _validate_v04_exact_fields(full, capability_id="algebra.ideal_membership_witness")


def test_cex_proved_outcome_rejected_by_allowed_outcomes() -> None:
    """Even a mis-mapped proved must fail registry allowedOutcomes for CEX."""
    from agent.api.receipt import _validate_v04_exact_fields

    full = {
        "schemaVersion": "0.4.0",
        "outcome": "proved",
        "claimRequested": "witness",
        "claimEstablished": "witness",
        "canonicalClaimHash": _zero_digest(),
        "candidateHash": _zero_digest(),
        "generatorId": NA_SENTINEL,
        "generatorVersion": NA_SENTINEL,
        "grammarVersion": NA_SENTINEL,
        "generatedSourceHash": NA_SENTINEL,
        "theoremOrDeclarationIdentity": "n/a",
        "toolchainContractDigest": NA_SENTINEL,
        "dependencyLockDigest": NA_SENTINEL,
        "artifactHashes": {},
        "replayManifestHash": NA_SENTINEL,
        "executionPolicyId": "policy",
        "assuranceTier": "evidence_only",
    }
    with pytest.raises(ValueError, match="allowedOutcomes"):
        _validate_v04_exact_fields(full, capability_id="logic.finite_counterexample")


def test_v03_and_v04_schemas_both_load() -> None:
    store = SchemaStore()
    store.validator("certification-receipt.schema.json")
    store.validator("certification-record.schema.json")
