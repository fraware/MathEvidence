#!/usr/bin/env python3
"""Ideal-membership value benchmark (ME-RV-035 / P0 exact-binding repair).

Tiers
-----
``candidate``:
  pass iff backend proposes + arity decodes + the independently recomputed
  Python mirror of ``checkMembership`` accepts. Adapter self-reports are
  diagnostic only. This tier never reports theorem authority.

``release``:
  pass iff the candidate gates succeed and the *exact proposed witness* is
  embedded in an exact Candidate Bundle, compiled by Lean, inspected from
  ``Lean.Environment``, and emitted as a strict Certification Record with
  ``resultStatus=soundness_verified``.

``expectedMultipliers`` is oracle-only and never decides backend pass/fail.
External library-derived held-out remains a separate human/external gate.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_candidate_bundle  # noqa: E402
from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.ideal_membership import (  # noqa: E402
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    SCHEMA_VERSION,
    ArityError,
    check_membership_python,
    propose_membership_witness,
)
from adapters.common.kernel_replay import KernelReplayError, run_kernel_replay  # noqa: E402

SUITE = ROOT / "benchmarks" / "ideal_membership"

# Keep PR/nightly theorem compilation bounded while the exact path is new.
# These are task IDs, not OfflineFixtures: the backend's proposed multipliers
# are the certificate that Lean compiles and certifies. The complete frozen
# corpus is evaluated separately at candidate/checker tier.
RELEASE_CERTIFICATION_TASKS = frozenset(
    {
        "IM01_linear_combination_xy",
        "IM02_x2_minus_1",
    }
)

TIER_CANDIDATE = "candidate"
TIER_RELEASE = "release"


def _lake_available() -> bool:
    return shutil.which("lake") is not None and (ROOT / "lakefile.toml").is_file()


def _resolve_tier(cli_tier: str | None) -> str:
    if cli_tier:
        return cli_tier.strip().lower()
    env = os.environ.get("MATHEVIDENCE_IDEAL_BENCH_TIER", "").strip().lower()
    return env if env in {TIER_CANDIDATE, TIER_RELEASE} else TIER_CANDIDATE


def _candidate_status(task: dict[str, Any], proposed: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "leanCheckStatus": "python_mirror_accepted_pending_release_tier",
        "kernelReplayStatus": "not_attempted_candidate_tier",
        "assuranceClaim": "native_checked_candidate_only",
        "resultStatus": None,
        "note": (
            "Candidate tier accepted only by the independently recomputed Python checker mirror; "
            "no theorem-level status is claimed."
        ),
        "taskId": task.get("id"),
        "proposedMultiplierCount": len(proposed),
    }


def _build_temp_bundle(
    *,
    task: dict[str, Any],
    proposed: list[dict[str, Any]],
    backend: str,
    bundle_dir: Path,
) -> Path:
    request = bind_request_digest(
        {
            "schemaVersion": SCHEMA_VERSION,
            "capability": CAPABILITY_ID,
            "capabilityVersion": CAPABILITY_VERSION,
            "target": task["target"],
            "generators": task["generators"],
            "requestedClaim": "witness",
        }
    )
    certificate = {
        "schemaVersion": SCHEMA_VERSION,
        "capability": CAPABILITY_ID,
        "capabilityVersion": CAPABILITY_VERSION,
        "requestDigest": request["requestDigest"],
        "target": task["target"],
        "generators": task["generators"],
        "multipliers": proposed,
        "claimClass": "witness",
        "pythonMirrorAccepts": True,
        "provenance": {
            "adapterVersion": "0.1.0",
            "backendId": backend,
            "backendVersion": "benchmark",
            "deterministic": True,
            "generatedAt": "benchmark-run",
        },
    }
    candidate = {
        "reportedOk": True,
        "multipliers": proposed,
        "backend": backend,
    }
    write_candidate_bundle(
        bundle_dir,
        request=request,
        candidate=candidate,
        certificate=certificate,
        claim_class="candidate",
        assurance_mode="native_checked",
    )
    return bundle_dir


def _release_grade_cert(
    task: dict[str, Any], proposed: list[dict[str, Any]], *, backend: str
) -> dict[str, Any]:
    tid = str(task.get("id") or "")
    if tid not in RELEASE_CERTIFICATION_TASKS:
        return {
            "leanCheckStatus": "outside_bounded_release_subset",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
            "certificationRecordDigest": None,
            "note": "task is outside the bounded exact-replay release subset",
        }
    if not _lake_available():
        return {
            "leanCheckStatus": "lake_unavailable",
            "kernelReplayStatus": "failed",
            "assuranceClaim": None,
            "resultStatus": None,
            "certificationRecordDigest": None,
            "note": "release tier requires Lean/Lake",
            "error": "lake_missing",
        }

    with tempfile.TemporaryDirectory(prefix="me_ideal_release_") as tmp:
        bundle_dir = Path(tmp) / "bundle"
        _build_temp_bundle(
            task=task, proposed=proposed, backend=backend, bundle_dir=bundle_dir
        )
        try:
            out = run_kernel_replay(
                bundle_dir=bundle_dir,
                repo_root=ROOT,
                declaration_name=f"certified_{tid}",
                require_lean=True,
                out_record_dir=Path(tmp) / "certification",
            )
        except KernelReplayError as exc:
            return {
                "leanCheckStatus": "kernel_replay_rejected",
                "kernelReplayStatus": "failed",
                "assuranceClaim": None,
                "resultStatus": None,
                "certificationRecordDigest": None,
                "error": str(exc),
                "errorCode": getattr(exc, "code", None),
                "note": "exact kernel replay refused theorem-level status",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "leanCheckStatus": "kernel_replay_error",
                "kernelReplayStatus": "failed",
                "assuranceClaim": None,
                "resultStatus": None,
                "certificationRecordDigest": None,
                "error": str(exc),
                "note": "unexpected exact kernel replay failure",
            }

        ok = bool(out.get("ok")) and out.get("resultStatus") == "soundness_verified"
        return {
            "leanCheckStatus": "exact_candidate_kernel_replay" if ok else "kernel_replay_incomplete",
            "kernelReplayStatus": "ok" if ok else "failed",
            "assuranceClaim": "kernel_replay" if ok else None,
            "resultStatus": out.get("resultStatus") if ok else None,
            "certificationRecordDigest": out.get("certificationRecordDigest") if ok else None,
            "certificationId": out.get("certificationId") if ok else None,
            "declarationName": out.get("declarationName"),
            "theoremTypeDigest": out.get("theoremTypeDigest"),
            "proofDeclarationDigest": out.get("proofDeclarationDigest"),
            "identityAuthority": out.get("identityAuthority"),
            "leanOk": out.get("leanOk"),
            "note": (
                "Exact backend-proposed multipliers certified; theorem/proof identity read from Lean.Environment"
                if ok
                else "kernel replay did not establish soundness_verified"
            ),
        }


def _score_task(task: dict[str, Any], backend: str, *, tier: str) -> dict[str, Any]:
    target = task["target"]
    generators = task["generators"]
    expected = task.get("expectedMultipliers")
    expected_status = task.get("expectedStatus", "pass")
    stratum = task.get("stratum") or task.get("family") or "unit"

    oracle_ok = None
    if expected is not None:
        try:
            oracle_ok = check_membership_python(target, generators, expected)
        except ArityError:
            oracle_ok = False

    start = time.perf_counter()
    decode_ok = True
    decode_error = None
    try:
        proposal = propose_membership_witness(
            target=target, generators=generators, backend=backend
        )
    except ArityError as exc:
        decode_ok = False
        decode_error = str(exc)
        proposal = {
            "multipliers": [],
            "pythonMirrorAccepts": False,
            "backend": backend,
        }
    generation_ms = (time.perf_counter() - start) * 1000.0

    proposed = list(proposal.get("multipliers") or [])
    start = time.perf_counter()
    proposed_ok = False
    if decode_ok and proposed:
        try:
            proposed_ok = check_membership_python(target, generators, proposed)
        except ArityError as exc:
            decode_ok = False
            decode_error = str(exc)
    check_ms = (time.perf_counter() - start) * 1000.0

    adapter_reported_accepts = proposal.get("pythonMirrorAccepts")
    adapter_checker_agreement = (
        adapter_reported_accepts == proposed_ok
        if isinstance(adapter_reported_accepts, bool)
        else None
    )
    critical_false_accept = expected_status == "xfail" and proposed_ok

    if not proposed_ok:
        lean = {
            "leanCheckStatus": "not_attempted",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
        }
    elif tier == TIER_RELEASE:
        lean = _release_grade_cert(task, proposed, backend=backend)
    else:
        lean = _candidate_status(task, proposed)

    if expected_status == "skip":
        status = "skip"
    elif expected_status == "xfail":
        # A negative-corpus outcome is decided only by the independently
        # recomputed checker result. Adapter self-report is untrusted telemetry.
        status = "xfail_unexpected_accept" if critical_false_accept else "xfail_ok"
    elif not decode_ok:
        status = "fail_decode_arity"
    elif not proposed:
        status = "fail_no_proposal"
    elif not proposed_ok:
        status = "fail_proposed_rejected"
    elif tier == TIER_RELEASE:
        status = (
            "pass"
            if lean.get("resultStatus") == "soundness_verified"
            and lean.get("certificationRecordDigest")
            else "fail_certification_record"
        )
    else:
        if lean.get("resultStatus") in {"soundness_verified", "witness_verified"}:
            raise RuntimeError("candidate tier attempted theorem-level status")
        status = "pass"

    return {
        "id": task["id"],
        "status": status,
        "tier": tier,
        "stratum": stratum,
        "expectedStatus": expected_status,
        "claimClass": task.get("claimClass"),
        "oracleExpectedAccepts": oracle_ok,
        "oracleNote": "expectedMultipliers are fixture validation only; never pass/fail authority",
        "decodeOk": decode_ok,
        "decodeError": decode_error,
        "proposedAccepts": proposed_ok,
        "criticalFalseAccept": critical_false_accept,
        "adapterPythonMirrorAccepts": adapter_reported_accepts,
        "adapterCheckerAgreement": adapter_checker_agreement,
        "adapterBackend": proposal.get("backend"),
        "nativeWitnessMs": round(generation_ms, 3),
        "mathEvidenceCheckMs": round(check_ms, 3),
        "lean": lean,
        "asymmetryNote": "generation_gt_check" if generation_ms > max(check_ms, 1e-9) else "check_gte_generation",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", choices=[TIER_CANDIDATE, TIER_RELEASE], default=None)
    parser.add_argument(
        "--backend",
        default=None,
        help="proposal backend (default: MATHEVIDENCE_IDEAL_BACKEND or sympy)",
    )
    args = parser.parse_args(argv)
    tier = _resolve_tier(args.tier)
    backend = (args.backend or os.environ.get("MATHEVIDENCE_IDEAL_BACKEND", "sympy")).strip() or "sympy"

    manifest = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    task_rels = list(manifest["tasks"])
    if tier == TIER_RELEASE:
        task_rels = [
            rel
            for rel in task_rels
            if str(json.loads((SUITE / rel).read_text(encoding="utf-8")).get("id") or "")
            in RELEASE_CERTIFICATION_TASKS
        ]

    rows = [
        _score_task(
            json.loads((SUITE / rel).read_text(encoding="utf-8")),
            backend=backend,
            tier=tier,
        )
        for rel in task_rels
    ]
    scored = [row for row in rows if row["status"] != "skip"]
    passed = sum(row["status"] in {"pass", "xfail_ok"} for row in scored)
    soundness_claims = [
        row for row in rows if (row.get("lean") or {}).get("resultStatus") == "soundness_verified"
    ]
    if tier == TIER_CANDIDATE and soundness_claims:
        raise SystemExit("candidate tier produced soundness_verified; refusing report")

    critical_false_accept_tasks = [
        str(row["id"]) for row in rows if row.get("criticalFalseAccept") is True
    ]
    adapter_checker_disagreement_tasks = [
        str(row["id"]) for row in rows if row.get("adapterCheckerAgreement") is False
    ]

    by_stratum: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_stratum.setdefault(str(row.get("stratum") or "unit"), {"total": 0, "passed": 0})
        if row["status"] != "skip":
            bucket["total"] += 1
        if row["status"] in {"pass", "xfail_ok"}:
            bucket["passed"] += 1

    native_times = [row["nativeWitnessMs"] for row in rows]
    check_times = [row["mathEvidenceCheckMs"] for row in rows]
    out = {
        "suite": manifest["suite"],
        "capability": CAPABILITY_ID,
        "tier": tier,
        "scoringRule": (
            "pass iff propose + arity-decode + independently recomputed Python mirror check; adapter self-report is diagnostic only; never theorem authority"
            if tier == TIER_CANDIDATE
            else "pass iff backend proposal passes independently recomputed mirror and that exact proposal obtains Lean.Environment-derived kernel Certification Record"
        ),
        "backend": backend,
        "declaredBaselines": manifest.get("baselines") or [],
        "releaseCertificationTasks": sorted(RELEASE_CERTIFICATION_TASKS),
        "taskCount": len(rows),
        "scoredTasks": len(scored),
        "passed": passed,
        "skipped": sum(row["status"] == "skip" for row in rows),
        "criticalFalseAcceptCount": len(critical_false_accept_tasks),
        "criticalFalseAcceptTasks": critical_false_accept_tasks,
        "adapterCheckerDisagreementCount": len(adapter_checker_disagreement_tasks),
        "adapterCheckerDisagreementTasks": adapter_checker_disagreement_tasks,
        "byStratum": by_stratum,
        "honestyNote": manifest.get("honestyNote"),
        "externalHeldOutNote": (
            "ME-RV-081 external library-derived held-out remains BLOCKED(human); "
            "in-repo held_out tasks are synthetic."
        ),
        "lakeBlockedNote": (
            "Candidate tier never claims theorem authority. Release tier requires Lean/Lake "
            "and exact Candidate Bundle replay; no OfflineFixtures theorem substitution."
        ),
        "baselineSummary": {
            "nativeBackend": backend,
            "nativeWitnessTotalMs": round(sum(native_times), 3),
            "mathEvidenceCheckTotalMs": round(sum(check_times), 3),
            "nativeWitnessAvgMs": round(sum(native_times) / len(native_times), 3) if native_times else None,
            "mathEvidenceCheckAvgMs": round(sum(check_times) / len(check_times), 3) if check_times else None,
            "tasksWhereGenerationExceedsCheck": sum(
                row.get("asymmetryNote") == "generation_gt_check" for row in rows
            ),
            "valueGateStatus": manifest.get("valueGate"),
            "certificationRecords": len(soundness_claims),
        },
        "tasks": rows,
    }
    print(json.dumps(out, indent=2))
    return (
        0
        if scored
        and passed == len(scored)
        and not critical_false_accept_tasks
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
