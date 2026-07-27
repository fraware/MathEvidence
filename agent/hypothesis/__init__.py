"""Hypothesis Synthesis orchestration (Product 03) — Agent-side, not TCB.

Sufficiency, deletion, and CEX verification return status only from the Python
mirror of Lean ``checkBool`` (``authorityStatus: python_checker_mirror``).
Mirror acceptance is ``mirror_accepted`` / ``mirrorSufficient`` — never a
theorem claim. A set enters ``sufficientSetsCertified`` only after a verified
Certification Record (kernel certification).
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from adapters.common.canonical import bind_request_digest
from adapters.common.hypothesis_util import (
    find_counterexample,
    propose_conditions_from_request,
)
from adapters.common.lean_mirrors import check_finite_counterexample
from adapters.common.lean_mirrors import check_rational_equality
from adapters.common.rational_ir import collect_division_denominators
from adapters.common.schema_validate import SchemaStore

from agent.epistemic_states import (
    AUTHORITY_LEAN_KERNEL,
    AUTHORITY_PYTHON_MIRROR,
    PRODUCT_STATES,
)

__all__ = [
    "AUTHORITY_STATUS",
    "CONDITION_NODE_KINDS",
    "PRODUCT_STATES",
    "SUFFICIENCY_THEOREM_DECL",
    "SUFFICIENCY_CHECKER_DECL",
    "build_condition_lattice",
    "certify_sufficient_set",
    "delete_hypothesis_python",
    "make_condition_node",
    "make_sufficient_set_record",
    "minimality_allowed",
    "propose_conditions_from_request",
    "prove_sufficient_python",
    "verify_counterexample_python",
]

# Agent may only assert mirror acceptance via Lean checker mirrors.
AUTHORITY_STATUS = AUTHORITY_PYTHON_MIRROR

SUFFICIENCY_THEOREM_DECL = "MathEvidence.Hypothesis.sufficient_implies_proposition"
SUFFICIENCY_CHECKER_DECL = "MathEvidence.Checkers.RationalEquality.checkBool"

_AUTHORITY_NOTES = [
    "Status from Python mirror of Lean RationalEquality/Counterexample.checkBool.",
    "mirror_accepted is not a theorem claim; kernel_certified requires Certification Record.",
    "Minimality is never asserted here by default.",
    "Denom coverage alone is never sufficiency (poly identity required).",
]

CONDITION_NODE_KINDS = (
    "nonzero_denominator",
    "domain_restriction",
    "hypothesis_literal",
    "imported_assumption",
)


def make_condition_node(
    *,
    node_id: str,
    kind: str,
    expr: dict[str, Any],
    lean_prop_hint: str | None = None,
    role: str = "original_division",
    evidence_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a typed condition node (Agent-side; sufficiency still Lean-mirrored)."""
    if kind not in CONDITION_NODE_KINDS:
        raise ValueError(f"unsupported condition node kind: {kind}")
    return {
        "id": node_id,
        "kind": kind,
        "expr": expr,
        "role": role,
        "leanPropHint": lean_prop_hint,
        "sufficiencyRequires": "lean_proof_and_receipt",
        "evidenceRefs": list(evidence_refs or []),
    }


def make_sufficient_set_record(
    condition_ids: list[str],
    *,
    preview_status: str = "mirror_accepted",
    candidate_bundle_id: str | None = None,
    certification_record_id: str | None = None,
    theorem_declaration: str | None = None,
    assumptions: list[str] | None = None,
    reviewer_status: str = "unreviewed",
) -> dict[str, Any]:
    """Lattice node for a sufficient-set candidate or certified entry."""
    if preview_status not in PRODUCT_STATES and preview_status not in {
        "sufficient_member",
        "unreviewed",
    }:
        raise ValueError(f"unsupported preview_status: {preview_status}")
    return {
        "conditionIds": list(condition_ids),
        "previewStatus": preview_status,
        "candidateBundleId": candidate_bundle_id,
        "certificationRecordId": certification_record_id,
        "theoremDeclaration": theorem_declaration,
        "assumptions": list(assumptions or condition_ids),
        "reviewerStatus": reviewer_status,
    }


def _condition_exprs(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    factors: list[dict[str, Any]] = []
    for c in conditions:
        expr = c.get("expr")
        if isinstance(expr, dict):
            factors.append(
                {
                    "expr": expr,
                    "role": c.get("role") or "original_division",
                    "multiplicity": int(c.get("multiplicity") or 1),
                }
            )
    return factors


def _ensure_rational_request(request: dict[str, Any]) -> dict[str, Any]:
    """Normalize a rational-equality request for mirror checking."""
    out = dict(request)
    out.setdefault("schemaVersion", "0.1.0")
    out.setdefault("capability", "algebra.rational_equality")
    out.setdefault("capabilityVersion", "0.1.0")
    out.setdefault("requestedClaim", "soundResult")
    out.setdefault(
        "resourcePolicy",
        {"maxWallTimeMs": 30_000, "maxOutputBytes": 1_048_576},
    )
    if "variables" not in out:
        out["variables"] = out.get("variables") or [{"name": "x", "type": "Rat"}]
    return bind_request_digest(out)


def _certificate_for_conditions(
    request: dict[str, Any], conditions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": request.get("capabilityVersion", "0.1.0"),
        "requestDigest": request["requestDigest"],
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": _condition_exprs(conditions),
        "factorization": {
            "method": "agent.hypothesis.sufficiency_preview",
            "notes": "Untrusted candidate; Lean checkBool owns acceptance.",
        },
        "provenance": {
            "backendId": "agent.hypothesis",
            "adapterVersion": "0.1.0",
            "deterministic": True,
        },
    }


def _factor_exprs(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        f["expr"]
        for f in _condition_exprs(conditions)
        if isinstance(f.get("expr"), dict)
    ]


def _denom_coverage_only(request: dict[str, Any], conditions: list[dict[str, Any]]) -> bool:
    """True when listed factors cover all division denominators (not sufficiency)."""
    factors = _factor_exprs(conditions)
    for dens in collect_division_denominators(request.get("lhs", {})) + collect_division_denominators(
        request.get("rhs", {})
    ):
        if dens not in factors:
            return False
    return True


def _typed_evidence(
    request: dict[str, Any],
    *,
    detail: str,
    receipt_ref: dict[str, Any] | None,
    bundle_ref: dict[str, Any] | None,
    axiom_report_id: str | None,
) -> dict[str, Any]:
    receipt_id = ""
    if isinstance(receipt_ref, dict):
        receipt_id = str(
            receipt_ref.get("receiptId")
            or receipt_ref.get("id")
            or receipt_ref.get("digest")
            or ""
        )
    axiom_id = axiom_report_id or ""
    if isinstance(bundle_ref, dict) and not axiom_id:
        axiom_id = str(bundle_ref.get("axiomReportId") or "")
    return {
        "theoremDecl": SUFFICIENCY_THEOREM_DECL,
        "checkerDecl": SUFFICIENCY_CHECKER_DECL,
        "receiptId": receipt_id,
        "axiomReportId": axiom_id,
        "requestDigest": request.get("requestDigest") or "",
        "detail": detail,
    }


def prove_sufficient_python(
    request: dict[str, Any],
    conditions: list[dict[str, Any]],
    *,
    poly_zero: bool | None = None,
    bundle_ref: dict[str, Any] | None = None,
    receipt_ref: dict[str, Any] | None = None,
    axiom_report_id: str | None = None,
) -> dict[str, Any]:
    """Sufficiency preview via Lean RationalEquality.checkBool mirror only.

    Returns distinct ``outcome`` values:
    * ``mirror_accepted`` — mirror accepts (poly identity + denom coverage + digest)
    * ``rejected`` — mirror rejects (never from coverage alone)
    * ``unknown`` — reserved; default rational path always decides

    Never emits theorem evidence or empty receipt as certified proof.
    ``poly_zero`` is ignored (API compatibility); poly identity is mirror-decided.
    """
    del poly_zero
    req = _ensure_rational_request(request)
    cert = _certificate_for_conditions(req, conditions)
    cover_only = _denom_coverage_only(req, conditions)
    ok = check_rational_equality(req, cert)

    evidence_refs: list[dict[str, Any]] = []
    if isinstance(bundle_ref, dict) and bundle_ref:
        evidence_refs.append({"kind": "bundle", **bundle_ref})
    if isinstance(receipt_ref, dict) and receipt_ref:
        evidence_refs.append({"kind": "checker_receipt", **receipt_ref})

    if ok:
        outcome = "mirror_accepted"
        detail = "checkBool_accept"
    elif cover_only:
        outcome = "rejected"
        detail = "poly_identity_failed_despite_denom_coverage"
    else:
        outcome = "rejected"
        detail = "denom_coverage_incomplete_or_digest_or_ill_formed"

    evidence = _typed_evidence(
        req,
        detail=detail,
        receipt_ref=receipt_ref,
        bundle_ref=bundle_ref,
        axiom_report_id=axiom_report_id,
    )
    # Empty / citation-only receipt ids are never theorem evidence.
    if evidence["receiptId"] == "" and outcome == "mirror_accepted":
        evidence["detail"] = f"{detail};preview_only_no_certification_record"

    return {
        "outcome": outcome,
        "mirrorSufficient": ok,
        # Deprecated alias — same as mirrorSufficient; not kernel certification.
        "sufficient": ok,
        "authorityStatus": AUTHORITY_STATUS,
        "requestDigest": req["requestDigest"],
        "denominatorsCovered": cover_only,
        "evidence": evidence,
        "evidenceRefs": evidence_refs,
        "notes": list(_AUTHORITY_NOTES)
        + (
            ["Sufficiency evidence refs are citations only; Certification Record owns Certified."]
            if evidence_refs
            else ["No evidenceRefs: sufficiency preview only."]
        )
        + (
            ["Refused to mark sufficient from denom coverage alone."]
            if (cover_only and not ok)
            else []
        ),
    }


def delete_hypothesis_python(
    request: dict[str, Any],
    conditions: list[dict[str, Any]],
    target_id: str,
    *,
    poly_zero: bool | None = None,
) -> dict[str, Any]:
    """Deletion redundancy via Lean sufficiency mirror (checkBool)."""
    del poly_zero
    remaining = [c for c in conditions if c.get("id") != target_id]
    if len(remaining) == len(conditions):
        return {
            "result": "missing",
            "remaining": conditions,
            "authorityStatus": AUTHORITY_STATUS,
            "notes": list(_AUTHORITY_NOTES),
        }
    preview = prove_sufficient_python(request, remaining)
    if preview["outcome"] == "mirror_accepted":
        return {
            "result": "redundant",
            "remaining": remaining,
            "justification": "python_checker_mirror_sufficiency",
            "authorityStatus": AUTHORITY_STATUS,
            "notes": list(_AUTHORITY_NOTES)
            + ["Redundancy justified only by checker-mirror sufficiency preview."],
        }
    return {
        "result": "not_redundant",
        "remaining": remaining,
        "justification": "python_checker_mirror_sufficiency_failed",
        "necessity": "open",
        "authorityStatus": AUTHORITY_STATUS,
        "notes": list(_AUTHORITY_NOTES)
        + [
            "Absence of a counterexample is not necessity.",
            "Use find_counterexample + verify_counterexample for weaker variants.",
        ],
    }


def verify_counterexample_python(
    request: dict[str, Any], certificate: dict[str, Any]
) -> dict[str, Any]:
    """Verify finite CEX via Lean Counterexample.checkBool mirror."""
    ok = check_finite_counterexample(request, certificate)
    return {
        "verified": ok,
        "outcome": "mirror_accepted" if ok else "rejected",
        "authorityStatus": AUTHORITY_STATUS,
        "notes": [
            "Python mirror of Lean Counterexample.checkBool.",
            "Lean kernel replay remains authoritative for certified refutation.",
        ],
    }


def minimality_allowed(
    *,
    certified_condition_ids: list[str],
    necessity_proofs: list[dict[str, Any]],
) -> bool:
    """Minimality requires certified sufficiency plus necessity coverage for each id."""
    if not certified_condition_ids:
        return False
    covered = {
        p.get("conditionId")
        for p in necessity_proofs
        if p.get("kind") in ("certified_counterexample", "necessity_theorem")
        and p.get("conditionId")
    }
    return all(cid in covered for cid in certified_condition_ids)


def certify_sufficient_set(
    lattice: dict[str, Any],
    condition_ids: list[str],
    *,
    certification_record_dir: Path | str,
    candidate_dir: Path | str | None = None,
    theorem_declaration: str | None = None,
    assumptions: list[str] | None = None,
    reviewer_status: str = "accepted",
) -> dict[str, Any]:
    """Promote a sufficient set into ``sufficientSetsCertified`` after kernel cert."""
    from agent.api.receipt import verify_certification_record

    record_path = Path(certification_record_dir)
    cand_path = Path(candidate_dir) if candidate_dir is not None else None
    try:
        verification = verify_certification_record(record_path, candidate_dir=cand_path)
    except Exception as exc:  # noqa: BLE001 — incomplete records never certify
        raise ValueError(f"Certification Record not verified: {exc}") from exc
    if not verification.verified:
        raise ValueError(
            "Certification Record not verified; cannot enter sufficientSetsCertified"
        )
    out = copy.deepcopy(lattice)
    certified = list(out.get("sufficientSetsCertified") or [])
    cert_id = verification.certification_record_digest
    record = make_sufficient_set_record(
        condition_ids,
        preview_status="kernel_certified",
        candidate_bundle_id=verification.candidate_bundle_digest,
        certification_record_id=cert_id,
        theorem_declaration=theorem_declaration or SUFFICIENCY_THEOREM_DECL,
        assumptions=assumptions,
        reviewer_status=reviewer_status,
    )
    record["authorityStatus"] = AUTHORITY_LEAN_KERNEL
    record["claimEstablished"] = verification.claim_established
    certified.append(record)
    out["sufficientSetsCertified"] = certified
    out["authorityStatus"] = AUTHORITY_STATUS
    return out


def build_condition_lattice(
    *,
    artifact_id: str,
    request: dict[str, Any],
    original: list[dict[str, Any]] | None = None,
    proposed: list[dict[str, Any]] | None = None,
    poly_zero: bool | None = None,
    weaker_variant_request: dict[str, Any] | None = None,
    related_condition_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Propose → sufficiency (checkBool mirror) → deletion → optional mirror CEX.

    ``sufficientSets`` holds mirror-accepted previews.
    ``sufficientSetsCertified`` stays empty until ``certify_sufficient_set``.
    """
    del poly_zero
    original = original or []
    proposed = proposed or propose_conditions_from_request(request)
    all_conds = original + proposed
    preview = prove_sufficient_python(request, all_conds)
    sufficient_sets: list[list[str]] = []
    sufficient_set_records: list[dict[str, Any]] = []
    redundant: list[str] = []
    unresolved: list[str] = []
    weakened: list[list[str]] = []
    certified_cex: list[str] = []
    necessity_proofs: list[dict[str, Any]] = []
    working = copy.deepcopy(all_conds)

    if preview["outcome"] == "mirror_accepted":
        ids = [c["id"] for c in working]
        sufficient_sets.append(ids)
        sufficient_set_records.append(
            make_sufficient_set_record(
                ids,
                preview_status="mirror_accepted",
                theorem_declaration=SUFFICIENCY_THEOREM_DECL,
                assumptions=ids,
            )
        )
        for cond in list(working):
            deletion = delete_hypothesis_python(request, working, cond["id"])
            if deletion["result"] == "redundant":
                redundant.append(cond["id"])
                working = deletion["remaining"]
                for c in proposed:
                    if c["id"] == cond["id"]:
                        c["status"] = "redundant"
                necessity_proofs.append(
                    {
                        "conditionId": cond["id"],
                        "kind": "redundancy_proof",
                        "detail": "python_checker_mirror_sufficiency",
                    }
                )
            elif deletion["result"] == "not_redundant":
                unresolved.append(cond["id"])
                for c in proposed:
                    if c["id"] == cond["id"]:
                        c["status"] = "necessity_open"
        for c in proposed:
            if c["id"] in {w["id"] for w in working} and c["status"] == "proposed":
                c["status"] = "sufficient_member"
    else:
        unresolved = [c["id"] for c in proposed]

    if weaker_variant_request is not None:
        wreq = bind_request_digest(dict(weaker_variant_request))
        cert = find_counterexample(wreq)
        if cert is not None and check_finite_counterexample(wreq, cert):
            cex_id = "cex_weaker_variant"
            certified_cex.append(cex_id)
            related = related_condition_ids or list(unresolved)
            weakened.append(related)
            for rid in related:
                if rid in unresolved:
                    unresolved = [u for u in unresolved if u != rid]
                for c in proposed:
                    if c["id"] == rid:
                        c["status"] = "weaker_falsified"
                necessity_proofs.append(
                    {
                        "conditionId": rid,
                        "kind": "certified_counterexample",
                        "detail": cex_id,
                    }
                )

    claims_minimal = False
    recommended = (
        [c["id"] for c in working] if preview["outcome"] == "mirror_accepted" else []
    )
    if claims_minimal and not minimality_allowed(
        certified_condition_ids=recommended, necessity_proofs=necessity_proofs
    ):
        raise ValueError("minimality refused: incomplete necessity coverage")

    lattice = {
        "schemaVersion": "0.1.0",
        "artifactId": artifact_id,
        "originalAssumptions": original,
        "proposed": proposed,
        "sufficientSets": sufficient_sets,
        "sufficientSetRecords": sufficient_set_records,
        "sufficientSetsCertified": [],
        "redundant": redundant,
        "weakenedVariants": weakened,
        "certifiedCounterexamples": certified_cex,
        "unresolvedNecessity": unresolved,
        "necessityProofs": necessity_proofs,
        "recommendedInterface": recommended,
        "ranking": {
            "criteria": [
                "logical generality",
                "assumption count",
                "library conventions",
                "human readability",
            ],
            "recommendedInterfaceId": (
                "recommended_v0" if preview["outcome"] == "mirror_accepted" else "none"
            ),
            "notes": "Minimality is not claimed. Expert review required before upstreaming.",
        },
        "claimsMinimal": False,
        "authorityStatus": AUTHORITY_STATUS,
        "sufficiencyPreview": {
            "outcome": preview["outcome"],
            "mirrorSufficient": preview["mirrorSufficient"],
            "evidence": preview["evidence"],
        },
    }
    store = SchemaStore()
    store.validate("condition-lattice.schema.json", lattice)
    return lattice

