#!/usr/bin/env python3
"""Generate thin Milestone-3 evidence fixtures for LA + finite counterexample."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_bundle
from adapters.common.canonical import bind_request_digest
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.sympy.adapter import compute_finite_counterexample, compute_linear_algebra


def _rat(n: int, d: int = 1) -> dict:
    return {"tag": "rat", "num": str(n), "den": str(d)}


def gen_inverse() -> Path:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [[_rat(1, 2), _rat(0)], [_rat(0), _rat(2)]],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    result = compute_linear_algebra(req, ResourceTracker(ResourceLimits())).result
    out = ROOT / "evidence" / "examples" / "linear_algebra_inverse_2x2"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="witness",
    )
    print(f"wrote {out}")
    return out


def gen_counterexample() -> Path:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "logic.finite_counterexample",
            "capabilityVersion": "0.1.0",
            "predicate": {
                "varNames": ["x"],
                "domains": [{"ty": "nat", "bound": 3}],
                "pred": {
                    "tag": "eq",
                    "left": {"tag": "var", "idx": 0},
                    "right": {"tag": "lit", "v": {"tag": "nat", "v": 0}},
                },
            },
            "requestedClaim": "refutation",
            "resourcePolicy": {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576},
        }
    )
    result = compute_finite_counterexample(req, ResourceTracker(ResourceLimits())).result
    out = ROOT / "evidence" / "examples" / "finite_counterexample_nat_eq0"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="refutation",
    )
    print(f"wrote {out}")
    return out


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"copied {src} -> {dst}")


def main() -> int:
    inv = gen_inverse()
    cex = gen_counterexample()
    _copy_tree(
        inv, ROOT / "evidence" / "conformance" / "linear_algebra" / "inverse_witness_2x2" / "bundle"
    )
    _copy_tree(
        cex,
        ROOT
        / "evidence"
        / "conformance"
        / "finite_counterexample"
        / "simple_false_universal"
        / "bundle",
    )
    # Remove mistakenly placed path from earlier generator bug if present.
    bad = ROOT / "evidence" / "conformance" / "finite_counterexample" / "inverse_witness_2x2"
    if bad.exists():
        shutil.rmtree(bad)
        print(f"removed stale {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
