"""Forensic: forged Certification Records and stale environment locks must not verify."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.common.bundle import write_candidate_bundle, write_certification_record
from adapters.common.canonical import sha256_digest
from adapters.common.theorem_identity import (
    default_rational_environment_lock,
    environment_lock_digest,
)
from agent.api.receipt import verify_certification_record
from tests.forensic.test_bundle_v03 import (
    _minimal_certificate,
    _minimal_rational_request,
)


def _write_kernel_cert(tmp_path: Path, *, env_lock: str | None = None) -> Path:
    request = _minimal_rational_request()
    cand = tmp_path / "cand"
    cand_manifest = write_candidate_bundle(
        cand,
        request=request,
        candidate={},
        certificate=_minimal_certificate(request["requestDigest"]),
    )
    lock = env_lock or environment_lock_digest(default_rational_environment_lock())
    d = sha256_digest({"k": "v"})
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
            "detail": "forensic",
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
            "environmentLockDigest": lock,
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


def test_forged_theorem_type_digest_rejected(tmp_path: Path) -> None:
    cert_dir = _write_kernel_cert(tmp_path)
    identity_path = cert_dir / "theorem-identity.cjson"
    obj = json.loads(identity_path.read_text(encoding="utf-8"))
    obj["theoremTypeDigest"] = "sha256:" + ("ab" * 32)
    identity_path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ValueError, match="theoremTypeDigest|digest|manifest|content"):
        verify_certification_record(cert_dir)


def test_stale_environment_lock_downgrades_verified(tmp_path: Path) -> None:
    stale = "sha256:" + ("cd" * 32)
    cert_dir = _write_kernel_cert(tmp_path, env_lock=stale)
    result = verify_certification_record(cert_dir)
    assert result.environment_lock_stale is True
    assert result.environment_lock_current is False
    assert result.verified is False


def test_current_environment_lock_can_verify(tmp_path: Path) -> None:
    cert_dir = _write_kernel_cert(tmp_path)
    result = verify_certification_record(cert_dir)
    assert result.environment_lock_current is True
    assert result.environment_lock_stale is False
    assert result.verified is True
