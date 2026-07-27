#!/usr/bin/env python3
"""Ideal-membership value benchmark (ME-RV-035 / P0-F).

Tiers
-----
``candidate`` (default; smoke / ``just check`` / ``lean.yml``):
  pass iff backend proposes ∧ arity-decode ∧ Python mirror of ``checkMembership``.
  NEVER reports ``soundness_verified`` / Certification Record authority.

``release`` (nightly / ``benchmarks.yml``):
  pass iff candidate gates succeed AND Lean ``checkBool`` via OfflineFixtures
  kernel-replay driver produces a verified Certification Record
  (``resultStatus=soundness_verified``, ``assuranceMode=kernel_replay``).

``expectedMultipliers`` is oracle-only — never determines backend pass/fail.

External library-derived held-out (ME-RV-081) remains BLOCKED(human). In-repo
``held_out`` stratum tasks are synthetic and are not claimed as external provenance.
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
from adapters.common.kernel_replay import (  # noqa: E402
    KernelReplayError,
    run_kernel_replay,
)

SUITE = ROOT / "benchmarks" / "ideal_membership"

# Release-grade certifiable tasks → OfflineFixtures keys (ME-RV-035).
RELEASE_FIXTURE_TASKS: dict[str, str] = {
    "IM01_linear_combination_xy": "xy",
    "IM02_x2_minus_1": "x2m1",
}

TIER_CANDIDATE = "candidate"
TIER_RELEASE = "release"


def _lake_available() -> bool:
    return shutil.which("lake") is not None and (ROOT / "lakefile.toml").is_file()


def _resolve_tier(cli_tier: str | None) -> str:
    if cli_tier:
        return cli_tier.strip().lower()
    env = os.environ.get("MATHEVIDENCE_IDEAL_BENCH_TIER", "").strip().lower()
    if env in {TIER_CANDIDATE, TIER_RELEASE}:
        return env
    return TIER_CANDIDATE


def _lean_check_candidate_smoke(
    task: dict[str, Any], proposed: list[dict[str, Any]]
) -> dict[str, Any]:
    """Honest candidate-tier Lean/kernel status — never soundness_verified."""
    force = os.environ.get("MATHEVIDENCE_IDEAL_LEAN_CHECK", "").strip().lower()
    if force in {"0", "false", "skip"}:
        return {
            "leanCheckStatus": "skipped_by_env",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
            "note": "MATHEVIDENCE_IDEAL_LEAN_CHECK disabled",
        }
    if not _lake_available():
        return {
            "leanCheckStatus": "smoke_unavailable",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
            "note": "lake not available; candidate tier does not require Lean",
        }
    return {
        "leanCheckStatus": "python_mirror_accepted_pending_release_tier",
        "kernelReplayStatus": "not_attempted_candidate_tier",
        "assuranceClaim": "native_checked_candidate_only",
        "resultStatus": None,
        "note": (
            "Proposed witness accepted by Python mirror of checkMembership; "
            "candidate tier MUST NOT claim soundness_verified. "
            "Use --tier release for Certification Record scoring."
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
    """Write a Candidate Bundle v0.3 for kernel replay (digest-bound request)."""
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
    task: dict[str, Any],
    proposed: list[dict[str, Any]],
    *,
    backend: str,
) -> dict[str, Any]:
    """Lean checkBool + kernel_replay Certification Record (release tier)."""
    tid = str(task.get("id") or "")
    fixture = RELEASE_FIXTURE_TASKS.get(tid)
    if fixture is None:
        return {
            "leanCheckStatus": "no_offline_fixture",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
            "certificationRecordDigest": None,
            "note": (
                f"task {tid} has no Ideal OfflineFixtures mapping; "
                "release-grade suite is the fixture-backed subset only"
            ),
            "fixture": None,
        }
    if not _lake_available():
        return {
            "leanCheckStatus": "lake_unavailable",
            "kernelReplayStatus": "failed",
            "assuranceClaim": None,
            "resultStatus": None,
            "certificationRecordDigest": None,
            "note": "release tier requires lake for kernel replay",
            "fixture": fixture,
            "error": "lake_missing",
        }

    with tempfile.TemporaryDirectory(prefix="me_ideal_release_") as tmp:
        bundle_dir = Path(tmp) / "bundle"
        _build_temp_bundle(
            task=task, proposed=proposed, backend=backend, bundle_dir=bundle_dir
        )
        record_dir = Path(tmp) / "cert"
        try:
            out = run_kernel_replay(
                bundle_dir=bundle_dir,
                repo_root=ROOT,
                require_lean=True,
                out_record_dir=record_dir,
            )
        except KernelReplayError as exc:
            return {
                "leanCheckStatus": "kernel_replay_rejected",
                "kernelReplayStatus": "failed",
                "assuranceClaim": None,
                "resultStatus": None,
                "certificationRecordDigest": None,
                "fixture": fixture,
                "error": str(exc),
                "errorCode": getattr(exc, "code", None),
                "note": "kernel replay refused soundness_verified",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "leanCheckStatus": "kernel_replay_error",
                "kernelReplayStatus": "failed",
                "assuranceClaim": None,
                "resultStatus": None,
                "certificationRecordDigest": None,
                "fixture": fixture,
                "error": str(exc),
                "note": "unexpected kernel replay failure",
            }

        ok = bool(out.get("ok")) and out.get("resultStatus") == "soundness_verified"
        return {
            "leanCheckStatus": "checkBool_via_offline_fixtures"
            if ok
            else "kernel_replay_incomplete",
            "kernelReplayStatus": "ok" if ok else "failed",
            "assuranceClaim": "kernel_replay" if ok else None,
            "resultStatus": out.get("resultStatus") if ok else None,
            "certificationRecordDigest": out.get("certificationRecordDigest")
            if ok
            else None,
            "certificationId": out.get("certificationId") if ok else None,
            "declarationName": out.get("declarationName"),
            "fixture": fixture,
            "leanOk": out.get("leanOk"),
            "note": (
                "Certification Record emitted via OfflineFixtures + replaySound"
                if ok
                else "kernel replay did not establish soundness_verified"
            ),
        }


def _score_task(task: dict[str, Any], backend: str, *, tier: str) -> dict[str, Any]:
    target = task["target"]
    gens = task["generators"]
    expected = task.get("expectedMultipliers")
    expected_status = task.get("expectedStatus", "pass")
    stratum = task.get("stratum") or task.get("family") or "unit"
    tid = str(task.get("id") or "")

    oracle_ok = None
    if expected is not None:
        try:
            oracle_ok = check_membership_python(target, gens, expected)
        except ArityError:
            oracle_ok = False

    native_start = time.perf_counter()
    decode_ok = True
    decode_error = None
    proposed_payload: dict[str, Any]
    try:
        proposed_payload = propose_membership_witness(
            target=target, generators=gens, backend=backend
        )
    except ArityError as exc:
        decode_ok = False
        decode_error = str(exc)
        proposed_payload = {
            "multipliers": [],
            "pythonMirrorAccepts": False,
            "backend": backend,
            "notes": [f"arity reject: {exc}"],
        }
    native_ms = (time.perf_counter() - native_start) * 1000.0

    proposed = list(proposed_payload.get("multipliers") or [])
    check_start = time.perf_counter()
    proposed_ok = False
    if decode_ok and proposed:
        try:
            proposed_ok = check_membership_python(target, gens, proposed)
        except ArityError as exc:
            decode_ok = False
            decode_error = str(exc)
            proposed_ok = False
    check_ms = (time.perf_counter() - check_start) * 1000.0

    lean_info: dict[str, Any]
    if not proposed_ok:
        lean_info = {
            "leanCheckStatus": "not_attempted",
            "kernelReplayStatus": "not_attempted",
            "assuranceClaim": None,
            "resultStatus": None,
        }
    elif tier == TIER_RELEASE:
        lean_info = _release_grade_cert(task, proposed, backend=backend)
    else:
        lean_info = _lean_check_candidate_smoke(task, proposed)

    # Candidate pass: propose ∧ decode ∧ mirror check.
    # Release pass: candidate gates + Certification Record (soundness_verified).
    if expected_status == "skip":
        status = "skip"
    elif expected_status == "xfail":
        status = (
            "xfail_ok"
            if not proposed_payload.get("pythonMirrorAccepts")
            else "xfail_unexpected_accept"
        )
    elif not decode_ok:
        status = "fail_decode_arity"
    elif not proposed:
        status = "fail_no_proposal"
    elif not proposed_ok:
        status = "fail_proposed_rejected"
    elif tier == TIER_RELEASE:
        if tid not in RELEASE_FIXTURE_TASKS:
            status = "fail_no_release_fixture"
        elif lean_info.get("resultStatus") == "soundness_verified" and lean_info.get(
            "certificationRecordDigest"
        ):
            status = "pass"
        else:
            status = "fail_certification_record"
    else:
        # Candidate: never mint soundness_verified even if lake is present.
        if lean_info.get("resultStatus") == "soundness_verified":
            lean_info = {
                **lean_info,
                "resultStatus": None,
                "assuranceClaim": "native_checked_candidate_only",
                "note": (
                    "candidate tier stripped soundness_verified; "
                    "use --tier release for Certification Record"
                ),
            }
        status = "pass"

    return {
        "id": task["id"],
        "status": status,
        "tier": tier,
        "stratum": stratum,
        "expectedStatus": expected_status,
        "claimClass": task.get("claimClass"),
        "oracleExpectedAccepts": oracle_ok,
        "oracleNote": (
            "expectedMultipliers used only for fixture validation; "
            "not used for pass/fail scoring"
        ),
        "decodeOk": decode_ok,
        "decodeError": decode_error,
        "proposedAccepts": proposed_ok,
        "adapterPythonMirrorAccepts": proposed_payload.get("pythonMirrorAccepts"),
        "adapterBackend": proposed_payload.get("backend"),
        "nativeWitnessMs": round(native_ms, 3),
        "mathEvidenceCheckMs": round(check_ms, 3),
        "lean": lean_info,
        "asymmetryNote": (
            "generation_gt_check" if native_ms > max(check_ms, 1e-9) else "check_gte_generation"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier",
        choices=[TIER_CANDIDATE, TIER_RELEASE],
        default=None,
        help=(
            "scoring tier (default: MATHEVIDENCE_IDEAL_BENCH_TIER or candidate). "
            "candidate never claims soundness_verified; release requires Certification Record"
        ),
    )
    parser.add_argument(
        "--backend",
        default=None,
        help="proposal backend (default: MATHEVIDENCE_IDEAL_BACKEND or sympy)",
    )
    args = parser.parse_args(argv)

    tier = _resolve_tier(args.tier)
    backend = (
        args.backend
        or os.environ.get("MATHEVIDENCE_IDEAL_BACKEND", "sympy")
    ).strip() or "sympy"

    manifest = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    baselines = manifest.get("baselines") or [
        "lean_reference_search",
        "sympy",
        "sage",
        "mathematica",
    ]

    task_rels = list(manifest["tasks"])
    if tier == TIER_RELEASE:
        # Release-grade scores the OfflineFixtures-backed subset only.
        release_rels = []
        for rel in task_rels:
            task = json.loads((SUITE / rel).read_text(encoding="utf-8"))
            if str(task.get("id") or "") in RELEASE_FIXTURE_TASKS:
                release_rels.append(rel)
        task_rels = release_rels

    rows = []
    for rel in task_rels:
        task = json.loads((SUITE / rel).read_text(encoding="utf-8"))
        rows.append(_score_task(task, backend=backend, tier=tier))

    scored = [r for r in rows if r["status"] not in {"skip"}]
    passed = sum(1 for r in scored if r["status"] in {"pass", "xfail_ok"})
    by_stratum: dict[str, dict[str, int]] = {}
    for r in rows:
        s = str(r.get("stratum") or "unit")
        bucket = by_stratum.setdefault(s, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r["status"] in {"pass", "xfail_ok"}:
            bucket["passed"] += 1
        elif r["status"] == "skip":
            bucket["total"] -= 1

    soundness_claims = [
        r
        for r in rows
        if (r.get("lean") or {}).get("resultStatus") == "soundness_verified"
    ]
    if tier == TIER_CANDIDATE and soundness_claims:
        raise SystemExit(
            "candidate tier produced soundness_verified; refusing dishonest report"
        )

    native_times = [r["nativeWitnessMs"] for r in rows]
    check_times = [r["mathEvidenceCheckMs"] for r in rows]
    scoring_rule = (
        "pass iff propose ∧ arity-decode ∧ checkMembership(proposed); "
        "never soundness_verified"
        if tier == TIER_CANDIDATE
        else (
            "pass iff propose ∧ arity-decode ∧ checkMembership(proposed) ∧ "
            "OfflineFixtures kernel_replay Certification Record "
            "(soundness_verified); fixture-backed subset only"
        )
    )
    out = {
        "suite": manifest["suite"],
        "capability": CAPABILITY_ID,
        "tier": tier,
        "scoringRule": scoring_rule,
        "backend": backend,
        "declaredBaselines": baselines,
        "releaseFixtureTasks": sorted(RELEASE_FIXTURE_TASKS),
        "taskCount": len(rows),
        "scoredTasks": len(scored),
        "passed": passed,
        "skipped": sum(1 for r in rows if r["status"] == "skip"),
        "byStratum": by_stratum,
        "honestyNote": manifest.get("honestyNote"),
        "externalHeldOutNote": (
            "ME-RV-081 external library-derived held-out remains BLOCKED(human). "
            "In-repo held_out stratum is synthetic and is not external provenance."
        ),
        "lakeBlockedNote": (
            "Candidate tier documents Lean smoke/stub without faking theorem authority. "
            "Release tier requires lake + OfflineFixtures + Certification Record."
        ),
        "baselineSummary": {
            "nativeBackend": backend,
            "nativeWitnessTotalMs": round(sum(native_times), 3),
            "mathEvidenceCheckTotalMs": round(sum(check_times), 3),
            "nativeWitnessAvgMs": round(sum(native_times) / len(native_times), 3)
            if native_times
            else None,
            "mathEvidenceCheckAvgMs": round(sum(check_times) / len(check_times), 3)
            if check_times
            else None,
            "tasksWhereGenerationExceedsCheck": sum(
                1 for r in rows if r.get("asymmetryNote") == "generation_gt_check"
            ),
            "valueGateStatus": manifest.get("valueGate"),
            "certificationRecords": len(soundness_claims),
        },
        "tasks": rows,
    }
    print(json.dumps(out, indent=2))
    return 0 if passed == len(scored) and len(scored) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
