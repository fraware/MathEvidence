#!/usr/bin/env python3
"""Property-test entrypoint for CI / justfile (pytest Hypothesis suite)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(ROOT / "adapters" / "common" / "test_property.py"),
        "-q",
    ]
    print("running:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
