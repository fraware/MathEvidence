#!/usr/bin/env python3
"""Normalize evidence text files to LF so content digests match Linux CI."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    changed = 0
    for pattern in ("evidence/**/*.lean", "evidence/**/*.md"):
        for path in ROOT.glob(pattern):
            raw = path.read_bytes()
            if b"\r\n" not in raw and b"\r" not in raw:
                continue
            path.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
            changed += 1
            print(f"normalized {path.relative_to(ROOT).as_posix()}")
    print(f"normalized {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
