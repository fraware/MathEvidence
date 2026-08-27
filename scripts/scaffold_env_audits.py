#!/usr/bin/env python3
"""Environment-level import/axiom audit reports (ME-RV-071 / ME-RV-072).

Runs Lake executables ``mathevidence-import-graph`` /
``mathevidence-axiom-report`` via ``lake env`` so ``LEAN_PATH`` includes built
oleans. Drivers load trusted roots with ``Lean.importModules`` and emit
Environment-level JSON. By default reports are written under
``docs/validation/ci/``; release workflows can redirect them with
``MATHEVIDENCE_ENV_AUDIT_OUT_DIR`` so runtime evidence does not mutate the
checked-out release tree.

Exit non-zero if either driver fails or reports ``environmentLevel: false``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _resolve_out_dir() -> Path:
    raw = os.environ.get("MATHEVIDENCE_ENV_AUDIT_OUT_DIR", "").strip()
    if not raw:
        return ROOT / "docs" / "validation" / "ci"
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


OUT_DIR = _resolve_out_dir()
TRUSTED_ROOTS = [
    "MathEvidence/Core",
    "MathEvidence/IR",
    "MathEvidence/Encoding",
    "MathEvidence/Checkers",
]


def _run_lake_exe(name: str, out_path: Path) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    exe_unix = ROOT / ".lake" / "build" / "bin" / name
    exe_win = ROOT / ".lake" / "build" / "bin" / (name + ".exe")
    exe = exe_win if exe_win.is_file() else exe_unix
    proc = _run(["lake", "env", str(exe), "--output", str(out_path)])
    payload: dict = {
        "driver": name,
        "exitCode": proc.returncode,
        "stdoutTail": (proc.stdout or "")[-2000:],
        "stderrTail": (proc.stderr or "")[-2000:],
    }
    if out_path.is_file():
        try:
            payload["report"] = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload["reportPath"] = str(out_path.as_posix())
            payload["reportParseError"] = True
    return payload


def _scaffold(kind: str, reason: str) -> dict:
    return {
        "schemaVersion": "0.1.0",
        "recordKind": f"environment_{kind}_audit_scaffold",
        "status": "pending_environment",
        "recordedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trustedRoots": TRUSTED_ROOTS,
        "reason": reason,
        "acceptance": {
            "regexSourceScan": "defense_in_depth_only",
            "environmentAudit": "required_for_ME-RV-071_072_closure",
            "blockedOn": ["lake_build", "mathlib_cache", "compiled_audit_drivers"],
        },
        "environmentLevel": False,
    }


def _classify(payload: dict) -> dict:
    report = payload.get("report") or {}
    env_level = bool(report.get("environmentLevel"))
    status_pass = report.get("status") == "pass" and payload.get("exitCode") == 0
    if payload.get("exitCode") not in (0, 1) or "report" not in payload:
        return {
            "status": "pending_environment",
            "environmentLevel": False,
            "note": "driver missing or failed to produce JSON",
            **payload,
        }
    if env_level and status_pass:
        return {
            "status": "environment_audit_pass",
            "environmentLevel": True,
            "note": "Lean.Environment importModules / CollectAxioms driver",
            **payload,
        }
    if env_level:
        return {
            "status": "environment_audit_fail",
            "environmentLevel": True,
            "note": "Environment driver ran; policy violations present",
            **payload,
        }
    return {
        "status": "driver_executed_source_scan",
        "environmentLevel": False,
        "note": "Driver did not set environmentLevel=true",
        **payload,
    }


def _ensure_trusted_oleans() -> int:
    """Build audit drivers + entry modules so importModules can load oleans."""
    proc = subprocess.run(
        [
            "lake",
            "build",
            "MathEvidence.Core.Basic",
            "MathEvidence.IR.MatrixExpr.Ops",
            "MathEvidence.Encoding.Matrix",
            "MathEvidence.Checkers.LinearAlgebra.Bridge",
            "MathEvidence.Checkers.RationalEquality.Soundness",
            "MathEvidence.Checkers.IdealMembership.Soundness",
            "MathEvidence.Checkers.Counterexample.Soundness",
            "mathevidence-import-graph",
            "mathevidence-axiom-report",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        print((proc.stderr or proc.stdout or "")[-2000:], file=sys.stderr)
    return proc.returncode


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bin_dir = ROOT / ".lake" / "build" / "bin"
    if _ensure_trusted_oleans() != 0:
        results = {
            "schemaVersion": "0.1.0",
            "recordKind": "environment_audit_bundle",
            "recordedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "importAudit": _scaffold(
                "import",
                "lake build of trusted roots / audit drivers failed",
            ),
            "axiomAudit": _scaffold(
                "axiom",
                "lake build of trusted roots / audit drivers failed",
            ),
        }
        bundle_path = OUT_DIR / "environment_audit_scaffold.json"
        bundle_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {_display_path(bundle_path)}")
        return 1

    if not (bin_dir / "mathevidence-import-graph").is_file() and not (
        bin_dir / "mathevidence-import-graph.exe"
    ).is_file():
        results = {
            "schemaVersion": "0.1.0",
            "recordKind": "environment_audit_bundle",
            "recordedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "importAudit": _scaffold(
                "import",
                "mathevidence-import-graph not built; run lake build mathevidence-import-graph",
            ),
            "axiomAudit": _scaffold(
                "axiom",
                "mathevidence-axiom-report not built; run lake build mathevidence-axiom-report",
            ),
        }
        bundle_path = OUT_DIR / "environment_audit_scaffold.json"
        bundle_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {_display_path(bundle_path)}")
        print("env audits: pending (binaries missing)", file=sys.stderr)
        return 1

    results: dict = {
        "schemaVersion": "0.1.0",
        "recordKind": "environment_audit_bundle",
        "recordedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "importAudit": _classify(
            _run_lake_exe(
                "mathevidence-import-graph", OUT_DIR / "import_graph_env.json"
            )
        ),
        "axiomAudit": _classify(
            _run_lake_exe(
                "mathevidence-axiom-report", OUT_DIR / "axiom_report_env.json"
            )
        ),
    }

    bundle_path = OUT_DIR / "environment_audit_scaffold.json"
    bundle_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_display_path(bundle_path)}")

    rc = 0
    for key, label in (("importAudit", "import"), ("axiomAudit", "axiom")):
        st = results[key].get("status")
        env = results[key].get("environmentLevel")
        print(f"env {label} audit: status={st} environmentLevel={env}")
        if st == "pending_environment" or not env:
            rc = 1
        if st == "environment_audit_fail":
            rc = 1
        if results[key].get("exitCode") not in (0, None):
            # exitCode 1 = policy fail (already counted); 2/3 = driver error
            if results[key].get("exitCode") not in (0, 1):
                rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
