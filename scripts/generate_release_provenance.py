#!/usr/bin/env python3
"""Emit release provenance manifest: evidence digests + Lean toolchain / lake pins."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _git_rev() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _lean_toolchain() -> str:
    path = ROOT / "lean-toolchain"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return "unknown"


def _lake_pins() -> dict[str, Any]:
    path = ROOT / "lake-manifest.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    packages = []
    for pkg in data.get("packages") or []:
        packages.append(
            {
                "name": pkg.get("name"),
                "rev": pkg.get("rev"),
                "url": pkg.get("url"),
                "inputRev": pkg.get("inputRev"),
            }
        )
    return {"manifestVersion": data.get("version"), "packages": packages}


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "provenance"
    out_dir.mkdir(parents=True, exist_ok=True)

    evidence_files: list[dict[str, str]] = []
    for root_name in ("evidence", "benchmarks"):
        root = ROOT / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".md"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            evidence_files.append({"path": rel, "digest": _sha256_file(path)})

    manifest = {
        "schemaVersion": "0.1.0",
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gitCommit": _git_rev(),
        "leanToolchain": _lean_toolchain(),
        "lake": _lake_pins(),
        "evidenceAndBenchmarkFiles": evidence_files,
        "notes": [
            "Lean commit pin is lean-toolchain + lake-manifest package revs.",
            "Evidence digests are content hashes of committed JSON/MD under evidence/ and benchmarks/.",
        ],
    }
    out_path = out_dir / "provenance-manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(evidence_files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
