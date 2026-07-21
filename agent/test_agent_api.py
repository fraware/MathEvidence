"""Unit tests for Agent API service (in-process)."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.common.canonical import bind_request_digest
from agent.api import service
from agent.sdk import list_capabilities_local


def test_list_capabilities_includes_placeholders() -> None:
    out = list_capabilities_local()
    ids = {c["id"] for c in out["capabilities"]}
    assert "algebra.rational_equality" in ids
    assert "algebra.linear_algebra" in ids
    assert "logic.finite_counterexample" in ids
    assert "algebra.formal_rational_calculus" in ids
    assert "algebra.groebner_membership" in ids


def test_compute_ideal_membership_sympy_writes_content_addressed_bundle() -> None:
    """Registry-driven Agent compute for ideal membership + CA bundle store."""
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.groebner_membership",
        "capabilityVersion": "0.1.0",
        "target": {
            "varCount": 1,
            "terms": [
                {"coefficient": 1, "exponents": [2]},
                {"coefficient": -1, "exponents": [0]},
            ],
        },
        "generators": [
            {
                "varCount": 1,
                "terms": [
                    {"coefficient": 1, "exponents": [1]},
                    {"coefficient": -1, "exponents": [0]},
                ],
            }
        ],
        "requestedClaim": "candidate",
    }
    out = service.op_compute_evidence(
        {
            "capability": "algebra.groebner_membership",
            "backend": "sympy",
            "request": request,
            "bundleId": "ideal_membership_agent_smoke",
        }
    )
    assert out["resultStatus"] == "computed", out
    assert out.get("backend") == "sympy" or (out.get("extra") or {}).get("backend") == "sympy"
    cert = out.get("certificate") or (out.get("extra") or {}).get("certificate") or {}
    assert cert.get("pythonMirrorAccepts") is True
    ref = out.get("bundleRef") or {}
    assert ref.get("capability") == "algebra.groebner_membership"
    assert ref.get("contentAddressed") is True or str(ref.get("bundleId", "")).startswith(
        "sha256_"
    )


def test_reject_unknown_capability() -> None:
    out = service.op_check_support({"capability": "nope.missing"})
    assert out["resultStatus"] == "unsupported"


def test_reject_shell_backend() -> None:
    out = service.op_compute_evidence(
        {
            "capability": "algebra.rational_equality",
            "backend": "bash",
            "request": {"schemaVersion": "0.1.0", "capability": "algebra.rational_equality"},
        }
    )
    assert out["resultStatus"] == "unsupported"


def test_open_and_replay_example_bundle() -> None:
    import shutil

    from agent.api.bundle_store import BundleStore

    from adapters.common.bundle import load_role_json

    root = Path(__file__).resolve().parents[1]
    example = root / "evidence" / "examples" / "rational_equality_basic"
    store = BundleStore.default(root)
    digest = load_role_json(example, "manifest")["requestDigest"]
    dest, bid = store.commit_content_addressed(example, request_digest=digest)
    try:
        opened = service.op_open_bundle({"bundleId": bid})
        assert opened.get("error") is None, opened
        assert opened["bundleRef"]["capability"] == "algebra.rational_equality"
        assert "resultStatus" in opened
        assert isinstance(opened["unresolvedObligations"], list)
        replayed = service.op_replay_bundle({"bundleId": bid})
        assert replayed.get("error") is None, replayed
        # Without Lean exe: tested. With Lean exe on rational: may be soundness_verified.
        assert replayed["resultStatus"] in {
            "tested",
            "computed",
            "soundness_verified",
        }
        if replayed["resultStatus"] == "soundness_verified":
            claim = replayed.get("claimEstablished") or (replayed.get("extra") or {}).get(
                "claimEstablished"
            )
            assert claim == "soundResult"
    finally:
        if dest.exists():
            shutil.rmtree(dest)


def test_hypothesis_lattice_never_claims_minimal() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "lhs": {
            "tag": "div",
            "num": {
                "tag": "sub",
                "left": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
                "right": {"tag": "int", "value": "1"},
            },
            "den": {
                "tag": "sub",
                "left": {"tag": "var", "name": "x"},
                "right": {"tag": "int", "value": "1"},
            },
        },
        "rhs": {
            "tag": "add",
            "left": {"tag": "var", "name": "x"},
            "right": {"tag": "int", "value": "1"},
        },
    }
    out = service.op_build_condition_lattice(
        {"request": request, "artifactId": "test_lat"}
    )
    assert out["resultStatus"] == "computed"
    lattice = out["lattice"]
    assert lattice["claimsMinimal"] is False
    assert out.get("authorityStatus") == "lean_checker_mirror"
    assert "c0" in lattice["recommendedInterface"] or lattice["sufficientSets"]


def test_conjecture_campaign_falsifies() -> None:
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
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    out = service.op_conjecture_campaign({"request": req, "familyId": "finite.nat_le_3"})
    assert out["resultStatus"] == "computed"
    assert out["episode"]["state"] == "falsified"


def test_list_operations_includes_hypothesis() -> None:
    ops = {o["id"] for o in service.op_list_operations()["operations"]}
    assert "propose_conditions" in ops
    assert "build_condition_lattice" in ops
    assert "conjecture_campaign" in ops
