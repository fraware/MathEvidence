"""Product 09 epistemic contract (Studio reference implementation).

Studio is a client of Lean/IR/Agent APIs only — no unique mathematical
semantics live here. This module mirrors the Certified gate used by
``studio/vscode/epistemic.js`` and ``studio/wolfram/MathEvidenceStudio.wl``.

Hard rules
----------
1. Certified ⇔ leanStatus ∈ LEAN_OK_STATUSES
2. Lean proposition + assumptions are always rendered *before* any
   Certified affordance in the certification surface transcript
3. Manifest-only verified statuses without Lean → Ambiguous
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
    return normalize_status(lean_status) in LEAN_OK_STATUSES


def epistemic_from_result_status(
    result_status: Any,
    lean_status: Any = None,
) -> dict[str, Any]:
    """Map machine resultStatus + Lean status → UI label/detail/AllowCertified."""
    s = normalize_status(result_status)
    lean = lean_status
    lean_norm = normalize_status(lean)

    if lean_status_allows_certified(lean):
        return {
            "label": "Certified",
            "detail": f"Lean status present: {lean}.",
            "allowCertified": True,
        }

    if s in LEAN_OK_STATUSES:
        return {
            "label": "Ambiguous",
            "detail": (
                "Manifest claims a verified status, but Lean status is missing. "
                "Not labeled Certified."
            ),
            "allowCertified": False,
        }
    if s == "tested":
        return {
            "label": "Tested",
            "detail": (
                "Offline schema/digest checks succeeded; Lean certification not asserted."
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
) -> dict[str, Any]:
    """Ordered certification surface: proposition → assumptions → epistemic.

    The Certified affordance appears only after proposition and assumptions
    sections. If Lean would allow Certified but the exact Lean proposition
    string is missing, the UI remains Ambiguous (Product 09 §5 / acceptance #4).
    """
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
    epi = epistemic_from_result_status(result_status, lean_status)

    # Exact Lean proposition must be available before Certified labeling.
    if epi["allowCertified"] and not proposition:
        epi = {
            "label": "Ambiguous",
            "detail": (
                "Lean status is present, but the exact Lean proposition is not "
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
    }


def verify_checker_receipt(
    receipt: dict[str, Any] | None,
    *,
    expected_request_digest: str | None = None,
) -> dict[str, Any]:
    """Shared Studio/Agent receipt gate (ME-307).

    Certified must not be derived from manifest/`leanStatus` alone when a receipt
    object is in play — require structural receipt fields and digest match.
    When a content digest or signature is present, verify via
    ``adapters.common.receipt_crypto`` (dev HMAC/Ed25519 only; not production PKI).
    """
    if not isinstance(receipt, dict):
        return {
            "ok": False,
            "allowCertified": False,
            "detail": "checker receipt missing",
        }
    req = receipt.get("requestDigest")
    status = normalize_status(receipt.get("resultStatus"))
    established = receipt.get("claimEstablished")
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

    if status not in LEAN_OK_STATUSES or established in (None, "", False):
        out = {
            "ok": True,
            "allowCertified": False,
            "detail": "receipt present but does not establish a certified claim",
        }
        if crypto_gate is not None:
            out["crypto"] = crypto_gate
        return out
    out = {
        "ok": True,
        "allowCertified": True,
        "detail": "checker receipt structurally verifies claimEstablished",
    }
    if crypto_gate is not None:
        out["crypto"] = crypto_gate
    return out
