"""Conjecture / falsification orchestration (Product 04) — Agent-side.

Wave 6 / ME-RV-061 (+ Wave 4 / ME-RV-042): Python mirror acceptance sets
``refutationPreview = mirror_accepted`` and leaves the episode in
``candidate_statement``. Only a verified Certification Record may set
``state = falsified``. ``mark_formally_proved`` is keyword-only and requires
theorem identity evidence plus a Certification Record (or validated source-proof
record) — a bare theorem reference string is rejected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.common.hypothesis_util import find_counterexample
from adapters.common.lean_mirrors import check_finite_counterexample

from agent.conjecture.finite_graph import (  # noqa: F401
    GENERATOR_VERSION as FINITE_GRAPH_GENERATOR_VERSION,
    calibrated_candidates,
    load_atlas,
    run_falsification_batch,
)
from agent.epistemic_states import AUTHORITY_LEAN_KERNEL, AUTHORITY_PYTHON_MIRROR

__all__ = [
    "STATES",
    "MIRROR_STATUS",
    "AUTHORITY_STATUS",
    "FINITE_GRAPH_GENERATOR_VERSION",
    "calibrated_candidates",
    "certify_refutation",
    "certify_refutation_from_record",
    "find_counterexample",
    "load_atlas",
    "mark_bounded_verified",
    "mark_formally_proved",
    "mark_open_problem",
    "new_episode",
    "precision_accounting",
    "preview_refutation",
    "run_family_campaign",
    "run_falsification_batch",
    "to_candidate",
]

STATES = (
    "observed_pattern",
    "candidate_statement",
    "falsified",
    "bounded_verified",
    "formally_proved",
    "open",
)

MIRROR_STATUS = "mirror_accepted"
AUTHORITY_STATUS = AUTHORITY_PYTHON_MIRROR
CERTIFIED_STATUS = AUTHORITY_LEAN_KERNEL


def new_episode(
    *, family_id: str, pred: dict[str, Any], state: str = "observed_pattern"
) -> dict[str, Any]:
    if state not in STATES:
        raise ValueError(f"unknown conjecture state: {state}")
    return {
        "familyId": family_id,
        "candidatePred": pred,
        "state": state,
        "certifiedRefutationId": None,
        "refutationPreview": None,
        "witnessStatus": None,
        "searchBound": 0,
        "notes": (
            "Pattern/candidate only; not a theorem."
            if state != "formally_proved"
            else "Formally proved requires Certification Record or validated declaration."
        ),
    }


def to_candidate(episode: dict[str, Any]) -> dict[str, Any]:
    out = dict(episode)
    out["state"] = "candidate_statement"
    return out


def preview_refutation(
    episode: dict[str, Any],
    *,
    request: dict[str, Any],
    certificate: dict[str, Any],
    refutation_id: str | None = None,
) -> dict[str, Any]:
    """Mirror-only refutation preview — never sets ``falsified``."""
    out = dict(episode)
    if check_finite_counterexample(request, certificate):
        out["state"] = "candidate_statement"
        out["refutationPreview"] = MIRROR_STATUS
        out["witnessStatus"] = "candidate_witness"
        out["authorityStatus"] = AUTHORITY_STATUS
        if refutation_id is not None:
            out["mirrorRefutationId"] = refutation_id
        out["notes"] = (
            "Mirror accepted finite counterexample; Certification Record required "
            "to set falsified."
        )
    else:
        out["refutationPreview"] = "rejected"
        out["witnessStatus"] = "mirror_rejected"
        out["notes"] = "Witness rejected; conjecture state unchanged."
        out["authorityStatus"] = AUTHORITY_STATUS
    return out


def certify_refutation_from_record(
    episode: dict[str, Any],
    *,
    certification_record_dir: Path | str,
    refutation_id: str,
    candidate_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Promote to ``falsified`` only after a verified Certification Record."""
    from agent.api.receipt import verify_certification_record

    out = dict(episode)
    try:
        verification = verify_certification_record(
            Path(certification_record_dir),
            candidate_dir=Path(candidate_dir) if candidate_dir is not None else None,
        )
    except Exception as exc:  # noqa: BLE001 — forged records must not falsify
        out["notes"] = (
            f"Certification Record verification failed ({exc}); falsified not set. "
            + str(out.get("notes") or "")
        )
        out["authorityStatus"] = out.get("authorityStatus") or AUTHORITY_STATUS
        return out
    if not verification.verified:
        out["notes"] = (
            "Certification Record failed verification; falsified not set. "
            + str(out.get("notes") or "")
        )
        out["authorityStatus"] = out.get("authorityStatus") or AUTHORITY_STATUS
        return out
    out["state"] = "falsified"
    out["certifiedRefutationId"] = (
        verification.certification_record_digest or refutation_id
    )
    out["certificationRecordDigest"] = verification.certification_record_digest
    out["authorityStatus"] = CERTIFIED_STATUS
    out["witnessStatus"] = "certified_witness"
    out["notes"] = (
        "Falsified by verified Certification Record "
        f"({out['certifiedRefutationId']})."
    )
    return out


def certify_refutation(
    episode: dict[str, Any],
    *,
    request: dict[str, Any],
    certificate: dict[str, Any],
    refutation_id: str,
    certification_record_dir: Path | str | None = None,
    candidate_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Certify a refutation.

    Without a Certification Record directory, only sets ``refutationPreview``
    (mirror path). With a verified Certification Record, sets ``falsified``.
    """
    out = preview_refutation(
        episode,
        request=request,
        certificate=certificate,
        refutation_id=refutation_id,
    )
    if out.get("refutationPreview") != MIRROR_STATUS:
        return out
    if certification_record_dir is None:
        out["certifiedRefutationId"] = None
        return out
    return certify_refutation_from_record(
        out,
        certification_record_dir=certification_record_dir,
        refutation_id=refutation_id,
        candidate_dir=candidate_dir,
    )


def mark_bounded_verified(episode: dict[str, Any], bound: int) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") in ("falsified", "formally_proved"):
        return out
    out["state"] = "bounded_verified"
    out["searchBound"] = bound
    out["notes"] = "Bounded verification only; not a theorem over the unbounded family."
    return out


def mark_formally_proved(
    episode: dict[str, Any],
    *,
    theorem_declaration: str,
    theorem_type_digest: str,
    environment_lock_digest: str,
    conjecture_type_digest: str | None = None,
    certification_record_dir: Path | str | None = None,
    candidate_dir: Path | str | None = None,
    source_proof_record: dict[str, Any] | None = None,
    axiom_policy_ok: bool = False,
) -> dict[str, Any]:
    """Mark formally proved only with validated theorem + certification evidence.

    A bare theorem reference string is insufficient (ME-RV-061). Keyword-only
    signature intentionally rejects ``mark_formally_proved(ep, \"thm\")``.
    """
    out = dict(episode)
    if out.get("state") == "falsified":
        return out

    if not isinstance(theorem_declaration, str) or not theorem_declaration.strip():
        raise ValueError("theorem_declaration required")
    if not isinstance(theorem_type_digest, str) or not theorem_type_digest.startswith(
        "sha256:"
    ):
        raise ValueError("theorem_type_digest must be a sha256 digest")
    if not isinstance(environment_lock_digest, str) or not environment_lock_digest.startswith(
        "sha256:"
    ):
        raise ValueError("environment_lock_digest must be a sha256 digest")
    if not axiom_policy_ok:
        raise ValueError("axiom_policy_ok must be true")

    if conjecture_type_digest is not None:
        if conjecture_type_digest != theorem_type_digest:
            raise ValueError("theorem type digest does not match conjecture")

    cert_id: str | None = None
    if certification_record_dir is not None:
        from agent.api.receipt import verify_certification_record

        record_path = Path(certification_record_dir)
        cand_path = Path(candidate_dir) if candidate_dir is not None else None
        try:
            verification = verify_certification_record(record_path, candidate_dir=cand_path)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Certification Record not verified: {exc}") from exc
        if not verification.verified:
            raise ValueError("Certification Record not verified")
        if verification.theorem_type_digest != theorem_type_digest:
            raise ValueError("theorem_type_digest mismatch vs Certification Record")
        if verification.environment_lock_digest != environment_lock_digest:
            raise ValueError("environment_lock_digest mismatch vs Certification Record")
        cert_id = verification.certification_record_digest
    elif isinstance(source_proof_record, dict):
        required = ("theoremDeclaration", "theoremTypeDigest", "environmentLockDigest")
        for key in required:
            if not source_proof_record.get(key):
                raise ValueError(f"source_proof_record missing {key}")
        if source_proof_record["theoremTypeDigest"] != theorem_type_digest:
            raise ValueError("source_proof_record theorem type mismatch")
        if source_proof_record.get("validated") is not True:
            raise ValueError("source_proof_record.validated must be true")
        cert_id = str(
            source_proof_record.get("proofRecordId")
            or source_proof_record.get("id")
            or "source_proof"
        )
    else:
        raise ValueError(
            "formally_proved requires Certification Record or validated source_proof_record"
        )

    out["state"] = "formally_proved"
    out["theoremDeclaration"] = theorem_declaration
    out["theoremTypeDigest"] = theorem_type_digest
    out["environmentLockDigest"] = environment_lock_digest
    out["certifiedProofId"] = cert_id
    out["authorityStatus"] = CERTIFIED_STATUS
    out["notes"] = f"Reusable theorem: {theorem_declaration} (certified={cert_id})"
    return out


def mark_open_problem(episode: dict[str, Any], detail: str) -> dict[str, Any]:
    out = dict(episode)
    if out.get("state") in ("falsified", "formally_proved"):
        return out
    out["state"] = "open"
    out["notes"] = detail
    return out


def precision_accounting(episodes: list[dict[str, Any]], *, family_id: str) -> dict[str, Any]:
    """Campaign accounting — ``refutationRate`` replaces ``precisionRate``."""
    counts: dict[str, Any] = {
        "familyId": family_id,
        "proposed": len(episodes),
        "falsified": 0,
        "boundedVerified": 0,
        "formallyProved": 0,
        "openProblems": 0,
        "mirrorAcceptedPreview": 0,
        "mirrorAccepted": 0,
        "candidateStatements": 0,
    }
    for e in episodes:
        st = e.get("state")
        if st == "falsified":
            counts["falsified"] += 1
        elif st == "bounded_verified":
            counts["boundedVerified"] += 1
        elif st == "formally_proved":
            counts["formallyProved"] += 1
        elif st == "open":
            counts["openProblems"] += 1
        elif st == "candidate_statement":
            counts["candidateStatements"] += 1
        if e.get("refutationPreview") == MIRROR_STATUS or (
            e.get("authorityStatus") in (MIRROR_STATUS, AUTHORITY_STATUS)
            and e.get("witnessStatus") == "candidate_witness"
        ):
            counts["mirrorAcceptedPreview"] += 1
            counts["mirrorAccepted"] += 1
    proposed = counts["proposed"] or 0

    def _rate(n: int) -> float | None:
        return (n / proposed) if proposed else None

    counts["refutationRate"] = _rate(counts["falsified"])
    counts["candidateValidityRate"] = _rate(
        counts["falsified"]
        + counts["formallyProved"]
        + counts["openProblems"]
        + counts["boundedVerified"]
        + counts["candidateStatements"]
    )
    counts["theoremConversionRate"] = _rate(counts["formallyProved"])
    counts["openRate"] = _rate(counts["openProblems"])
    counts["boundedOnlyRate"] = _rate(counts["boundedVerified"])
    counts["falsePositiveRate"] = None
    counts["notes"] = [
        "refutationRate = falsified/proposed (kernel-certified refutations only).",
        "mirror_accepted preview does not count as falsified.",
        "bounded_verified and open are not unbounded theorems.",
        "formally_proved requires Certification Record or validated source proof.",
        "falsePositiveRate requires expert review (unset until then).",
    ]
    return counts


def run_family_campaign(
    *,
    family_id: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run one formal family campaign with refutation-rate accounting.

    Each candidate is
    ``{pred, request?, certificate?, outcome?, theoremDeclaration?, ...}``.
    When ``request`` is provided, attempts mirror preview first. ``falsified`` /
    ``formally_proved`` require Certification Record paths (or validated source
    proof fields for the latter).
    """
    episodes: list[dict[str, Any]] = []
    for i, cand in enumerate(candidates):
        pred = cand["pred"]
        ep = to_candidate(new_episode(family_id=family_id, pred=pred))
        req = cand.get("request")
        cert = cand.get("certificate")
        if isinstance(req, dict):
            if cert is None:
                cert = find_counterexample(req)
            if cert is not None:
                ep = certify_refutation(
                    ep,
                    request=req,
                    certificate=cert,
                    refutation_id=cand.get("refutationId") or f"cex_{i}",
                    certification_record_dir=cand.get("certificationRecordDir")
                    or cand.get("certification_record_dir"),
                    candidate_dir=cand.get("candidateDir"),
                )
        if ep.get("state") != "falsified":
            outcome = cand.get("outcome")
            if outcome == "formally_proved":
                try:
                    ep = mark_formally_proved(
                        ep,
                        theorem_declaration=str(
                            cand.get("theoremDeclaration")
                            or cand.get("theoremRef")
                            or ""
                        ),
                        theorem_type_digest=str(cand.get("theoremTypeDigest") or ""),
                        environment_lock_digest=str(
                            cand.get("environmentLockDigest") or ""
                        ),
                        conjecture_type_digest=cand.get("conjectureTypeDigest"),
                        certification_record_dir=cand.get("certificationRecordDir")
                        or cand.get("certification_record_dir"),
                        candidate_dir=cand.get("candidateDir"),
                        source_proof_record=cand.get("sourceProofRecord"),
                        axiom_policy_ok=bool(cand.get("axiomPolicyOk")),
                    )
                except (TypeError, ValueError) as exc:
                    ep = mark_open_problem(
                        ep,
                        f"formally_proved refused: {exc}",
                    )
            elif outcome == "open":
                ep = mark_open_problem(
                    mark_bounded_verified(ep, int(cand.get("searchBound") or 0)),
                    str(cand.get("openDetail") or "Explicit open-problem artifact."),
                )
            elif outcome == "bounded_verified" or (
                isinstance(req, dict) and cert is None
            ):
                ep = mark_bounded_verified(ep, int(cand.get("searchBound") or 0))
        episodes.append(ep)
    accounting = precision_accounting(episodes, family_id=family_id)
    return {
        "familyId": family_id,
        "episodes": episodes,
        "precisionAccounting": accounting,
        "authorityStatus": AUTHORITY_STATUS,
    }

