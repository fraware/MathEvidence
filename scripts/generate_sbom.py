#!/usr/bin/env python3
"""Generate a minimal CycloneDX-like SBOM for MathEvidence release packaging.

This is an engineering SBOM scaffold: Python requirements freeze + Lean toolchain
pins. It does not claim SPDX legal review or signed attestations.
"""

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
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _parse_requirements(path: Path) -> list[dict[str, Any]]:
    comps: list[dict[str, Any]] = []
    if not path.is_file():
        return comps
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line
        version = None
        for sep in ("==", ">=", "~=", "!="):
            if sep in line:
                name, version = line.split(sep, 1)
                name = name.strip()
                version = version.strip()
                break
        comps.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name}@{version}" if version else f"pkg:pypi/{name}",
            }
        )
    return comps


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "sbom"
    out_dir.mkdir(parents=True, exist_ok=True)

    lean = (ROOT / "lean-toolchain").read_text(encoding="utf-8").strip()
    components = _parse_requirements(ROOT / "requirements-freeze.txt")
    if not components:
        components = _parse_requirements(ROOT / "requirements.txt")

    components.append(
        {
            "type": "framework",
            "name": "lean4",
            "version": lean,
            "purl": f"pkg:generic/lean4@{lean}",
        }
    )

    freeze = ROOT / "requirements-freeze.txt"
    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "component": {
                "type": "application",
                "name": "MathEvidence",
                "version": "0.1.0",
            },
            "properties": [
                {"name": "mathevidence:gitCommit", "value": _git_rev()},
                {"name": "mathevidence:leanToolchain", "value": lean},
                {
                    "name": "mathevidence:requirementsFreezeDigest",
                    "value": _sha256_file(freeze) if freeze.is_file() else "absent",
                },
                {
                    "name": "mathevidence:honesty",
                    "value": "engineering_scaffold_unsigned",
                },
            ],
        },
        "components": components,
    }

    out_path = out_dir / "sbom.cdx.json"
    text = json.dumps(bom, indent=2) + "\n"
    out_path.write_text(text, encoding="utf-8")
    digest_path = out_dir / "sbom.cdx.json.sha256"
    digest_path.write_text(
        hashlib.sha256(text.encode("utf-8")).hexdigest() + "  sbom.cdx.json\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path} ({len(components)} components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
