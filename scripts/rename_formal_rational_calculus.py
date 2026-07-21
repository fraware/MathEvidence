#!/usr/bin/env python3
"""Rename algebra.formal_rational_calculus -> algebra.formal_rational_calculus."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "algebra.formal_rational_calculus"
NEW = "algebra.formal_rational_calculus"
SKIP = {".lake", ".git", "node_modules", "__pycache__", ".cursor"}
EXTS = {
    ".json",
    ".py",
    ".lean",
    ".md",
    ".wl",
    ".yml",
    ".yaml",
    ".toml",
}


def main() -> int:
    src = ROOT / "registry" / "capabilities" / f"{OLD}.json"
    dst = ROOT / "registry" / "capabilities" / f"{NEW}.json"
    if src.is_file():
        data = json.loads(src.read_text(encoding="utf-8"))
        data["id"] = NEW
        data["domain"] = NEW
        data.pop("renameNote", None)
        limits = []
        for item in data.get("knownLimitations", []):
            if "Planned ID rename" in item or "Planned rename" in item:
                continue
            limits.append(item)
        data["knownLimitations"] = [
            "FORMAL RATIONAL CALCULUS: not HasDerivAt / analytic ODE "
            f"(renamed from {OLD}).",
            *limits,
        ]
        if data.get("conformance", {}).get("suite"):
            # keep suite path; directory rename is separate
            pass
        dst.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        src.unlink()
        print(f"wrote {dst.relative_to(ROOT)}")

    updated = 0
    for path in ROOT.rglob("*"):
        if any(part in SKIP for part in path.parts):
            continue
        if not path.is_file() or path.suffix not in EXTS:
            continue
        if path.resolve() == dst.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if OLD not in text:
            continue
        path.write_text(text.replace(OLD, NEW), encoding="utf-8", newline="\n")
        updated += 1
        print(f"updated {path.relative_to(ROOT)}")
    print(f"updated_files={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
