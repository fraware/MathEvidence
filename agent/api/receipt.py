"""Checker receipt parsing and content-digest binding for Agent API trust status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.common.bundle import file_digest, find_role_path


VERIFIED_STATUSES = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "native_verified",
    }
)


@dataclass(frozen=True)
class CheckerReceipt:
    request_digest: str
    bundle_digest: str | None
    theorem_digest: str | None
    certificate_content_digest: str | None
    claim_established: str | None
    result_status: str
    content_digests_verified: bool = False

    @property
    def preview_accepted(self) -> bool:
        return (
            self.result_status in VERIFIED_STATUSES
            and self.content_digests_verified
            and self.claim_established is not None
        )


def parse_receipt(payload: dict[str, Any]) -> CheckerReceipt:
    """Parse the stable fields expected from a Lean checker receipt.

    When ``receiptDigest`` / ``contentDigest`` / ``signatureAlg`` are present,
    verify them via ``adapters.common.receipt_crypto`` (dev HMAC/Ed25519 only).
    This prevents Python summaries from fabricating ``claimEstablished`` from a
    manifest's ``resultStatus`` alone and binds optional certificate content digests.
    """
    request_digest = _digest(payload.get("requestDigest"), "requestDigest")
    result_status = payload.get("resultStatus")
    if not isinstance(result_status, str) or not result_status:
        raise ValueError("receipt.resultStatus must be a non-empty string")

    claim = payload.get("claimEstablished")
    if claim is not None and not isinstance(claim, str):
        raise ValueError("receipt.claimEstablished must be a string when present")

    if payload.get("receiptDigest") or payload.get("contentDigest") or payload.get(
        "signatureAlg"
    ):
        from adapters.common.receipt_crypto import verify_receipt_signature_if_present

        gate = verify_receipt_signature_if_present(payload)
        if not gate.get("ok"):
            raise ValueError(gate.get("detail", "receipt crypto verification failed"))

    return CheckerReceipt(
        request_digest=request_digest,
        bundle_digest=_optional_digest(
            payload.get("bundleDigest"), "bundleDigest"
        ),
        theorem_digest=_optional_digest(
            payload.get("theoremDigest"), "theoremDigest"
        ),
        certificate_content_digest=_optional_digest(
            payload.get("certificateContentDigest")
            or payload.get("certificateDigest"),
            "certificateContentDigest",
        ),
        claim_established=claim,
        result_status=result_status,
        content_digests_verified=bool(payload.get("contentDigestsVerified", False)),
    )


def verify_receipt_against_manifest(
    receipt: CheckerReceipt, manifest: dict[str, Any]
) -> CheckerReceipt:
    """Verify receipt fields that can be checked without Lean kernel replay."""
    manifest_digest = manifest.get("requestDigest")
    if receipt.request_digest != manifest_digest:
        raise ValueError("receipt.requestDigest != manifest.requestDigest")
    if (
        receipt.result_status in VERIFIED_STATUSES
        and receipt.claim_established is None
    ):
        raise ValueError("verified receipt missing claimEstablished")
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
        if verified.result_status in VERIFIED_STATUSES:
            raise ValueError("verified receipt requires certificate file on disk")
        return verified

    actual = file_digest(cert_path)
    # Manifest file digests are authoritative for content binding.
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
    )


def trusted_status_from_receipt(
    payload: dict[str, Any] | None,
    manifest: dict[str, Any],
    *,
    bundle_dir: Path | None = None,
) -> CheckerReceipt | None:
    """Return a receipt only when it is present and internally consistent.

    When ``bundle_dir`` is provided, certificate content digests are verified
    against on-disk bytes before any verified status is trusted.
    """
    if payload is None:
        return None
    receipt = parse_receipt(payload)
    if bundle_dir is not None:
        return verify_receipt_content_digests(
            receipt, bundle_dir=bundle_dir, manifest=manifest
        )
    return verify_receipt_against_manifest(receipt, manifest)


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"receipt.{field} must be a sha256 digest")
    return value


def _optional_digest(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _digest(value, field)
