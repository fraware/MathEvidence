"""Product 09 epistemic contract (Studio reference implementation).

Studio is a client of Lean/IR/Agent APIs only — no unique mathematical
semantics live here. This module mirrors the Certified gate used by
``studio/vscode/epistemic.js`` and ``studio/wolfram/MathEvidenceStudio.wl``.

Hard rules (Wave 2 / ME-RV-024)
-------------------------------
1. Certified ⇔ Agent ``certificationVerified: true`` PLUS certification record id
   PLUS claim/theorem identity fields — never from a raw receipt object alone.
2. Lean proposition + assumptions are always rendered *before* any
   Certified affordance in the certification surface transcript.
3. Manifest-only verified statuses without Certification Record → Ambiguous/Tested.
4. Operational verify-bundle (``native_checked`` / ``checker_accepted``) never Certified.
"""

from __future__ import annotations

from typing import Any

LEAN_OK_STATUSES: frozenset[str] = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "approximation_certified",
        "native_verified",
    }
)

EpistemicLabel = str  # Computed | Tested | Certified | Ambiguous


def normalize_status(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def lean_status_allows_certified(lean_status: Any) -> bool:
    """Legacy helper — insufficient alone for Certified (ME-RV-024)."""
    return normalize_status(lean_status) in LEAN_OK_STATUSES


def certification_gate(
    *,
    certification_verified: Any = None,
    certification_id: Any = None,
    claim_established: Any = None,
    theorem_type_digest: Any = None,
    result_status: Any = None,
) -> dict[str, Any]:
    """Wave 2 Certified gate: Agent certificationVerified + record id + claim/theorem."""
    verified = certification_verified is True
    cert_id_ok = isinstance(certification_id, str) and bool(certification_id.strip())
    claim_ok = isinstance(claim_established, str) and bool(claim_established.strip())
    theorem_ok = (
        isinstance(theorem_type_digest, str)
        and theorem_type_digest.startswith("sha256:")
    )
    status = normalize_status(result_status)
    status_ok = status in LEAN_OK_STATUSES or status == ""

    if verified and cert_id_ok and claim_ok and theorem_ok and status_ok:
        return {
            "label": "Certified",
            "detail": (
                f"Certification Record verified ({certification_id}); "
                f"claimEstablished={claim_established}."
            ),
            "allowCertified": True,
        }
    missing: list[str] = []
    if not verified:
        missing.append("certificationVerified")
    if not cert_id_ok:
        missing.append("certificationId")
    if not claim_ok:
        missing.append("claimEstablished")
    if not theorem_ok:
        missing.append("theoremTypeDigest")
    return {
        "label": "Ambiguous" if status in LEAN_OK_STATUSES else "Tested",
        "detail": (
            "Certified requires Agent certificationVerified + certificationId + "
            f"claimEstablished + theoremTypeDigest (missing: {', '.join(missing) or 'none'})."
        ),
        "allowCertified": False,
    }


def epistemic_from_result_status(
    result_status: Any,
    lean_status: Any = None,
    *,
    certification_verified: Any = None,
    certification_id: Any = None,
    claim_established: Any = None,
    theorem_type_digest: Any = None,
) -> dict[str, Any]:
    """Map machine resultStatus + certification gate → UI label/detail/AllowCertified."""
    # Prefer explicit Certification Record gate when any certification field is present.
    if (
        certification_verified is not None
        or (isinstance(certification_id, str) and certification_id)
        or (isinstance(theorem_type_digest, str) and theorem_type_digest)
    ):
        return certification_gate(
            certification_verified=certification_verified,
            certification_id=certification_id,
            claim_established=claim_established,
            theorem_type_digest=theorem_type_digest,
            result_status=result_status or lean_status,
        )

    s = normalize_status(result_status)
    lean = lean_status
    lean_norm = normalize_status(lean)

    # Raw leanStatus alone must not grant Certified (ME-RV-024).
    if lean_status_allows_certified(lean) or s in LEAN_OK_STATUSES:
        return {
            "label": "Ambiguous",
            "detail": (
                "Manifest/Lean status alone is insufficient for Certified; "
                "open_certification must return certificationVerified=true."
            ),
            "allowCertified": False,
        }
    if s in ("tested", "checker_accepted"):
        return {
            "label": "Tested",
            "detail": (
                "Offline schema/digest checks and/or operational checkBool succeeded; "
                "theorem Certified requires a Certification Record (not verify-bundle)."
            ),
            "allowCertified": False,
        }
    if s == "computed":
        return {
            "label": "Computed",
            "detail": "Backend/candidate output only. Not Lean-certified.",
            "allowCertified": False,
        }
    if s in ("ambiguous", "rejected", "unsupported", ""):
        return {
            "label": "Ambiguous",
            "detail": "Status is ambiguous, rejected, unsupported, or missing.",
            "allowCertified": False,
        }
    return {
        "label": "Ambiguous",
        "detail": f"Unrecognized resultStatus: {result_status}",
        "allowCertified": False,
    }


def extract_assumptions(request: dict[str, Any] | None) -> list[Any]:
    """Assumptions from request IR fields only (no Studio invention)."""
    if not isinstance(request, dict):
        return []
    for key in ("knownAssumptions", "domainConditions", "assumptions"):
        raw = request.get(key)
        if isinstance(raw, list):
            return list(raw)
    return []


def extract_lean_proposition(
    *,
    lean_proposition: Any = None,
    theorem_preview: Any = None,
    request: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> str:
    """Prefer explicit Lean/Agent fields; never invent checker semantics."""
    for candidate in (
        lean_proposition,
        theorem_preview,
        (manifest or {}).get("leanProposition") if isinstance(manifest, dict) else None,
        (manifest or {}).get("theoremPreview") if isinstance(manifest, dict) else None,
        (request or {}).get("leanProposition") if isinstance(request, dict) else None,
        (request or {}).get("theoremPreview") if isinstance(request, dict) else None,
        (request or {}).get("proposedLeanProposition")
        if isinstance(request, dict)
        else None,
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def build_certification_surface(
    *,
    result_status: Any,
    lean_status: Any = None,
    lean_proposition: Any = None,
    theorem_preview: Any = None,
    request: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    assumptions: list[Any] | None = None,
    certification_verified: Any = None,
    certification_id: Any = None,
    claim_established: Any = None,
    theorem_type_digest: Any = None,
) -> dict[str, Any]:
    """Ordered certification surface: proposition → assumptions → epistemic."""
    proposition = extract_lean_proposition(
        lean_proposition=lean_proposition,
        theorem_preview=theorem_preview,
        request=request,
        manifest=manifest,
    )
    assumps = (
        list(assumptions)
        if assumptions is not None
        else extract_assumptions(request)
    )
    epi = epistemic_from_result_status(
        result_status,
        lean_status,
        certification_verified=certification_verified,
        certification_id=certification_id,
        claim_established=claim_established,
        theorem_type_digest=theorem_type_digest,
    )

    # Exact Lean proposition must be available before Certified labeling.
    if epi["allowCertified"] and not proposition:
        epi = {
            "label": "Ambiguous",
            "detail": (
                "Certification Record is present, but the exact Lean proposition is not "
                "available yet. Not labeled Certified."
            ),
            "allowCertified": False,
        }

    transcript = [
        {
            "section": "leanProposition",
            "title": "Proposed Lean proposition",
            "body": proposition
            or "(Lean proposition not yet available — required before Certified)",
        },
        {
            "section": "assumptions",
            "title": "Assumptions / side conditions",
            "body": assumps if assumps else [],
            "emptyNote": "(none listed — confirm no hidden defaults)",
        },
        {
            "section": "epistemicLabel",
            "title": "Epistemic state",
            "body": epi["label"],
            "detail": epi["detail"],
            "allowCertified": epi["allowCertified"],
        },
    ]

    return {
        "epistemic": epi,
        "leanProposition": proposition,
        "assumptions": assumps,
        "transcript": transcript,
        "transcriptOrder": [t["section"] for t in transcript],
        "certifiedAffordanceIndex": next(
            i for i, t in enumerate(transcript) if t["section"] == "epistemicLabel"
        ),
        "receiptVerified": False,
        "certificationVerified": bool(certification_verified is True),
    }


def verify_checker_receipt(
    receipt: dict[str, Any] | None,
    *,
    expected_request_digest: str | None = None,
) -> dict[str, Any]:
    """Structural receipt checks are diagnostic only — never grant Certified.

    ME-RV-024: Certified requires ``certification_gate`` / Agent
    ``open_certification`` with ``certificationVerified: true``.
    """
    if not isinstance(receipt, dict):
        return {
            "ok": False,
            "allowCertified": False,
            "detail": "checker receipt missing",
        }
    req = receipt.get("requestDigest")
    status = normalize_status(receipt.get("resultStatus"))
    if not isinstance(req, str) or not req.startswith("sha256:"):
        return {
            "ok": False,
            "allowCertified": False,
            "detail": "receipt.requestDigest missing or malformed",
        }
    if expected_request_digest and req != expected_request_digest:
        return {
            "ok": False,
            "allowCertified": False,
            "detail": "receipt.requestDigest does not match expected request",
        }

    crypto_gate: dict[str, Any] | None = None
    if receipt.get("receiptDigest") or receipt.get("contentDigest") or receipt.get(
        "signatureAlg"
    ):
        from adapters.common.receipt_crypto import verify_receipt_signature_if_present

        crypto_gate = verify_receipt_signature_if_present(receipt)
        if not crypto_gate.get("ok"):
            return {
                "ok": False,
                "allowCertified": False,
                "detail": crypto_gate.get("detail", "receipt crypto verification failed"),
                "crypto": crypto_gate,
            }

    out = {
        "ok": True,
        "allowCertified": False,
        "detail": (
            "receipt structurally present (diagnostic only); "
            "Certified requires open_certification / certificationVerified"
        ),
    }
    if crypto_gate is not None:
        out["crypto"] = crypto_gate
    if status in LEAN_OK_STATUSES:
        out["detail"] = (
            "receipt advertises verified status but Studio refuses Certified "
            "without Agent certificationVerified + record id + theorem fields"
        )
    return out
