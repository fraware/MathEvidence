"""Capability-specific environment locks for theorem certification.

The old v0.3 helper in ``theorem_identity.py`` is intentionally retained for
historical rational-equality vectors. New exact replay paths use this module so
an ideal-membership theorem is never labeled with the rational checker import
set.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adapters.common.theorem_identity import ENVIRONMENT_LOCK_SCHEMA_VERSION

CAPABILITY_IMPORTS: dict[str, tuple[str, ...]] = {
    "algebra.ideal_membership_witness": (
        "MathEvidence.Checkers.IdealMembership.ReplaySound",
    ),
}


def _read_lean_toolchain(repo_root: Path) -> str:
    path = repo_root / "lean-toolchain"
    value = path.read_text(encoding="utf-8").strip()
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


def current_capability_environment_lock(
    repo_root: Path | str, capability_id: str
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    imports = CAPABILITY_IMPORTS.get(capability_id)
    if imports is None:
        raise ValueError(f"no exact environment-lock profile for {capability_id}")
    return {
        "schemaVersion": ENVIRONMENT_LOCK_SCHEMA_VERSION,
        "leanVersion": _read_lean_toolchain(root),
        "lakeVersion": "lake",
        "mathlibRevision": _read_mathlib_revision(root),
        "imports": list(imports),
    }
