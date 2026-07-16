"""LeanLink integration scaffold (non-TCB).

This module documents the future native bridge surface. It must not be imported
by Lean checkers. Loading LeanLink is optional and disabled unless explicitly
configured.

**Supported live Mathematica path for R1:** ``MATHEVIDENCE_WOLFRAMSCRIPT`` →
``wolframscript`` (see ``adapters/mathematica/adapter.py``). LeanLink remains
disabled until fuzz + review checkboxes in
``docs/architecture/leanlink-adapter-review.md`` are closed with evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LeanLinkConfig:
    root: Path | None
    enabled: bool
    notes: str


def load_leanlink_config(path: str | None) -> LeanLinkConfig:
    if not path:
        return LeanLinkConfig(
            root=None,
            enabled=False,
            notes="LeanLink not configured; wolframscript path used when available.",
        )
    root = Path(path)
    if not root.exists():
        return LeanLinkConfig(
            root=root,
            enabled=False,
            notes=f"LeanLink path does not exist: {root}",
        )
    return LeanLinkConfig(
        root=root,
        enabled=False,  # native bridge intentionally off until fuzz + review complete
        notes=(
            "LeanLink path present but native bridge disabled pending "
            "docs/architecture/leanlink-adapter-review.md checklist completion."
        ),
    )
