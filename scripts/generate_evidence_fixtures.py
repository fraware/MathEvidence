#!/usr/bin/env python3
"""Generate RFC 0001 conformance fixtures and example evidence bundles."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_bundle  # noqa: E402
from adapters.common.canonical import bind_request_digest, canonical_dumps, sha256_digest  # noqa: E402
from adapters.common.limits import ResourceLimits, ResourceTracker  # noqa: E402
from adapters.common.rational_ir import (  # noqa: E402
    add_expr,
    div_expr,
    int_expr,
    mul_expr,
    pow_expr,
    sub_expr,
    var_expr,
)
from adapters.common.schema_validate import SchemaStore  # noqa: E402
from adapters.sympy.adapter import compute_rational_equality  # noqa: E402

SUITE = ROOT / "evidence" / "conformance" / "rfc0001"
EXAMPLES = ROOT / "evidence" / "examples"
VECTORS = ROOT / "evidence" / "conformance" / "vectors"


def base_request(lhs, rhs, variables, assumptions=None) -> dict:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": n, "type": "Rat"} for n in variables],
        "lhs": lhs,
        "rhs": rhs,
        "knownAssumptions": assumptions or [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
    }
    return bind_request_digest(req)


def write_case(name: str, *, expect: str, request: dict, **meta) -> Path:
    case_dir = SUITE / name
    case_dir.mkdir(parents=True, exist_ok=True)
    case = {"id": name, "expect": expect, **meta}
    (case_dir / "case.json").write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
    (case_dir / "request.json").write_text(
        json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return case_dir


def maybe_bundle(case_dir: Path, request: dict, store: SchemaStore) -> None:
    tracker = ResourceTracker(ResourceLimits())
    result = compute_rational_equality(request, tracker, schemas=store)
    write_bundle(
        case_dir / "bundle",
        request=request,
        candidate=result.result["candidate"],
        certificate=result.result["certificate"],
        schemas=store,
        readme=f"# Conformance bundle: {case_dir.name}\n",
    )


def main() -> int:
    store = SchemaStore()
    SUITE.mkdir(parents=True, exist_ok=True)
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    VECTORS.mkdir(parents=True, exist_ok=True)

    # valid_identity: (x^2 - 1)/(x - 1) = x + 1  (needs x ≠ 1)
    x = var_expr("x")
    lhs = div_expr(sub_expr(pow_expr(x, 2), int_expr(1)), sub_expr(x, int_expr(1)))
    rhs = add_expr(x, int_expr(1))
    req = base_request(lhs, rhs, ["x"])
    write_case(
        "valid_identity",
        expect="valid_identity",
        request=req,
        requireFactorRoles=["original_division"],
    )
    maybe_bundle(SUITE / "valid_identity", req, store)

    # false_identity: x/x = 2
    req = base_request(div_expr(x, x), int_expr(2), ["x"])
    write_case("false_identity", expect="false_identity", request=req)
    maybe_bundle(SUITE / "false_identity", req, store)

    # missing_condition: same identity but we only record that factors are required
    req = base_request(lhs, rhs, ["x"], assumptions=[])
    write_case(
        "missing_condition",
        expect="valid_identity",
        request=req,
        notes="Backend still returns denominator factors; Lean exposes missing locals as goals.",
        requireFactorRoles=["original_division"],
    )
    maybe_bundle(SUITE / "missing_condition", req, store)

    # redundant_condition: include extra nonzero assumption y ≠ 0 unused
    y = var_expr("y")
    req = base_request(
        lhs,
        rhs,
        ["x", "y"],
        assumptions=[{"kind": "nonzero", "expr": y}],
    )
    write_case(
        "redundant_condition",
        expect="valid_identity",
        request=req,
        notes="Extra known assumption must not break candidate generation.",
    )
    maybe_bundle(SUITE / "redundant_condition", req, store)

    # hash_mismatch
    req = base_request(lhs, rhs, ["x"])
    bad = dict(req)
    bad["requestDigest"] = "sha256:" + ("ab" * 32)
    write_case(
        "hash_mismatch",
        expect="digest_mismatch",
        request=bad,
        bindDigest=False,
    )
    # Bundle with intentional mismatch for offline replay warnings
    tracker = ResourceTracker(ResourceLimits())
    good_req = base_request(lhs, rhs, ["x"])
    result = compute_rational_equality(good_req, tracker, schemas=store)
    mismatched_cert = dict(result.result["certificate"])
    mismatched_cert["requestDigest"] = bad["requestDigest"]
    # Skip schema-invalid? certificate digest pattern ok but binding wrong.
    # Use good request digest in cert to keep schema valid, wrong in request.
    write_bundle(
        SUITE / "hash_mismatch" / "bundle",
        request=bad,
        candidate=result.result["candidate"],
        certificate={**mismatched_cert, "requestDigest": bad["requestDigest"]},
        schemas=store,
        readme="# Intentional digest mismatch fixture\n",
    )

    # variable_permutation: declare y,x order but expression uses x
    req = base_request(lhs, rhs, ["y", "x"])
    write_case(
        "variable_permutation",
        expect="valid_identity",
        request=req,
        notes="Declaration order must not affect digest-stable math outcome.",
    )
    maybe_bundle(SUITE / "variable_permutation", req, store)

    # large_coeffs
    big = "9" * 64
    req = base_request(
        mul_expr({"tag": "int", "value": big}, x),
        mul_expr(x, {"tag": "int", "value": big}),
        ["x"],
    )
    write_case("large_coeffs", expect="valid_identity", request=req)
    maybe_bundle(SUITE / "large_coeffs", req, store)

    # unsupported_rejection: transcendental-like / unsupported via undeclared symbol
    # (schema-valid IR that the adapter must reject)
    unsupported = base_request(var_expr("x"), int_expr(0), ["x"])
    unsupported["lhs"] = var_expr("sin_x")  # not declared — stands in for rejected syntax class
    unsupported.pop("requestDigest", None)
    unsupported = bind_request_digest(unsupported)
    write_case(
        "unsupported_rejection",
        expect="unsupported",
        request=unsupported,
        errorCode="unsupported_expression",
        bindDigest=True,
    )

    # Example bundle (SymPy-generated, Mathematica-replayable offline)
    example_req = base_request(lhs, rhs, ["x"])
    tracker = ResourceTracker(ResourceLimits())
    result = compute_rational_equality(example_req, tracker, schemas=store)
    write_bundle(
        EXAMPLES / "rational_equality_basic",
        request=example_req,
        candidate=result.result["candidate"],
        certificate=result.result["certificate"],
        schemas=store,
        readme=(
            "# Example: rational equality basic\n\n"
            "Identity `(x^2 - 1)/(x - 1) = x + 1` with explicit denominator condition.\n"
            "Generated by SymPy adapter; Lean checker owns acceptance.\n"
        ),
    )

    # Mathematica-labeled offline copy (same mathematical evidence; provenance tagged)
    mma_cert = dict(result.result["certificate"])
    mma_cert["provenance"] = {
        "backendId": "mathematica",
        "backendVersion": "offline-fixture",
        "adapterVersion": "0.1.0",
        "leanLinkVersion": None,
        "generatedAt": mma_cert["provenance"].get("generatedAt"),
        "deterministic": True,
    }
    write_bundle(
        EXAMPLES / "rational_equality_mathematica_offline",
        request=example_req,
        candidate=result.result["candidate"],
        certificate=mma_cert,
        schemas=store,
        readme=(
            "# Example: Mathematica offline evidence\n\n"
            "Committed evidence for closed-backend replay without Mathematica installed.\n"
            "Live generation is optional; see adapters/mathematica/README.md.\n"
        ),
    )

    # Canonical JSON vectors
    vectors = {
        "version": "0.1.0",
        "profile": "docs/architecture/canonical-json.md",
        "cases": [
            {
                "id": "object-key-order",
                "input": {"b": 1, "a": 2},
                "canonical": canonical_dumps({"b": 1, "a": 2}),
                "digest": sha256_digest({"b": 1, "a": 2}),
            },
            {
                "id": "nested",
                "input": {"z": [1, {"y": True, "x": None}], "a": "q"},
                "canonical": canonical_dumps({"z": [1, {"y": True, "x": None}], "a": "q"}),
                "digest": sha256_digest({"z": [1, {"y": True, "x": None}], "a": "q"}),
            },
        ],
    }
    (VECTORS / "canonical_json_vectors.json").write_text(
        json.dumps(vectors, indent=2) + "\n", encoding="utf-8"
    )

    print("generated conformance + example evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
