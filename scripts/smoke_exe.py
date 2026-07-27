#!/usr/bin/env python3
"""Smoke positive/negative fixtures for verify-bundle (and kernel-replay when built).

ME-RV-073: ``just check`` must exercise executables against fixtures.
When Lake has not built the exe, exit 0 with an explicit skip (local Mathlib
blockers) but print the gap — CI Lean jobs build the exe first.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.replay import (  # noqa: E402
    THEOREM_LEVEL_STATUSES,
    find_replay_exe,
    run_lean_replay,
)

POSITIVE = ROOT / "evidence" / "examples" / "rational_equality_basic"
NEGATIVE_MARKER = "goal_mismatch"


def _require_or_skip(exe: Path | None, name: str) -> int | None:
    if exe is not None:
        return None
    force = os.environ.get("MATHEVIDENCE_REQUIRE_EXE_SMOKE", "").strip().lower()
    msg = f"smoke_exe: SKIP {name} not built (run lake build {name})"
    if force in {"1", "true", "yes"}:
        print(msg.replace("SKIP", "FAIL"), file=sys.stderr)
        return 1
    print(msg)
    return 0


def smoke_verify_bundle() -> int:
    exe = find_replay_exe(ROOT)
    skip = _require_or_skip(exe, "mathevidence-verify-bundle")
    if skip is not None:
        return skip

    import tempfile

    with tempfile.TemporaryDirectory(prefix="me-exe-smoke-") as tmp:
        dest = Path(tmp) / "positive"
        shutil.copytree(POSITIVE, dest)
        for name in ("checker-receipt.cjson", "checker-receipt.json"):
            p = dest / name
            if p.is_file():
                p.unlink()
        out = run_lean_replay(
            bundle_dir=dest,
            repo_root=ROOT,
            require_exe=True,
            goal_file=dest / "request.cjson",
        )
        if not out.get("ok"):
            print(f"FAIL positive: {out.get('stderr')}", file=sys.stderr)
            return 1
        if out.get("resultStatus") in THEOREM_LEVEL_STATUSES:
            print("FAIL positive emitted theorem-level status", file=sys.stderr)
            return 1
        if out.get("assuranceMode") != "native_checked":
            print(f"FAIL unexpected assuranceMode={out.get('assuranceMode')}", file=sys.stderr)
            return 1
        print("smoke_exe positive: ok (checker_accepted / native_checked)")

        # Negative: mismatched goal digest → hard fail
        bad = Path(tmp) / "negative"
        shutil.copytree(POSITIVE, bad)
        bad_goal = Path(tmp) / "bad_goal.json"
        bad_goal.write_text(
            json.dumps(
                {
                    "schemaVersion": "0.1.0",
                    "capability": "algebra.rational_equality",
                    "capabilityVersion": "0.1.0",
                    "variables": [{"name": "x", "type": "Rat"}],
                    "lhs": {"tag": "var", "name": "x"},
                    "rhs": {"tag": "int", "value": "0"},
                    "knownAssumptions": [],
                    "requestedClaim": "soundResult",
                    "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
                    "requestDigest": "sha256:" + "0" * 64,
                }
            ),
            encoding="utf-8",
        )
        neg = run_lean_replay(
            bundle_dir=bad,
            repo_root=ROOT,
            require_exe=True,
            goal_file=bad_goal,
        )
        if neg.get("ok"):
            print(f"FAIL negative ({NEGATIVE_MARKER}): expected rejection", file=sys.stderr)
            return 1
        print("smoke_exe negative: ok (goal mismatch rejected)")
    return 0


def _run_kernel_replay_self_tests(exe: Path) -> int:
    """Rational + analytic fixture self-tests (Linux CI + Windows when linked)."""
    import subprocess

    for flag, label in (
        ("--self-test", "rational"),
        ("--self-test-analytic", "analytic"),
    ):
        proc = subprocess.run(
            [str(exe), flag],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=False,
            shell=False,
        )
        if proc.returncode != 0:
            print(
                f"FAIL kernel-replay {flag}: {proc.stderr}",
                file=sys.stderr,
            )
            return 1
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        except json.JSONDecodeError:
            print(
                f"FAIL kernel-replay {flag} stdout not JSON: {proc.stdout[:500]}",
                file=sys.stderr,
            )
            return 1
        if payload.get("resultStatus") != "soundness_verified":
            print(
                f"FAIL {label} resultStatus={payload.get('resultStatus')}",
                file=sys.stderr,
            )
            return 1
        if payload.get("assuranceMode") != "kernel_replay":
            print(
                f"FAIL {label} assuranceMode={payload.get('assuranceMode')}",
                file=sys.stderr,
            )
            return 1
        print(f"smoke_exe kernel-replay {flag}: ok (soundness_verified)")
    return 0


def smoke_kernel_replay_presence() -> int:
    """Kernel replay (ME-RV-022): exe preferred; olean proves theorem compiled.

    On Windows Lean 4.14, Lake may fail ``leanc`` with CreateProcess error 206
    (command line too long). ``scripts/link_exe_via_rsp.py`` is the **required**
    Windows local path; always attempt it before degrading to olean-only.
    Never fake Certified. Linux CI requires the linked exe
    (``MATHEVIDENCE_REQUIRE_EXE_SMOKE=1``) and remains authoritative.
    """
    candidates = [
        ROOT / ".lake" / "build" / "bin" / "mathevidence-kernel-replay.exe",
        ROOT / ".lake" / "build" / "bin" / "mathevidence-kernel-replay",
    ]
    found = next((p for p in candidates if p.is_file()), None)
    olean = ROOT / ".lake" / "build" / "lib" / "MathEvidence" / "Exe" / "KernelReplay.olean"
    force = os.environ.get("MATHEVIDENCE_REQUIRE_EXE_SMOKE", "").strip().lower()

    if found is None and os.name == "nt":
        # Required Windows path: response-file link (Lean 4.14 Lake lacks @rsp).
        import subprocess

        link_script = ROOT / "scripts" / "link_exe_via_rsp.py"
        if link_script.is_file():
            print(
                "smoke_exe: attempting required Windows rsp link "
                "for mathevidence-kernel-replay"
            )
            proc = subprocess.run(
                [sys.executable, str(link_script), "mathevidence-kernel-replay"],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                check=False,
                shell=False,
            )
            if proc.stdout:
                print(proc.stdout.rstrip())
            if proc.returncode == 0:
                found = next((p for p in candidates if p.is_file()), None)
            else:
                print(
                    "smoke_exe: replay_dependency_missing — Windows platform link "
                    "unavailable after required rsp attempt "
                    "(Linux CI remains authoritative; no Certified claim)",
                    file=sys.stderr,
                )
                if proc.stderr and proc.returncode != 2:
                    print(proc.stderr.rstrip(), file=sys.stderr)
        else:
            print(
                "smoke_exe: replay_dependency_missing — "
                "scripts/link_exe_via_rsp.py missing "
                "(required Windows path; Linux CI remains authoritative)",
                file=sys.stderr,
            )

    if found is not None:
        print(f"smoke_exe: kernel-replay present at {found.name}")
        return _run_kernel_replay_self_tests(found)

    if olean.is_file():
        msg = (
            "smoke_exe: kernel-replay exe not linked, but KernelReplay.olean present "
            "(theorem compiled; error code: replay_dependency_missing / "
            "assurance_mode_unavailable for exe path; Linux CI attests linked exe)"
        )
        if force in {"1", "true", "yes"}:
            print(msg.replace("smoke_exe:", "FAIL"), file=sys.stderr)
            return 1
        print(msg)
        return 0

    msg = (
        "smoke_exe: kernel-replay not built "
        "(run lake build mathevidence-kernel-replay)"
    )
    if force in {"1", "true", "yes"}:
        print(msg.replace("not built", "FAIL not built"), file=sys.stderr)
        return 1
    print(f"smoke_exe: SKIP {msg}")
    return 0


def main() -> int:
    rc = smoke_verify_bundle()
    if rc != 0:
        return rc
    return smoke_kernel_replay_presence()


if __name__ == "__main__":
    raise SystemExit(main())
