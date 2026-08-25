"""Capability-specific environment locks for theorem certification.

Exact replay locks bind not only toolchain/import names, but also the trusted
MathEvidence Lean source tree and dependency lockfile. Candidate-generated
modules under ``MathEvidence/Generated`` are intentionally excluded: they are
certificate inputs whose accepted theorem/proof identity is measured separately.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

from adapters.common.canonical import sha256_digest

CURRENT_ENVIRONMENT_LOCK_SCHEMA_VERSION = "0.4.0"

CAPABILITY_IMPORTS: dict[str, tuple[str, ...]] = {
    "algebra.ideal_membership_witness": (
        "MathEvidence.Checkers.IdealMembership.ReplaySound",
    ),
    "algebra.rational_equality": (
        "MathEvidence.Checkers.RationalEquality.ReplaySound",
    ),
    "algebra.linear_algebra": (
        "MathEvidence.Checkers.LinearAlgebra.ReplaySound",
    ),
    "logic.finite_counterexample": (
        "MathEvidence.Checkers.Counterexample.ReplaySound",
    ),
    "algebra.formal_rational_calculus": (
        "MathEvidence.Checkers.Calculus.ReplaySound",
    ),
    "analysis.analytic_calculus": (
        "MathEvidence.Checkers.AnalyticCalculus.ReplaySound",
    ),
}


def _read_lean_toolchain(repo_root: Path) -> str:
    value = (repo_root / "lean-toolchain").read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("lean-toolchain is empty")
    return value


def _read_mathlib_revision(repo_root: Path) -> str:
    text = (repo_root / "lakefile.toml").read_text(encoding="utf-8")
    block = re.search(
        r'\[\[require\]\]\s*\nname\s*=\s*"mathlib"(?P<body>.*?)(?:\n\[\[|\Z)',
        text,
        flags=re.DOTALL,
    )
    if block is None:
        raise ValueError("lakefile.toml has no mathlib require block")
    rev = re.search(r'^rev\s*=\s*"([^"]+)"', block.group("body"), flags=re.MULTILINE)
    if rev is None:
        raise ValueError("mathlib require block has no pinned rev")
    return rev.group(1)


def _content_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _project_revision(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "workspace"
    value = (proc.stdout or "").strip()
    if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value):
        return value
    return "workspace"


def _trusted_lean_source_digest(repo_root: Path) -> str:
    source_root = repo_root / "MathEvidence"
    if not source_root.is_dir():
        raise ValueError("MathEvidence source tree is missing")
    entries: list[dict[str, str]] = []
    for path in sorted(source_root.rglob("*.lean")):
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith("MathEvidence/Generated/"):
            continue
        entries.append({"path": rel, "digest": _content_digest(path)})
    if not entries:
        raise ValueError("MathEvidence trusted Lean source tree is empty")
    return sha256_digest(
        {
            "profile": "mathevidence-trusted-lean-source-tree-0.1",
            "files": entries,
        }
    )


def _dependency_lock_digest(repo_root: Path) -> str:
    manifest = repo_root / "lake-manifest.json"
    if not manifest.is_file():
        raise ValueError("lake-manifest.json is missing")
    return _content_digest(manifest)


def current_capability_environment_lock(
    repo_root: Path | str, capability_id: str
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    imports = CAPABILITY_IMPORTS.get(capability_id)
    if imports is None:
        raise ValueError(f"no exact environment-lock profile for {capability_id}")
    return {
        "schemaVersion": CURRENT_ENVIRONMENT_LOCK_SCHEMA_VERSION,
        "leanVersion": _read_lean_toolchain(root),
        "lakeVersion": "lake",
        "mathlibRevision": _read_mathlib_revision(root),
        "imports": list(imports),
        "projectRevision": _project_revision(root),
        "projectSourceDigest": _trusted_lean_source_digest(root),
        "dependencyLockDigest": _dependency_lock_digest(root),
    }
