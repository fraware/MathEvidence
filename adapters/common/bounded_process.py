"""Bounded argv-only subprocess execution (SPEC-11).

Provides wall-clock timeout, process-group termination (POSIX ``start_new_session``
+ ``killpg``, Windows ``CREATE_NEW_PROCESS_GROUP``), output capture caps,
controlled cwd, and an optional environment allowlist. Never uses shell=True.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from adapters.common.errors import stable_error
from adapters.common.limits import ResourceLimits
from adapters.common.security_bounds import reject_path_traversal

# Minimal env keys preserved when an allowlist is used (platform-safe defaults).
_DEFAULT_ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "PATHEXT",
        "SystemRoot",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "USERNAME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "ComSpec",
        "COMSPEC",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
        "OS",
        "ELAN_HOME",
        "LEAN_PATH",
        "LAKE_NO_CACHE",
    }
)

EXECUTION_POLICY_ID = "mathevidence.kernel_replay.argv_only.v1"


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    output_truncated: bool
    wall_time_ms: int
    killed_process_group: bool


def filter_environ(
    base: Mapping[str, str] | None = None,
    *,
    allowlist: frozenset[str] | None = None,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build an environment from an allowlist (poisoning resistance)."""
    allowed = allowlist if allowlist is not None else _DEFAULT_ENV_ALLOWLIST
    src = dict(base) if base is not None else dict(os.environ)
    out: dict[str, str] = {}
    for key, value in src.items():
        if key in allowed or key.startswith("MATHEVIDENCE_"):
            out[key] = value
    if extra:
        out.update({str(k): str(v) for k, v in extra.items()})
    for poison in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
    ):
        out.pop(poison, None)
    out.setdefault("MATHEVIDENCE_OFFLINE", "1")
    return out


def _kill_process_group(proc: subprocess.Popen[bytes]) -> bool:
    """Best-effort kill of the process group / tree. Returns True if attempted."""
    if proc.poll() is not None:
        return False
    killed = False
    try:
        if sys.platform == "win32":
            try:
                proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                killed = True
            except (OSError, ValueError, AttributeError):
                pass
            try:
                proc.terminate()
                killed = True
            except OSError:
                pass
            try:
                proc.kill()
                killed = True
            except OSError:
                pass
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
                killed = True
            except (OSError, ProcessLookupError):
                try:
                    proc.kill()
                    killed = True
                except OSError:
                    pass
    except OSError:
        pass
    return killed


def _popen_kwargs() -> dict[str, object]:
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}  # type: ignore[attr-defined]
    return {"start_new_session": True}


def run_bounded(
    argv: list[str],
    *,
    cwd: Path,
    limits: ResourceLimits | None = None,
    env: Mapping[str, str] | None = None,
    env_allowlist: frozenset[str] | None = None,
    extra_env: Mapping[str, str] | None = None,
    use_env_allowlist: bool = True,
) -> BoundedProcessResult:
    """Run ``argv`` with wall timeout, output cap, and process-group kill.

    ``argv`` must be a list of strings (no shell). Never interpolates into a shell.
    """
    if not argv or not all(isinstance(a, str) for a in argv):
        raise stable_error("malformed_evidence", "bounded process requires argv list of str")
    if any("\x00" in a for a in argv):
        raise stable_error("malformed_evidence", "NUL byte in argv rejected")
    root = Path(cwd).resolve()
    if not root.is_dir():
        raise stable_error(
            "replay_dependency_missing",
            f"working directory missing: {root}",
            details={"kind": "setup_integrity"},
        )
    lim = limits or ResourceLimits()
    timeout_s = max(0.001, lim.max_wall_time_ms / 1000.0)
    max_out = lim.max_output_bytes

    if use_env_allowlist:
        run_env = filter_environ(env, allowlist=env_allowlist, extra=extra_env)
    else:
        run_env = dict(env) if env is not None else dict(os.environ)
        if extra_env:
            run_env.update({str(k): str(v) for k, v in extra_env.items()})

    t0 = time.monotonic()
    killed_group = False
    timed_out = False
    truncated = False

    try:
        proc = subprocess.Popen(
            argv,
            cwd=str(root),
            env=run_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            **_popen_kwargs(),  # type: ignore[arg-type]
        )
    except OSError as exc:
        raise stable_error(
            "replay_dependency_missing",
            f"failed to spawn process: {exc}",
            details={"kind": "setup_integrity", "argv0": argv[0]},
        ) from exc

    try:
        stdout_b, stderr_b = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        killed_group = _kill_process_group(proc)
        try:
            stdout_b, stderr_b = proc.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except OSError:
                pass
            stdout_b, stderr_b = proc.communicate(timeout=2.0)
    finally:
        if proc.poll() is None:
            killed_group = _kill_process_group(proc) or killed_group

    wall_ms = int((time.monotonic() - t0) * 1000)
    stdout_b = stdout_b or b""
    stderr_b = stderr_b or b""
    if len(stdout_b) > max_out or len(stderr_b) > max_out:
        truncated = True
        stdout_b = stdout_b[:max_out]
        stderr_b = stderr_b[:max_out]

    if timed_out:
        raise stable_error(
            "resource_limit_exceeded",
            f"command exceeded {lim.max_wall_time_ms}ms wall timeout",
            details={
                "kind": "wall_time",
                "argv0": argv[0],
                "killedProcessGroup": killed_group,
            },
        )
    if truncated:
        raise stable_error(
            "resource_limit_exceeded",
            f"command output exceeded {max_out} bytes",
            details={"kind": "output_bytes", "argv0": argv[0]},
        )

    return BoundedProcessResult(
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        timed_out=False,
        output_truncated=False,
        wall_time_ms=wall_ms,
        killed_process_group=killed_group,
    )


def confine_under_workspace(path: Path | str, *, root: Path) -> Path:
    """Resolve ``path`` and require it to stay under ``root`` (symlink-aware)."""
    root_resolved = root.resolve()
    raw = Path(path)
    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        reject_path_traversal(raw.as_posix().replace("\\", "/"))
        candidate = (root_resolved / raw).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise stable_error(
            "malformed_evidence",
            f"path escapes workspace: {path}",
            details={"kind": "path_traversal", "path": str(path)},
        ) from exc
    return candidate
