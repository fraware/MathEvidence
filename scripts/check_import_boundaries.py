#!/usr/bin/env python3
"""Fail closed if Core / IR / Checkers Lean sources import forbidden modules."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRUSTED = [
    ROOT / "MathEvidence" / "Core",
    ROOT / "MathEvidence" / "IR",
    ROOT / "MathEvidence" / "Checkers",
]
# Also scan root module files for those packages.
TRUSTED_ROOT_FILES = [
    ROOT / "MathEvidence" / "Core.lean",
    ROOT / "MathEvidence" / "IR.lean",
    ROOT / "MathEvidence" / "Checkers.lean",
]

FORBIDDEN = re.compile(
    r"^\s*import\s+(MathEvidence\.(Tactic|Registry|Testing)|adapters)\b",
    re.MULTILINE,
)
# Broader scan for obvious adapter / network / IO escapes in trusted packages.
FORBIDDEN_TEXT = re.compile(
    r"\b(IO\.Process|Lean\.Server|adapters\.|Network\.|Socket\.)\b"
)


def lean_files() -> list[Path]:
    files: list[Path] = []
    for path in TRUSTED:
        if path.is_dir():
            files.extend(path.rglob("*.lean"))
    for path in TRUSTED_ROOT_FILES:
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def main() -> int:
    violations: list[str] = []
    for path in lean_files():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        if FORBIDDEN.search(text):
            violations.append(f"{rel}: forbidden import of Tactic/Registry/Testing/adapters")
        if FORBIDDEN_TEXT.search(text):
            violations.append(f"{rel}: forbidden process/network/adapter reference")
    if violations:
        print("import-boundary check FAILED:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print(f"import-boundary check ok ({len(lean_files())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
