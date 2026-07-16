#!/usr/bin/env python3
"""Fail closed on project `sorry` or project-specific `axiom` in MathEvidence/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    ROOT / "MathEvidence" / "Core",
    ROOT / "MathEvidence" / "IR",
    ROOT / "MathEvidence" / "Checkers",
    ROOT / "MathEvidence" / "Tactic",
    ROOT / "MathEvidence" / "Registry",
    ROOT / "MathEvidence" / "Testing",
]
ROOT_FILES = [
    ROOT / "MathEvidence" / "Core.lean",
    ROOT / "MathEvidence" / "IR.lean",
    ROOT / "MathEvidence" / "Checkers.lean",
    ROOT / "MathEvidence" / "Tactic.lean",
    ROOT / "MathEvidence" / "Registry.lean",
    ROOT / "MathEvidence" / "Testing.lean",
]

# Match standalone `sorry` / `axiom` commands (not in comments/strings best-effort).
SORRY = re.compile(r"(?m)^\s*sorry\b")
AXIOM = re.compile(r"(?m)^\s*axiom\s+\w+")


def lean_files() -> list[Path]:
    files: list[Path] = []
    for path in SCAN_ROOTS:
        if path.is_dir():
            files.extend(path.rglob("*.lean"))
    for path in ROOT_FILES:
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def strip_block_comments(text: str) -> str:
    return re.sub(r"/-.*?-/", "", text, flags=re.DOTALL)


def main() -> int:
    violations: list[str] = []
    for path in lean_files():
        raw = path.read_text(encoding="utf-8")
        text = strip_block_comments(raw)
        # Drop line comments
        lines = []
        for line in text.splitlines():
            if "--" in line:
                line = line[: line.index("--")]
            lines.append(line)
        body = "\n".join(lines)
        rel = path.relative_to(ROOT).as_posix()
        for m in SORRY.finditer(body):
            violations.append(f"{rel}: sorry")
        for m in AXIOM.finditer(body):
            violations.append(f"{rel}: axiom declaration")
    if violations:
        print("sorry/axiom audit FAILED:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print(f"sorry/axiom audit ok ({len(lean_files())} files, 0 sorry, 0 axiom)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
