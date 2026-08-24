"""Certification Record verification and receipt coherence (Wave 1 / P0 repair)."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.common.bundle import (
    VERIFIED_RESULT_STATUSES,
    file_digest,
    find_role_path,
    load_role_json,
    role_from_path,
    verify_bundle_offline,
)
from adapters.common.schema_validate import SchemaStore

VERIFIED_STATUSES = VERIFIED_RESULT_STATUSES


@dataclass(frozen=True)
class CheckerReceipt:
    """Legacy operational receipt view (compat for existing Agent callers)."""

    request_digest: str
    bundle_digest: str | None
    theorem_digest: str | None
    certificate_content_digest: str | None
    claim_established: str | None
    result_status: str
    content_digests_verified: bool = False
    assurance_mode: str | None = None

    @property
    def preview_accepted(self) -> bool:
        return (
            self.result_status in VERIFIED_RESULT_STATUSES
            and self.content_digests_verified
            and self.claim_established is not None
            and self.assurance_mode != "native_checked"
        )


@dataclass(frozen=True)
class CertificationVerification:
    """Result of verifying a complete Certification Record."""

    candidate_bundle_digest: str
    certification_record_digest: str
    request_digest: str
    claim_established: str | None
    result_status: str
    assurance_mode: str
    theorem_type_digest: str
    proof_declaration_digest: str
    axiom_report_digest: str
    environment_lock_digest: str
    verified: bool
    environment_lock_current: bool = True
    environment_lock_stale: bool = False
    record_integrity_verified: bool = True
    kernel_replay_verified: bool = False
    kernel_replay_error: str | None = None

    @property
    def preview_accepted(self) -> bool:
        return self.verified and self.claim_established is not None


def parse_receipt(payload: dict[str, Any]) -> CheckerReceipt:
    """Parse operational checker-receipt fields (legacy / Wave 0 evaluate)."""
    request_digest = _digest(payload.get("requestDigest"), "requestDigest")
    result_status = payload.get("resultStatus")
    if not isinstance(result_status, str) or not result_status:
        raise ValueError("receipt.resultStatus must be a non-empty string")

    claim = payload.get("claimEstablished")
    if claim is not None and not isinstance(claim, str):
        raise ValueError("receipt.claimEstablished must be a string when present")

    assurance = payload.get("assuranceMode")
    if assurance == "native_checked" and result_status in VERIFIED_RESULT_STATUSES:
        raise ValueError(
            "native_checked must not report soundness_verified / verified status"
        )
    if assurance == "kernel_replay":
        th = payload.get("theoremDigest") or payload.get("theoremTypeDigest")
        if not isinstance(th, str) or not th.startswith("sha256:"):
            raise ValueError("kernel_replay requires theorem digest")

    if payload.get("receiptDigest") or payload.get("contentDigest") or payload.get(
        "signatureAlg"
    ):
        from adapters.common.receipt_crypto import verify_receipt_signature_if_present

        gate = verify_receipt_signature_if_present(payload)
        if not gate.get("ok"):
            raise ValueError(gate.get("detail", "receipt crypto verification failed"))

    return CheckerReceipt(
        request_digest=request_digest,
        bundle_digest=_optional_digest(payload.get("bundleDigest"), "bundleDigest"),
        theorem_digest=_optional_digest(
            payload.get("theoremDigest") or payload.get("theoremTypeDigest"),
            "theoremDigest",
        ),
        certificate_content_digest=_optional_digest(
            payload.get("certificateContentDigest")
            or payload.get("certificateDigest"),
            "certificateContentDigest",
        ),
        claim_established=claim,
        result_status=result_status,
        content_digests_verified=bool(payload.get("contentDigestsVerified", False)),
        assurance_mode=assurance if isinstance(assurance, str) else None,
    )


def verify_receipt_against_manifest(
    receipt: CheckerReceipt, manifest: dict[str, Any]
) -> CheckerReceipt:
    """Verify receipt fields that can be checked without Lean kernel replay."""
    manifest_digest = manifest.get("requestDigest")
    if receipt.request_digest != manifest_digest:
        raise ValueError("receipt.requestDigest != manifest.requestDigest")
    if (
        receipt.result_status in VERIFIED_RESULT_STATUSES
        and receipt.claim_established is None
    ):
        raise ValueError("verified receipt missing claimEstablished")
    if (
        receipt.assurance_mode == "native_checked"
        and receipt.result_status in VERIFIED_RESULT_STATUSES
    ):
        raise ValueError("native_checked must not report verified status")
    return receipt


def verify_receipt_content_digests(
    receipt: CheckerReceipt,
    *,
    bundle_dir: Path,
    manifest: dict[str, Any],
) -> CheckerReceipt:
    """Bind receipt certificate digest to on-disk file content when declared."""
    verified = verify_receipt_against_manifest(receipt, manifest)
    cert_path = find_role_path(bundle_dir, "certificate")
    if cert_path is None:
        if verified.result_status in VERIFIED_RESULT_STATUSES:
            raise ValueError("verified receipt requires certificate file on disk")
        return verified

    actual = file_digest(cert_path)
    expected_from_manifest: str | None = None
    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        rel = str(entry.get("path", "")).replace("\\", "/")
        if rel in {"certificate.json", "certificate.cjson"}:
            dig = entry.get("digest")
            if isinstance(dig, str):
                expected_from_manifest = dig
            break

    if expected_from_manifest is not None and actual != expected_from_manifest:
        raise ValueError(
            f"certificate content digest mismatch: {actual} != {expected_from_manifest}"
        )

    if (
        verified.certificate_content_digest is not None
        and verified.certificate_content_digest != actual
    ):
        raise ValueError(
            "receipt.certificateContentDigest != on-disk certificate digest"
        )

    return CheckerReceipt(
        request_digest=verified.request_digest,
        bundle_digest=verified.bundle_digest,
        theorem_digest=verified.theorem_digest,
        certificate_content_digest=verified.certificate_content_digest or actual,
        claim_established=verified.claim_established,
        result_status=verified.result_status,
        content_digests_verified=True,
        assurance_mode=verified.assurance_mode,
    )


def trusted_status_from_receipt(
    payload: dict[str, Any] | None,
    manifest: dict[str, Any],
    *,
    bundle_dir: Path | None = None,
) -> CheckerReceipt | None:
    """Legacy gate: operational receipt only — never theorem authority."""
    if payload is None:
        return None
    if (
        manifest.get("artifactKind") == "candidate"
        or manifest.get("bundleVersion") == "0.3.0"
    ) and "candidateBundleDigest" not in manifest:
        return None
    receipt = parse_receipt(payload)
    if bundle_dir is not None:
        return verify_receipt_content_digests(
            receipt, bundle_dir=bundle_dir, manifest=manifest
        )
    return verify_receipt_against_manifest(receipt, manifest)


def _candidate_store_path(candidate_digest: str) -> Path | None:
    if not candidate_digest.startswith("sha256:") or len(candidate_digest) != 71:
        return None
    root = Path(__file__).resolve().parents[2]
    hex_body = candidate_digest[7:]
    path = root / "evidence" / "store" / "bundles" / "sha256" / hex_body[:2] / hex_body[2:]
    return path if path.is_dir() else None


def _current_lock_digest(capability_id: str) -> str | None:
    root = Path(__file__).resolve().parents[2]
    try:
        from adapters.common.environment_lock import current_capability_environment_lock
        from adapters.common.theorem_identity import environment_lock_digest

        return environment_lock_digest(
            current_capability_environment_lock(root, capability_id)
        )
    except Exception:  # noqa: BLE001
        return None


def _independent_kernel_replay(
    *,
    candidate_dir: Path,
    theorem_identity: dict[str, Any],
    expected_candidate_digest: str,
    expected_claim: str | None,
) -> tuple[bool, str | None]:
    """Re-run the exact candidate and compare Lean-derived theorem/proof identity."""
    try:
        from adapters.common.kernel_replay import run_kernel_replay

        declaration = theorem_identity.get("declarationName")
        if not isinstance(declaration, str) or not declaration:
            return False, "stored theorem identity has no declarationName"
        with tempfile.TemporaryDirectory(prefix="me_open_cert_replay_") as tmp:
            out = run_kernel_replay(
                bundle_dir=candidate_dir,
                repo_root=Path(__file__).resolve().parents[2],
                declaration_name=declaration,
                require_lean=True,
                out_record_dir=Path(tmp) / "certification",
            )
        comparisons = {
            "candidateBundleDigest": expected_candidate_digest,
            "theoremTypeDigest": theorem_identity.get("theoremTypeDigest"),
            "proofDeclarationDigest": theorem_identity.get("proofDeclarationDigest"),
            "environmentLockDigest": theorem_identity.get("environmentLockDigest"),
            "claimEstablished": expected_claim,
        }
        for key, expected in comparisons.items():
            if out.get(key) != expected:
                return False, f"independent replay mismatch for {key}"
        if out.get("identityAuthority") != "Lean.Environment ConstantInfo":
            return False, "independent replay did not use Lean.Environment identity"
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def verify_certification_record(
    record_dir: Path,
    *,
    candidate_dir: Path | None = None,
    schemas: SchemaStore | None = None,
) -> CertificationVerification:
    """Verify record integrity and independently reproduce theorem-level claims.

    `verified=True` now means more than internally coherent JSON: for a
    theorem-level kernel-replay record the exact Candidate Bundle must be
    available and a fresh exact replay must reproduce the stored theorem type,
    proof-term digest, environment lock, claim, and candidate digest.
    """
    verify_bundle_offline(record_dir, schemas=schemas, strict=True)
    manifest = load_role_json(record_dir, "manifest")
    if manifest.get("artifactKind") != "certification":
        raise ValueError("not a Certification Record (artifactKind != certification)")

    receipt = load_role_json(record_dir, "certification-receipt")
    store = schemas or SchemaStore()
    store.validate("certification-receipt.schema.json", receipt)

    mode = receipt.get("assuranceMode")
    status = receipt.get("resultStatus")
    if not isinstance(mode, str) or not isinstance(status, str):
        raise ValueError("certification receipt missing assuranceMode/resultStatus")
    if mode == "native_checked" and status in VERIFIED_RESULT_STATUSES:
        raise ValueError("native_checked must not report theorem-level verified status")
    if mode == "kernel_replay":
        for key in ("theoremTypeDigest", "proofDeclarationDigest"):
            if not isinstance(receipt.get(key), str) or not str(receipt[key]).startswith(
                "sha256:"
            ):
                raise ValueError(f"kernel_replay requires {key}")

    claim = receipt.get("claimEstablished")
    if status in VERIFIED_RESULT_STATUSES and claim in (None, "", False):
        raise ValueError("verified certification requires claimEstablished")
    if status in VERIFIED_RESULT_STATUSES and receipt.get("unresolvedObligations"):
        raise ValueError("verified certification forbids unresolved obligations")

    role_digests: dict[str, str] = {}
    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role") or role_from_path(str(entry.get("path", "")))
        dig = entry.get("digest")
        if isinstance(role, str) and isinstance(dig, str):
            role_digests[role] = dig
    for receipt_key, role in {
        "replayTargetDigest": "replay-target",
        "axiomReportDigest": "axiom-report",
    }.items():
        expected = role_digests.get(role)
        declared = receipt.get(receipt_key)
        if expected and declared and declared != expected:
            raise ValueError(f"receipt.{receipt_key} != on-disk {role} digest")

    theorem_obj = load_role_json(record_dir, "theorem-identity")
    target_obj = load_role_json(record_dir, "replay-target")
    for key in ("theoremTypeDigest", "proofDeclarationDigest", "environmentLockDigest"):
        declared = receipt.get(key)
        identity_val = theorem_obj.get(key)
        if isinstance(identity_val, str) and isinstance(declared, str):
            if identity_val != declared:
                raise ValueError(f"receipt.{key} != theorem-identity.{key}")

    candidate_digest = manifest.get("candidateBundleDigest")
    if not isinstance(candidate_digest, str):
        raise ValueError("certification manifest missing candidateBundleDigest")
    if receipt.get("candidateBundleDigest") != candidate_digest:
        raise ValueError("receipt.candidateBundleDigest != manifest.candidateBundleDigest")

    manifest_request = manifest.get("requestDigest")
    if target_obj.get("candidateBundleDigest") != candidate_digest:
        raise ValueError("replay-target.candidateBundleDigest != certification candidate")
    if target_obj.get("requestDigest") != manifest_request:
        raise ValueError("replay-target.requestDigest != certification requestDigest")
    manifest_cap = manifest.get("capability") or {}
    if target_obj.get("capability") != manifest_cap:
        raise ValueError("replay-target.capability != certification capability")
    if target_obj.get("declarationName") != theorem_obj.get("declarationName"):
        raise ValueError("replay-target.declarationName != theorem identity declarationName")
    if target_obj.get("theoremTypeDigest") != theorem_obj.get("theoremTypeDigest"):
        raise ValueError("replay-target.theoremTypeDigest != theorem identity digest")
    if target_obj.get("environmentLockDigest") != theorem_obj.get("environmentLockDigest"):
        raise ValueError("replay-target.environmentLockDigest != theorem identity environment")

    # Recompute theorem type digest from the structural snapshot stored in the
    # role. A producer cannot change the snapshot without changing the digest.
    if isinstance(theorem_obj.get("elaboratedSerialization"), str):
        from adapters.common.theorem_identity import theorem_type_digest

        structural = {
            "schemaVersion": theorem_obj.get("schemaVersion"),
            "serializerVersion": theorem_obj.get("serializerVersion"),
            "elaboratedSerialization": theorem_obj["elaboratedSerialization"],
            "universeParams": theorem_obj.get("universeParams") or [],
            "binders": theorem_obj.get("binders") or [],
            "constantNames": theorem_obj.get("constantNames") or [],
            "environmentLockDigest": theorem_obj.get("environmentLockDigest"),
        }
        if theorem_type_digest(structural) != theorem_obj.get("theoremTypeDigest"):
            raise ValueError("theorem identity structural snapshot digest mismatch")

    cert_digest = manifest.get("certificationDigest") or manifest.get("bundleDigest")
    if not isinstance(cert_digest, str):
        raise ValueError("certification digest missing")
    if receipt.get("certificationRecordDigest") != cert_digest:
        raise ValueError("receipt.certificationRecordDigest != manifest.certificationDigest")

    if candidate_dir is None:
        candidate_dir = _candidate_store_path(candidate_digest)
    if candidate_dir is not None:
        verify_bundle_offline(candidate_dir, schemas=schemas, strict=True)
        cand_manifest = load_role_json(candidate_dir, "manifest")
        if cand_manifest.get("bundleDigest") != candidate_digest:
            raise ValueError("candidate bundleDigest mismatch")
        if cand_manifest.get("requestDigest") != manifest_request:
            raise ValueError("candidate requestDigest != Certification Record requestDigest")
        cert_path = find_role_path(candidate_dir, "certificate")
        if cert_path is None:
            raise ValueError("candidate has no certificate role")
        actual_cert = file_digest(cert_path)
        if receipt.get("certificateContentDigest") != actual_cert:
            raise ValueError("receipt.certificateContentDigest != candidate certificate digest")

    capability_id = str(manifest_cap.get("id") or "")
    current_lock_digest = _current_lock_digest(capability_id)
    record_lock = str(receipt.get("environmentLockDigest") or "")
    lock_current = bool(current_lock_digest) and record_lock == current_lock_digest
    lock_stale = bool(record_lock) and not lock_current

    replay_verified = False
    replay_error: str | None = None
    if (
        status in VERIFIED_RESULT_STATUSES
        and mode == "kernel_replay"
        and candidate_dir is not None
        and lock_current
    ):
        replay_verified, replay_error = _independent_kernel_replay(
            candidate_dir=candidate_dir,
            theorem_identity=theorem_obj,
            expected_candidate_digest=candidate_digest,
            expected_claim=claim if isinstance(claim, str) else None,
        )

    verified = (
        status in VERIFIED_RESULT_STATUSES
        and isinstance(claim, str)
        and mode == "kernel_replay"
        and not receipt.get("unresolvedObligations")
        and lock_current
        and replay_verified
    )

    return CertificationVerification(
        candidate_bundle_digest=candidate_digest,
        certification_record_digest=cert_digest,
        request_digest=str(receipt.get("requestDigest") or manifest_request),
        claim_established=claim if isinstance(claim, str) else None,
        result_status=status,
        assurance_mode=mode,
        theorem_type_digest=str(receipt.get("theoremTypeDigest")),
        proof_declaration_digest=str(receipt.get("proofDeclarationDigest")),
        axiom_report_digest=str(receipt.get("axiomReportDigest")),
        environment_lock_digest=record_lock,
        verified=verified,
        environment_lock_current=lock_current,
        environment_lock_stale=lock_stale,
        record_integrity_verified=True,
        kernel_replay_verified=replay_verified,
        kernel_replay_error=replay_error,
    )


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"receipt.{field} must be a sha256 digest")
    return value


def _optional_digest(value: Any, field: str) -> str | None:
    if value is None or value == "":
        return None
    return _digest(value, field)
