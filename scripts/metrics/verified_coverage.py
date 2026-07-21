#!/usr/bin/env python3
"""§19 verified computational coverage (in-repo proxy).

Measures the fraction of representative computational obligations in
benchmarks/real_world + docs/validation/bottlenecks.md that have a bound
capability and committed evidence or conformance path.

This is an engineering proxy — not a claim about all Lean developments.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REAL_WORLD = ROOT / "benchmarks" / "real_world"
BOTTLENECKS = ROOT / "docs" / "validation" / "bottlenecks.md"
EVIDENCE = ROOT / "evidence"


def _real_world_rows() -> list[dict]:
    manifest = REAL_WORLD / "manifest.json"
    if not manifest.is_file():
        return []
    data = json.loads(manifest.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for t in data.get("cases") or data.get("tasks") or data.get("obligations") or []:
        if isinstance(t, str):
            path = REAL_WORLD / t
            if path.is_file():
                rows.append(json.loads(path.read_text(encoding="utf-8")))
        elif isinstance(t, dict):
            if "path" in t:
                path = REAL_WORLD / t["path"]
                if path.is_file():
                    row = json.loads(path.read_text(encoding="utf-8"))
                    row.setdefault("id", t.get("id"))
                    row.setdefault("capability", t.get("capability"))
                    rows.append(row)
                else:
                    rows.append(t)
            else:
                rows.append(t)
    if not rows:
        for path in sorted(REAL_WORLD.glob("RW*.json")):
            rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def _bottleneck_capability_mentions() -> int:
    if not BOTTLENECKS.is_file():
        return 0
    text = BOTTLENECKS.read_text(encoding="utf-8")
    # Table rows that look like data (have pipes and aren't header separators)
    rows = 0
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        if "bottleneck" in line.lower() and "domain" in line.lower():
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not cells[0].lower().startswith("id"):
            rows += 1
    return rows


def _has_evidence_for_capability(cap: str | None) -> bool:
    if not cap:
        return False
    # Map capability id fragments to evidence dirs
    needles = {
        "algebra.rational_equality": ["rational_equality", "rfc0001"],
        "algebra.linear_algebra": ["linear_algebra"],
        "logic.finite_counterexample": ["finite_counterexample", "counterexample"],
        "algebra.formal_rational_calculus": ["symbolic_calculus", "calculus_"],
    }
    keys = needles.get(cap, [cap.replace(".", "_")])
    for root in (EVIDENCE / "examples", EVIDENCE / "conformance"):
        if not root.is_dir():
            continue
        for pattern in ("manifest.cjson", "manifest.json"):
            for p in root.rglob(pattern):
                s = str(p).replace("\\", "/")
                if any(k in s for k in keys):
                    return True
    return False


def measure() -> dict:
    rw = _real_world_rows()
    covered = 0
    details: list[dict] = []
    for row in rw:
        cap = row.get("capability")
        ok = bool(cap) and _has_evidence_for_capability(str(cap))
        if ok:
            covered += 1
        details.append(
            {
                "id": row.get("id") or row.get("name"),
                "capability": cap,
                "covered": ok,
            }
        )
    total = len(rw)
    rate = (covered / total) if total else 0.0
    bn = _bottleneck_capability_mentions()
    return {
        "metric": "verified_computational_coverage",
        "spec": "PROJECT_SPEC §19 primary (in-repo proxy)",
        "real_world_total": total,
        "real_world_covered": covered,
        "real_world_coverage_rate": round(rate, 4),
        "bottleneck_table_rows": bn,
        "details": details,
        "claims": {
            "in_repo_proxy": True,
            "all_lean_developments": False,
        },
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"verified_coverage: {result['real_world_covered']}/"
        f"{result['real_world_total']} "
        f"({result['real_world_coverage_rate']:.1%} real-world proxy)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
