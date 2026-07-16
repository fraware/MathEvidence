#!/usr/bin/env python3
"""Track Foundry / library contribution records (honest counts).

Reads YAML/JSON stubs under docs/foundry/contributions/. Does not invent
merged PRs, funding, or frontier acceleration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRIB_DIR = ROOT / "docs" / "foundry" / "contributions"


def _parse_simple_yaml(text: str) -> dict:
    """Minimal key: value YAML subset for contribution stubs (no deps)."""
    data: dict = {}
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        if val in {"null", "Null", "~", ""}:
            data[key] = None
        elif val.lower() in {"true", "false"}:
            data[key] = val.lower() == "true"
        else:
            data[key] = val
    return data


def load_records() -> list[dict]:
    records: list[dict] = []
    if not CONTRIB_DIR.is_dir():
        return records
    for path in sorted(CONTRIB_DIR.iterdir()):
        if path.name.upper() == "README.MD" or path.name.startswith("."):
            continue
        if path.suffix.lower() == ".json":
            records.append(json.loads(path.read_text(encoding="utf-8")))
        elif path.suffix.lower() in {".yaml", ".yml"}:
            records.append(_parse_simple_yaml(path.read_text(encoding="utf-8")))
    return records


def measure() -> dict:
    records = load_records()
    by_status: dict[str, int] = {}
    for r in records:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
    merged = by_status.get("merged", 0)
    return {
        "metric": "library_contribution_tracking",
        "records_total": len(records),
        "by_status": by_status,
        "merged_count": merged,
        "records_dir": str(CONTRIB_DIR.relative_to(ROOT)).replace("\\", "/"),
        "template": "docs/foundry/library-contribution-template.md",
        "claims": {
            "tracking_script": True,
            "frontier_acceleration": False,
            "funding_secured": False,
            "invented_contributions": False,
        },
        "notes": (
            "Zero merged records is an honest empty ledger. "
            "Add real YAML/JSON stubs under docs/foundry/contributions/."
        ),
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"contributions: total={result['records_total']} "
        f"merged={result['merged_count']} (no inventions)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
