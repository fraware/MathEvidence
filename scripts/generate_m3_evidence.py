#!/usr/bin/env python3
"""Generate LA + finite-counterexample example and conformance evidence (R4).

Produces SymPy-backed accept bundles for every requiredCases entry that must
pass the Python Lean-mirror checker, plus intentional reject fixtures for
singular inverse, hash mismatch, type mismatch, and out-of-domain witnesses.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_bundle
from adapters.common.canonical import bind_request_digest
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.sympy.adapter import compute_finite_counterexample, compute_linear_algebra

LA_CONF = ROOT / "evidence" / "conformance" / "linear_algebra"
CEX_CONF = ROOT / "evidence" / "conformance" / "finite_counterexample"
EXAMPLES = ROOT / "evidence" / "examples"

POLICY = {"maxWallTimeMs": 60000, "maxOutputBytes": 1048576}
ZERO_DIGEST = "sha256:" + ("00" * 32)


def _rat(n: int, d: int = 1) -> dict[str, str]:
    return {"tag": "rat", "num": str(n), "den": str(d)}


def _matrix(rows: list[list[dict[str, str]]]) -> dict[str, Any]:
    return {
        "tag": "matrix",
        "rows": len(rows),
        "cols": len(rows[0]) if rows else 0,
        "entries": rows,
    }


def _write_case_meta(suite: Path, name: str, expect: str, **extra: Any) -> None:
    case_dir = suite / name
    case_dir.mkdir(parents=True, exist_ok=True)
    payload = {"id": name, "expect": expect, **extra}
    (case_dir / "case.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"copied {src} -> {dst}")


def gen_la_inverse() -> tuple[dict[str, Any], dict[str, Any]]:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": _matrix([[_rat(1, 2), _rat(0)], [_rat(0), _rat(2)]]),
            "requestedClaim": "witness",
            "resourcePolicy": dict(POLICY),
        }
    )
    result = compute_linear_algebra(req, ResourceTracker(ResourceLimits())).result
    out = EXAMPLES / "linear_algebra_inverse_2x2"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="witness",
        readme=(
            "# Example: 2x2 inverse witness\n\n"
            "Diagonal matrix inverse over ℚ. SymPy generates; Lean owns accept.\n"
        ),
    )
    print(f"wrote {out}")
    return req, result


def gen_la_system() -> Path:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "system_solution",
            "matrix": _matrix([[_rat(1), _rat(1)], [_rat(0), _rat(1)]]),
            "rhs": [_rat(3), _rat(2)],
            "requestedClaim": "witness",
            "resourcePolicy": dict(POLICY),
        }
    )
    result = compute_linear_algebra(req, ResourceTracker(ResourceLimits())).result
    out = LA_CONF / "exact_system_solution" / "bundle"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="witness",
        readme="# Conformance: exact_system_solution\n",
    )
    _write_case_meta(LA_CONF, "exact_system_solution", "accept")
    print(f"wrote {out}")
    return out


def gen_la_kernel() -> Path:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "kernel_vector",
            "matrix": _matrix([[_rat(1), _rat(2)], [_rat(2), _rat(4)]]),
            "requestedClaim": "witness",
            "resourcePolicy": dict(POLICY),
        }
    )
    result = compute_linear_algebra(req, ResourceTracker(ResourceLimits())).result
    out = LA_CONF / "kernel_vector" / "bundle"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="witness",
        readme="# Conformance: kernel_vector\n",
    )
    _write_case_meta(LA_CONF, "kernel_vector", "accept")
    print(f"wrote {out}")
    return out


def gen_la_det() -> Path:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "det_identity",
            "matrix": _matrix([[_rat(1), _rat(2)], [_rat(3), _rat(4)]]),
            "claimedDet": _rat(-2),
            "requestedClaim": "soundResult",
            "resourcePolicy": dict(POLICY),
        }
    )
    result = compute_linear_algebra(req, ResourceTracker(ResourceLimits())).result
    out = LA_CONF / "det_identity" / "bundle"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="soundResult",
        readme="# Conformance: det_identity\n",
    )
    _write_case_meta(LA_CONF, "det_identity", "accept")
    print(f"wrote {out}")
    return out


def gen_la_singular_rejected() -> Path:
    """Singular matrix with identity claimed as inverse — must fail checker."""
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "inverse_witness",
            "matrix": _matrix([[_rat(1), _rat(2)], [_rat(2), _rat(4)]]),
            "requestedClaim": "witness",
            "resourcePolicy": dict(POLICY),
        }
    )
    digest = req["requestDigest"]
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "operation": "inverse_witness",
        "inverse": _matrix([[_rat(1), _rat(0)], [_rat(0), _rat(1)]]),
        "sideConditions": ["matrix_invertible"],
        "provenance": {
            "backendId": "fixture",
            "backendVersion": "0.1.0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-16T00:00:00Z",
            "deterministic": True,
        },
    }
    out = LA_CONF / "singular_inverse_rejected" / "bundle"
    write_bundle(
        out,
        request=req,
        candidate={"reportedOk": True},
        certificate=cert,
        claim_class="witness",
        result_status="rejected",
        readme="# Conformance: singular_inverse_rejected (expected reject)\n",
    )
    _write_case_meta(LA_CONF, "singular_inverse_rejected", "reject")
    print(f"wrote {out}")
    return out


def gen_la_hash_mismatch(good_req: dict[str, Any], good_result: dict[str, Any]) -> Path:
    bad_req = dict(good_req)
    bad_req["requestDigest"] = ZERO_DIGEST
    mismatched_cert = dict(good_result["certificate"])
    mismatched_cert["requestDigest"] = ZERO_DIGEST
    out = LA_CONF / "hash_mismatch" / "bundle"
    write_bundle(
        out,
        request=bad_req,
        candidate=good_result["candidate"],
        certificate=mismatched_cert,
        claim_class="witness",
        result_status="rejected",
        readme="# Conformance: hash_mismatch (expected reject)\n",
    )
    _write_case_meta(LA_CONF, "hash_mismatch", "digest_mismatch", bindDigest=False)
    print(f"wrote {out}")
    return out


def gen_cex_simple() -> tuple[dict[str, Any], dict[str, Any]]:
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
            "resourcePolicy": dict(POLICY),
        }
    )
    result = compute_finite_counterexample(req, ResourceTracker(ResourceLimits())).result
    out = EXAMPLES / "finite_counterexample_nat_eq0"
    write_bundle(
        out,
        request=req,
        candidate=result["candidate"],
        certificate=result["certificate"],
        claim_class="refutation",
        readme=(
            "# Example: finite counterexample\n\n"
            "Predicate `x = 0` over `nat ≤ 3` falsified by a nonzero witness.\n"
        ),
    )
    print(f"wrote {out}")
    return req, result


def gen_cex_type_mismatch(good_req: dict[str, Any]) -> Path:
    digest = good_req["requestDigest"]
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "logic.finite_counterexample",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "witness": {"assignment": [{"tag": "bool", "v": False}]},
        "provenance": {
            "backendId": "fixture",
            "backendVersion": "0.1.0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-16T00:00:00Z",
            "deterministic": True,
        },
    }
    out = CEX_CONF / "witness_type_mismatch" / "bundle"
    write_bundle(
        out,
        request=good_req,
        candidate={"reportedFalse": True},
        certificate=cert,
        claim_class="refutation",
        result_status="rejected",
        readme="# Conformance: witness_type_mismatch (expected reject)\n",
    )
    _write_case_meta(CEX_CONF, "witness_type_mismatch", "reject")
    print(f"wrote {out}")
    return out


def gen_cex_ood(good_req: dict[str, Any]) -> Path:
    digest = good_req["requestDigest"]
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "logic.finite_counterexample",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "witness": {"assignment": [{"tag": "nat", "v": 9}]},
        "provenance": {
            "backendId": "fixture",
            "backendVersion": "0.1.0",
            "adapterVersion": "0.1.0",
            "generatedAt": "2026-07-16T00:00:00Z",
            "deterministic": True,
        },
    }
    out = CEX_CONF / "out_of_domain_rejected" / "bundle"
    write_bundle(
        out,
        request=good_req,
        candidate={"reportedFalse": True},
        certificate=cert,
        claim_class="refutation",
        result_status="rejected",
        readme="# Conformance: out_of_domain_rejected (expected reject)\n",
    )
    _write_case_meta(CEX_CONF, "out_of_domain_rejected", "reject")
    print(f"wrote {out}")
    return out


def gen_cex_hash_mismatch(good_req: dict[str, Any], good_result: dict[str, Any]) -> Path:
    bad_req = dict(good_req)
    bad_req["requestDigest"] = ZERO_DIGEST
    mismatched_cert = dict(good_result["certificate"])
    mismatched_cert["requestDigest"] = ZERO_DIGEST
    out = CEX_CONF / "hash_mismatch" / "bundle"
    write_bundle(
        out,
        request=bad_req,
        candidate=good_result["candidate"],
        certificate=mismatched_cert,
        claim_class="refutation",
        result_status="rejected",
        readme="# Conformance: hash_mismatch (expected reject)\n",
    )
    _write_case_meta(CEX_CONF, "hash_mismatch", "digest_mismatch", bindDigest=False)
    print(f"wrote {out}")
    return out


def main() -> int:
    LA_CONF.mkdir(parents=True, exist_ok=True)
    CEX_CONF.mkdir(parents=True, exist_ok=True)

    inv_req, inv_result = gen_la_inverse()
    _copy_tree(
        EXAMPLES / "linear_algebra_inverse_2x2",
        LA_CONF / "inverse_witness_2x2" / "bundle",
    )
    _write_case_meta(LA_CONF, "inverse_witness_2x2", "accept")

    gen_la_system()
    gen_la_kernel()
    gen_la_det()
    gen_la_singular_rejected()
    gen_la_hash_mismatch(inv_req, inv_result)

    cex_req, cex_result = gen_cex_simple()
    _copy_tree(
        EXAMPLES / "finite_counterexample_nat_eq0",
        CEX_CONF / "simple_false_universal" / "bundle",
    )
    _write_case_meta(CEX_CONF, "simple_false_universal", "accept")
    gen_cex_type_mismatch(cex_req)
    gen_cex_ood(cex_req)
    gen_cex_hash_mismatch(cex_req, cex_result)

    bad = CEX_CONF / "inverse_witness_2x2"
    if bad.exists():
        shutil.rmtree(bad)
        print(f"removed stale {bad}")

    (LA_CONF / "README.md").write_text(
        "# Conformance suite for algebra.linear_algebra\n\n"
        "Lean offline fixtures: `MathEvidence.Checkers.LinearAlgebra.Tests`.\n"
        "Python offline bundles under each `requiredCases` name "
        "(accept + intentional reject).\n"
        "SymPy live generation backs accept cases; Lean owns theorem acceptance.\n"
        "Mathematica/Sage remain declared/placeholder (not dual-backend).\n",
        encoding="utf-8",
    )
    (CEX_CONF / "README.md").write_text(
        "# Conformance suite for logic.finite_counterexample\n\n"
        "Lean offline fixtures: `MathEvidence.Checkers.Counterexample.Tests`.\n"
        "Python offline bundles under each `requiredCases` name "
        "(accept + intentional reject).\n"
        "SymPy/enumeration live generation backs accept cases; Lean owns accept.\n"
        "Mathematica/Sage remain declared/placeholder (not dual-backend).\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
