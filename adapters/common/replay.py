"""Invoke Lean `mathevidence-replay` — Lean is theorem authority.

Python packaging validation is preview/`tested` only. When the Lake exe emits a
checker receipt with ``claimEstablished``, that value is preserved for Agent
trust wiring (never invented by Python).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from adapters.common.bundle import verify_bundle_offline


class ReplayError(RuntimeError):
    """Lean replay executable failed or is unavailable."""


def find_replay_exe(repo_root: Path | None = None) -> Path | None:
    root = repo_root or Path(__file__).resolve().parents[2]
    candidates = [
        root / ".lake" / "build" / "bin" / "mathevidence-replay.exe",
        root / ".lake" / "build" / "bin" / "mathevidence-replay",
    ]
    which = shutil.which("mathevidence-replay")
    if which:
        return Path(which)
    for path in candidates:
        if path.is_file():
            return path
    return None


def run_lean_replay(
    *,
    bundle_dir: Path | str,
    goal_file: str | Path | None = None,
    repo_root: Path | None = None,
    timeout_s: float = 120.0,
    require_exe: bool = False,
    bundle_id: str | None = None,
) -> dict[str, Any]:
    """Verify content digests on ``bundle_dir``, then run ``mathevidence-replay``.

    When Lean succeeds with a receipt containing ``claimEstablished``, that field
    is returned as Lean authority (Python must not invent verified claims).
    Missing exe → soft packaging-only ``tested`` with ``claimEstablished: null``.
    """
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    path = Path(bundle_dir)
    if not path.is_dir():
        raise ReplayError(f"bundle_not_found: {path}")

    warnings = verify_bundle_offline(path)
    exe = find_replay_exe(root)
    display_id = bundle_id or str(path)
    if exe is None:
        if require_exe:
            raise ReplayError(
                "mathevidence-replay not found; build with "
                "`lake build mathevidence-replay` first"
            )
        return {
            "exitCode": 0,
            "stdout": json.dumps(
                {
                    "schemaVersion": "0.2.0",
                    "resultStatus": "tested",
                    "contentDigestsVerified": True,
                    "claimEstablished": None,
                    "detail": "python offline digest verify; lean exe missing",
                    "bundlePath": str(path),
                    "bundleId": display_id,
                }
            ),
            "stderr": "mathevidence-replay exe missing; python offline verify only",
            "ok": True,
            "contentDigestsVerified": True,
            "claimEstablished": None,
            "leanExeMissing": True,
            "warnings": warnings,
            "bundlePath": str(path),
            "authority": "python_preview",
        }

    # Default goal binding: request role file (claim identity for offline replay).
    resolved_goal = goal_file
    if resolved_goal is None:
        for stem in ("request.cjson", "request.json"):
            candidate = path / stem
            if candidate.is_file():
                resolved_goal = candidate
                break

    cmd = [
        str(exe),
        "--bundle",
        str(path),
        "--store-root",
        str(root / "evidence" / "store"),
    ]
    if resolved_goal is not None:
        cmd.extend(["--goal-file", str(resolved_goal)])
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
        shell=False,
        cwd=str(root),
    )
    envelope: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
            if isinstance(parsed, dict):
                envelope = parsed
        except json.JSONDecodeError:
            envelope = {}

    claim = envelope.get("claimEstablished")
    if claim is not None and not isinstance(claim, str):
        claim = None
    # Lean authority only when exe succeeded and reported a string claim.
    lean_authority = proc.returncode == 0 and isinstance(claim, str) and bool(claim)

    return {
        "exitCode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
        "contentDigestsVerified": bool(
            envelope.get("contentDigestsVerified", proc.returncode == 0)
        ),
        "claimEstablished": claim if lean_authority else None,
        "resultStatus": envelope.get("resultStatus")
        if lean_authority
        else ("tested" if proc.returncode == 0 else "rejected"),
        "envelope": envelope,
        "warnings": warnings,
        "bundlePath": str(path),
        "leanExeMissing": False,
        "authority": "lean_exe" if lean_authority else "python_preview",
    }


# Backward-compatible alias used by older call sites that passed bundle_id as path.
def run_lean_replay_by_id(
    *,
    bundle_id: str,
    goal_file: str | Path | None = None,
    repo_root: Path | None = None,
    timeout_s: float = 120.0,
) -> dict[str, Any]:
    """Deprecated path: treat ``bundle_id`` as a filesystem path string."""
    return run_lean_replay(
        bundle_dir=bundle_id,
        goal_file=goal_file,
        repo_root=repo_root,
        timeout_s=timeout_s,
        bundle_id=bundle_id,
    )
