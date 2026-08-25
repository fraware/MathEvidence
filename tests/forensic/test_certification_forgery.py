"""Forensic tests for Certification Record forgery, freshness, and replay."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.common.bundle import (
    file_digest,
    find_role_path,
    load_role_json,
    write_certification_record,
)
from adapters.common.canonical import sha256_digest
from adapters.common.environment_lock import current_capability_environment_lock
from adapters.common.kernel_replay import find_lake, run_kernel_replay
from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SCHEMA_VERSION,
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    build_replay_target,
    environment_lock_digest,
)
from agent.api.receipt import verify_certification_record
from tests.forensic.test_wave2_kernel_replay import _write_exact_ideal_bundle

ROOT = Path(__file__).resolve().parents[2]
CAPABILITY = "algebra.ideal_membership_witness"


def _write_stale_structural_record(tmp_path: Path) -> tuple[Path, Path]:
    """Write a coherent record with a deliberately stale exact-capability lock.

    This record has valid role/digest structure but no current-environment
    authority. The verifier must therefore stop before independent replay and
    refuse theorem-level verification.
    """
    candidate_dir = tmp_path / "cand"
    _write_exact_ideal_bundle(candidate_dir)
    candidate_manifest = load_role_json(candidate_dir, "manifest")
    request = load_role_json(candidate_dir, "request")
    certificate_path = find_role_path(candidate_dir, "certificate")
    assert certificate_path is not None

    stale_lock = current_capability_environment_lock(ROOT, CAPABILITY)
    stale_lock = dict(stale_lock)
    stale_lock["projectRevision"] = "forensic-stale-revision"
    stale_lock_digest = environment_lock_digest(stale_lock)

    declaration = "forensic_stale_ideal_record"
    identity_digest = sha256_digest({"forensic": "stale-identity"})
    replay_target = build_replay_target(
        module_name=f"MathEvidence.Generated.Replay.{declaration}",
        declaration_name=declaration,
        theorem_type_canonical="forensic-stale-type",
        theorem_type_digest_value=identity_digest,
        source_revision=stale_lock["projectRevision"],
        source_file=f"MathEvidence/Generated/Replay/{declaration}.lean",
        environment_lock_digest_value=stale_lock_digest,
        request_digest=request["requestDigest"],
        capability_id=CAPABILITY,
        capability_version=request["capabilityVersion"],
        candidate_bundle_digest=candidate_manifest["bundleDigest"],
    )
    theorem_identity = {
        "schemaVersion": THEOREM_IDENTITY_SCHEMA_VERSION,
        "serializerVersion": THEOREM_IDENTITY_SERIALIZER_VERSION,
        "declarationName": declaration,
        "theoremTypeDigest": identity_digest,
        "proofDeclarationDigest": identity_digest,
        "environmentLockDigest": stale_lock_digest,
        "environmentLock": stale_lock,
    }
    checker = {
        "package": "MathEvidence.Checkers.IdealMembership",
        "module": "MathEvidence.Checkers.IdealMembership.ReplaySound",
        "name": "checkBool",
        "version": "0.1.0",
        "soundnessTheorem": "replaySound",
    }
    receipt = {
        "schemaVersion": "0.3.0",
        "candidateBundleDigest": candidate_manifest["bundleDigest"],
        "certificationRecordDigest": identity_digest,
        "requestDigest": request["requestDigest"],
        "certificateContentDigest": file_digest(certificate_path),
        "replayTargetDigest": identity_digest,
        "theoremTypeDigest": identity_digest,
        "proofDeclarationDigest": identity_digest,
        "axiomReportDigest": identity_digest,
        "environmentLockDigest": stale_lock_digest,
        "capability": {
            "id": CAPABILITY,
            "version": request["capabilityVersion"],
        },
        "checker": checker,
        "soundnessTheorem": "replaySound",
        "claimRequested": "witness",
        "claimEstablished": "witness",
        "unresolvedObligations": [],
        "assuranceMode": "kernel_replay",
        "resultStatus": "soundness_verified",
        "toolchain": {
            "leanVersion": stale_lock["leanVersion"],
            "lakeVersion": stale_lock["lakeVersion"],
            "mathlibVersion": stale_lock["mathlibRevision"],
        },
    }
    cert_dir = tmp_path / "cert"
    write_certification_record(
        cert_dir,
        candidate_bundle_digest=candidate_manifest["bundleDigest"],
        request_digest=request["requestDigest"],
        capability_id=CAPABILITY,
        capability_version=request["capabilityVersion"],
        claim_class="witness",
        result_status="soundness_verified",
        assurance_mode="kernel_replay",
        replay_target=replay_target,
        checker_evaluation={
            "schemaVersion": "0.3.0",
            "requestDigest": request["requestDigest"],
            "candidateBundleDigest": candidate_manifest["bundleDigest"],
            "resultStatus": "soundness_verified",
            "assuranceMode": "kernel_replay",
            "claimEstablished": "witness",
            "checker": checker,
            "detail": "forensic stale-lock record",
        },
        theorem_identity=theorem_identity,
        axiom_report={
            "schemaVersion": "0.3.0",
            "status": "compiled",
            "declarationName": declaration,
            "axioms": [],
            "allowedAxioms": [],
            "axiomDigests": [],
        },
        certification_receipt=receipt,
    )
    return candidate_dir, cert_dir


def test_forged_theorem_identity_content_rejected(tmp_path: Path) -> None:
    candidate_dir, cert_dir = _write_stale_structural_record(tmp_path)
    identity_path = cert_dir / "theorem-identity.cjson"
    obj = json.loads(identity_path.read_text(encoding="utf-8"))
    obj["theoremTypeDigest"] = "sha256:" + ("ab" * 32)
    identity_path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ValueError, match="theoremTypeDigest|digest|manifest|content"):
        verify_certification_record(cert_dir, candidate_dir=candidate_dir)


def test_stale_environment_lock_downgrades_verified(tmp_path: Path) -> None:
    candidate_dir, cert_dir = _write_stale_structural_record(tmp_path)
    result = verify_certification_record(cert_dir, candidate_dir=candidate_dir)
    assert result.record_integrity_verified is True
    assert result.environment_lock_stale is True
    assert result.environment_lock_current is False
    assert result.kernel_replay_verified is False
    assert result.verified is False


@pytest.mark.skipif(
    find_lake(ROOT) is None,
    reason="lake unavailable; independent exact replay requires Lean",
)
def test_exact_current_record_verifies_by_independent_replay(tmp_path: Path) -> None:
    candidate_dir = tmp_path / "candidate"
    _write_exact_ideal_bundle(candidate_dir)
    cert_dir = tmp_path / "certification"
    produced = run_kernel_replay(
        bundle_dir=candidate_dir,
        repo_root=ROOT,
        declaration_name="forensic_independent_exact_ideal",
        require_lean=True,
        out_record_dir=cert_dir,
    )

    result = verify_certification_record(cert_dir, candidate_dir=candidate_dir)
    assert result.record_integrity_verified is True
    assert result.environment_lock_current is True
    assert result.environment_lock_stale is False
    assert result.kernel_replay_verified is True
    assert result.kernel_replay_error is None
    assert result.verified is True
    assert result.candidate_bundle_digest == produced["candidateBundleDigest"]
    assert result.theorem_type_digest == produced["theoremTypeDigest"]
    assert result.proof_declaration_digest == produced["proofDeclarationDigest"]
    assert result.environment_lock_digest == produced["environmentLockDigest"]
    assert result.claim_established == produced["claimEstablished"] == "witness"
