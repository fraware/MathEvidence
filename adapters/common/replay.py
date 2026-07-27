"""Invoke Lean `mathevidence-verify-bundle` — operational checker only.

Wave 0–2: success means content digests + ``checkBool`` accepted
(``native_checked`` / ``checker_accepted``). This path MUST NOT be treated as
theorem authority, ``kernel_replay``, ``soundness_verified``, or Certified.

Theorem certification is ``adapters.common.kernel_replay.run_kernel_replay`` /
Agent ``kernel_replay`` + ``open_certification``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from adapters.common.bundle import verify_bundle_offline

# Theorem-level statuses that the Wave 0 verifier must never promote.
THEOREM_LEVEL_STATUSES = frozenset(
    {
        "witness_verified",
        "soundness_verified",
        "completeness_verified",
        "optimality_verified",
        "approximation_certified",
        "native_verified",
    }
)


class ReplayError(RuntimeError):
    """Lean verify-bundle executable failed or is unavailable."""


def find_replay_exe(repo_root: Path | None = None) -> Path | None:
    """Locate ``mathevidence-verify-bundle`` (preferred) or legacy alias."""
    root = repo_root or Path(__file__).resolve().parents[2]
    names = (
        "mathevidence-verify-bundle",
        "mathevidence-replay",  # temporary Wave 0 alias
    )
    candidates: list[Path] = []
    for name in names:
        candidates.append(root / ".lake" / "build" / "bin" / f"{name}.exe")
        candidates.append(root / ".lake" / "build" / "bin" / name)
        which = shutil.which(name)
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
    """Verify content digests on ``bundle_dir``, then run the operational verifier.

    On success, returns ``resultStatus=checker_accepted`` / ``assuranceMode=native_checked``
    when the Lean exe reports them. Never promotes ``claimEstablished`` or
    theorem-level statuses from this path (ME-RV-001).
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
                "mathevidence-verify-bundle not found; build with "
                "`lake build mathevidence-verify-bundle` first"
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
            "stderr": "mathevidence-verify-bundle exe missing; python offline verify only",
            "ok": True,
            "contentDigestsVerified": True,
            "claimEstablished": None,
            "leanExeMissing": True,
            "warnings": warnings,
            "bundlePath": str(path),
            "authority": "python_preview",
        }

    # Default goal binding: request role file (claim identity for offline verify).
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

    # Wave 0: operational path never establishes a theorem claim.
    raw_status = envelope.get("resultStatus")
    if isinstance(raw_status, str) and raw_status in THEOREM_LEVEL_STATUSES:
        raw_status = "checker_accepted"
    if proc.returncode == 0:
        result_status = (
            raw_status
            if isinstance(raw_status, str) and raw_status
            else "checker_accepted"
        )
        if result_status in THEOREM_LEVEL_STATUSES:
            result_status = "checker_accepted"
    else:
        result_status = "rejected"

    return {
        "exitCode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
        "contentDigestsVerified": bool(
            envelope.get("contentDigestsVerified", proc.returncode == 0)
        ),
        "claimEstablished": None,
        "resultStatus": result_status,
        "assuranceMode": envelope.get("assuranceMode", "native_checked")
        if proc.returncode == 0
        else None,
        "envelope": envelope,
        "warnings": warnings,
        "bundlePath": str(path),
        "leanExeMissing": False,
        # Operational Lean checker only — not theorem / Certified authority.
        "authority": "lean_operational" if proc.returncode == 0 else "python_preview",
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
