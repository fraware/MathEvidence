"""Exact-replay plugin forensic tests (no Lake required)."""

from __future__ import annotations

import copy

import pytest

from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.exact_replay.plugins.analytic_calculus import (
    generate_exact_analytic_calculus_module,
)
from adapters.common.exact_replay.plugins.finite_counterexample import (
    generate_exact_finite_counterexample_module,
)
from adapters.common.exact_replay.plugins.formal_rational_calculus import (
    generate_exact_formal_rational_calculus_module,
)
from adapters.common.exact_replay.plugins.linear_algebra import (
    generate_exact_linear_algebra_module,
)
from adapters.common.exact_replay.plugins.rational_equality import (
    generate_exact_rational_equality_module,
)
from agent.api.assurance_policy import (
    decide_exact_kernel_replay,
    map_claim_to_outcome,
)

DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)
BUNDLE = "sha256:" + ("c" * 64)


def _rat_request_cert(
    *,
    lhs: dict,
    rhs: dict,
    factors: list[dict] | None = None,
    assumptions: list[dict] | None = None,
    digest: str = DIGEST_A,
) -> tuple[dict, dict]:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [{"name": "x", "type": "Rat"}],
        "lhs": lhs,
        "rhs": rhs,
        "knownAssumptions": assumptions or [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": digest,
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "requestDigest": digest,
        "differenceNumerator": {"tag": "int", "value": "0"},
        "denominatorFactors": factors
        or [
            {
                "expr": {
                    "tag": "sub",
                    "left": {"tag": "var", "name": "x"},
                    "right": {"tag": "int", "value": "1"},
                },
                "role": "original_division",
            }
        ],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    return request, certificate


def test_rational_equal_reduced_and_unreduced_canonicalize() -> None:
    # (x^2-1)/(x-1) = x+1
    lhs = {
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
    }
    rhs = {
        "tag": "add",
        "left": {"tag": "var", "name": "x"},
        "right": {"tag": "int", "value": "1"},
    }
    request, certificate = _rat_request_cert(lhs=lhs, rhs=rhs)
    text = generate_exact_rational_equality_module(
        module_name="MathEvidence.Generated.Replay.rat_eq",
        declaration_name="rat_eq",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "OfflineFixtures" not in text
    assert "replaySound" in text
    assert "Expr.div" in text
    assert DIGEST_A in text

    # Unreduced rat literal 2/4 -> 1/2 in source
    request2, cert2 = _rat_request_cert(
        lhs={"tag": "rat", "num": "2", "den": "4"},
        rhs={"tag": "rat", "num": "1", "den": "2"},
        factors=[],
        digest=DIGEST_B,
    )
    text2 = generate_exact_rational_equality_module(
        module_name="MathEvidence.Generated.Replay.rat_canon",
        declaration_name="rat_canon",
        request=request2,
        certificate=cert2,
        candidate_bundle_digest=BUNDLE,
    )
    assert "Expr.rat (1 : Int) 2" in text2
    assert "Expr.rat (2 : Int) 4" not in text2


def test_rational_negatives_zero_unequal_den0_float() -> None:
    request, certificate = _rat_request_cert(
        lhs={"tag": "neg", "arg": {"tag": "int", "value": "3"}},
        rhs={"tag": "int", "value": "-3"},
        factors=[],
    )
    text = generate_exact_rational_equality_module(
        module_name="MathEvidence.Generated.Replay.rat_neg",
        declaration_name="rat_neg",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "Expr.neg" in text

    request0, cert0 = _rat_request_cert(
        lhs={"tag": "rat", "num": "0", "den": "5"},
        rhs={"tag": "int", "value": "0"},
        factors=[],
        digest=DIGEST_B,
    )
    text0 = generate_exact_rational_equality_module(
        module_name="MathEvidence.Generated.Replay.rat_zero",
        declaration_name="rat_zero",
        request=request0,
        certificate=cert0,
        candidate_bundle_digest=BUNDLE,
    )
    assert "Expr.rat (0 : Int) 1" in text0

    bad = copy.deepcopy(request)
    bad["lhs"] = {"tag": "rat", "num": "1", "den": "0"}
    with pytest.raises(ValueError, match="den=0"):
        generate_module(
            capability_id="algebra.rational_equality",
            request=bad,
            certificate=certificate,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.rat_bad",
            declaration_name="rat_bad",
        )

    float_req = copy.deepcopy(request)
    float_req["lhs"] = {"tag": "int", "value": 1.5}  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="float"):
        generate_module(
            capability_id="algebra.rational_equality",
            request=float_req,
            certificate=certificate,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.rat_float",
            declaration_name="rat_float",
        )


def test_rational_field_and_operator_mutation_change_hash() -> None:
    lhs = {"tag": "int", "value": "1"}
    rhs = {"tag": "int", "value": "1"}
    request, certificate = _rat_request_cert(lhs=lhs, rhs=rhs, factors=[])
    base = generate_module(
        capability_id="algebra.rational_equality",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.rat_base",
        declaration_name="rat_base",
    )
    mutated = copy.deepcopy(request)
    mutated["rhs"] = {"tag": "int", "value": "2"}
    other = generate_module(
        capability_id="algebra.rational_equality",
        request=mutated,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.rat_mut",
        declaration_name="rat_mut",
    )
    assert other.source_hash != base.source_hash
    op_mut = copy.deepcopy(request)
    op_mut["lhs"] = {
        "tag": "add",
        "left": {"tag": "int", "value": "1"},
        "right": {"tag": "int", "value": "0"},
    }
    op_other = generate_module(
        capability_id="algebra.rational_equality",
        request=op_mut,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.rat_op",
        declaration_name="rat_op",
    )
    assert op_other.source_hash != base.source_hash
    assert "OfflineFixtures" not in base.source_text


def _matrix(rows: list[list[tuple[str, str]]]) -> dict:
    return {
        "tag": "matrix",
        "rows": len(rows),
        "cols": len(rows[0]),
        "entries": [[{"tag": "rat", "num": n, "den": d} for n, d in row] for row in rows],
    }


def _rat(n: str, d: str = "1") -> dict:
    return {"tag": "rat", "num": n, "den": d}


def test_linear_algebra_ops_true_false_and_mutations() -> None:
    # inverse_witness true: diag(1/2,2) inverse diag(2,1/2)
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "operation": "inverse_witness",
        "matrix": _matrix([[("1", "2"), ("0", "1")], [("0", "1"), ("2", "1")]]),
        "requestedClaim": "witness",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": DIGEST_A,
    }
    cert = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "operation": "inverse_witness",
        "inverse": _matrix([[("2", "1"), ("0", "1")], [("0", "1"), ("1", "2")]]),
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    text = generate_exact_linear_algebra_module(
        module_name="MathEvidence.Generated.Replay.la_inv",
        declaration_name="la_inv",
        request=req,
        certificate=cert,
        candidate_bundle_digest=BUNDLE,
    )
    assert "operation = inverse_witness" in text
    assert ".inverseWitness" in text
    assert "OfflineFixtures" not in text

    # dimension mismatch
    bad = copy.deepcopy(cert)
    bad["inverse"] = _matrix([[("1", "1"), ("0", "1")]])
    with pytest.raises(ValueError, match="dimensions"):
        generate_module(
            capability_id="algebra.linear_algebra",
            request=req,
            certificate=bad,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.la_dim",
            declaration_name="la_dim",
        )

    # entry mutation changes hash
    base = generate_module(
        capability_id="algebra.linear_algebra",
        request=req,
        certificate=cert,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.la_base",
        declaration_name="la_base",
    )
    mut_req = copy.deepcopy(req)
    mut_req["matrix"]["entries"][0][0] = _rat("1", "3")
    mut_cert = copy.deepcopy(cert)
    other = generate_module(
        capability_id="algebra.linear_algebra",
        request=mut_req,
        certificate=mut_cert,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.la_mut",
        declaration_name="la_mut",
    )
    assert other.source_hash != base.source_hash

    # discriminant / operation mutation
    disc = copy.deepcopy(req)
    disc["operation"] = "det_identity"
    disc["requestedClaim"] = "soundResult"
    disc["claimedDet"] = _rat("-2")
    with pytest.raises(ValueError, match="operation"):
        generate_module(
            capability_id="algebra.linear_algebra",
            request=disc,
            certificate=cert,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.la_disc",
            declaration_name="la_disc",
        )

    float_req = copy.deepcopy(req)
    float_req["matrix"]["entries"][0][0] = {"tag": "rat", "num": 1.5, "den": "1"}
    with pytest.raises(ValueError, match="float"):
        generate_module(
            capability_id="algebra.linear_algebra",
            request=float_req,
            certificate=cert,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.la_float",
            declaration_name="la_float",
        )

    # system / kernel / det smoke
    sys_req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "operation": "system_solution",
        "matrix": _matrix([[("1", "1"), ("1", "1")], [("0", "1"), ("1", "1")]]),
        "rhs": [_rat("3"), _rat("2")],
        "requestedClaim": "witness",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": DIGEST_B,
    }
    sys_cert = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_B,
        "operation": "system_solution",
        "vector": [_rat("1"), _rat("2")],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    assert "systemSolution" in generate_exact_linear_algebra_module(
        module_name="MathEvidence.Generated.Replay.la_sys",
        declaration_name="la_sys",
        request=sys_req,
        certificate=sys_cert,
        candidate_bundle_digest=BUNDLE,
    )


def test_counterexample_refutation_polarity_and_guards() -> None:
    request = {
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
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": DIGEST_A,
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "logic.finite_counterexample",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "witness": {"assignment": [{"tag": "nat", "v": 2}]},
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    text = generate_exact_finite_counterexample_module(
        module_name="MathEvidence.Generated.Replay.cex_ok",
        declaration_name="cex_ok",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "outcome = refuted" in text
    assert "claimClass := .refutation" in text
    assert "OfflineFixtures" not in text
    assert map_claim_to_outcome(claim_class="refutation", claim_established="refutation") == "refuted"

    # non-violating / out-of-domain rejected at parse (type/domain checks)
    ood = copy.deepcopy(certificate)
    ood["witness"] = {"assignment": [{"tag": "nat", "v": 9}]}
    with pytest.raises(ValueError, match="out of nat domain"):
        generate_module(
            capability_id="logic.finite_counterexample",
            request=request,
            certificate=ood,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.cex_ood",
            declaration_name="cex_ood",
        )

    empty = copy.deepcopy(certificate)
    empty["witness"] = {"assignment": []}
    with pytest.raises(ValueError, match="no-witness"):
        generate_module(
            capability_id="logic.finite_counterexample",
            request=request,
            certificate=empty,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.cex_empty",
            declaration_name="cex_empty",
        )

    proved_req = copy.deepcopy(request)
    proved_req["requestedClaim"] = "candidate"
    with pytest.raises(ValueError, match="refutation|candidate"):
        generate_module(
            capability_id="logic.finite_counterexample",
            request=proved_req,
            certificate=certificate,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.cex_cand",
            declaration_name="cex_cand",
        )

    # mutated predicate changes hash
    base = generate_module(
        capability_id="logic.finite_counterexample",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.cex_base",
        declaration_name="cex_base",
    )
    mut = copy.deepcopy(request)
    mut["predicate"]["pred"]["right"]["v"]["v"] = 1
    other = generate_module(
        capability_id="logic.finite_counterexample",
        request=mut,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
        module_name="MathEvidence.Generated.Replay.cex_mut",
        declaration_name="cex_mut",
    )
    assert other.source_hash != base.source_hash


def test_formal_calculus_binds_tree_and_rejects_candidate_only() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.formal_rational_calculus",
        "capabilityVersion": "0.1.0",
        "operation": "derivative_candidate",
        "variables": [{"name": "x", "type": "Rat"}],
        "independentVar": "x",
        "expr": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
        "candidate": {
            "tag": "mul",
            "left": {"tag": "int", "value": "2"},
            "right": {"tag": "var", "name": "x"},
        },
        "domainConditions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 10000, "maxOutputBytes": 1048576},
        "requestDigest": DIGEST_A,
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.formal_rational_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "operation": "derivative_candidate",
        "domainConditions": [],
        "provenance": {"backendId": "test", "adapterVersion": "0.1.0"},
    }
    text = generate_exact_formal_rational_calculus_module(
        module_name="MathEvidence.Generated.Replay.calc_deriv",
        declaration_name="calc_deriv",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "formal_rational_calculus_not_analytic" in text
    assert ".derivativeCandidate" in text
    assert "replaySound" in text
    assert "OfflineFixtures" not in text

    cand = copy.deepcopy(request)
    cand["requestedClaim"] = "candidate"
    with pytest.raises(ValueError, match="candidate"):
        generate_module(
            capability_id="algebra.formal_rational_calculus",
            request=cand,
            certificate=certificate,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.calc_cand",
            declaration_name="calc_cand",
        )


def test_analytic_whitelist_and_unsupported_fail_closed() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "kind": "derivative",
        "source": {"tag": "mul", "lhs": {"tag": "variable", "idx": 0}, "rhs": {"tag": "variable", "idx": 0}},
        "target": {
            "tag": "add",
            "lhs": {
                "tag": "mul",
                "lhs": {"tag": "const", "value": "1"},
                "rhs": {"tag": "variable", "idx": 0},
            },
            "rhs": {
                "tag": "mul",
                "lhs": {"tag": "variable", "idx": 0},
                "rhs": {"tag": "const", "value": "1"},
            },
        },
        "requestDigest": DIGEST_A,
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "source": request["source"],
        "derivative": request["target"],
        "proof": {"tag": "mul", "p": {"tag": "variable"}, "q": {"tag": "variable"}},
        "obligations": [],
        "claimsCompleteness": False,
    }
    text = generate_exact_analytic_calculus_module(
        module_name="MathEvidence.Generated.Replay.an_prod",
        declaration_name="an_prod",
        request=request,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "checkDeriv_sound" in text
    assert "HasDerivAt" in text
    assert "OfflineFixtures" not in text

    within = copy.deepcopy(request)
    within["kind"] = "derivativeWithin"
    within_text = generate_exact_analytic_calculus_module(
        module_name="MathEvidence.Generated.Replay.an_within",
        declaration_name="an_within",
        request=within,
        certificate=certificate,
        candidate_bundle_digest=BUNDLE,
    )
    assert "checkDerivWithin_sound" in within_text
    assert "HasDerivWithinAt" in within_text
    assert "Set.univ" in within_text

    bad = copy.deepcopy(request)
    bad["kind"] = "numerical_estimate"
    with pytest.raises(ValueError, match="whitelist"):
        generate_module(
            capability_id="analysis.analytic_calculus",
            request=bad,
            certificate=certificate,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.an_bad",
            declaration_name="an_bad",
        )

    # kind mismatch between request and certificate must fail closed
    mismatched = copy.deepcopy(certificate)
    mismatched["kind"] = "antiderivative"
    with pytest.raises(ValueError, match="kind"):
        generate_module(
            capability_id="analysis.analytic_calculus",
            request=request,
            certificate=mismatched,
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.an_kind",
            declaration_name="an_kind",
        )

    # unbounded pow exponents are rejected
    huge = copy.deepcopy(request)
    huge["source"] = {
        "tag": "pow",
        "base": {"tag": "variable", "idx": 0},
        "exp": 1_000_001,
    }
    with pytest.raises(ValueError, match="maximum"):
        generate_module(
            capability_id="analysis.analytic_calculus",
            request=huge,
            certificate={**certificate, "source": huge["source"]},
            candidate_bundle_digest=BUNDLE,
            module_name="MathEvidence.Generated.Replay.an_pow",
            declaration_name="an_pow",
        )


def test_analytic_antideriv_and_ode_generate() -> None:
    """Newly enabled whitelist forms must render Soundness decls, not fixtures."""
    antideriv_req = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "kind": "antiderivative",
        "source": {"tag": "variable", "idx": 0},
        "target": {"tag": "const", "value": "1"},
        "requestDigest": DIGEST_A,
    }
    antideriv_cert = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "source": antideriv_req["source"],
        "derivative": antideriv_req["target"],
        "proof": {"tag": "variable"},
        "obligations": [],
        "claimsCompleteness": False,
    }
    text = generate_exact_analytic_calculus_module(
        module_name="MathEvidence.Generated.Replay.an_anti",
        declaration_name="an_anti",
        request=antideriv_req,
        certificate=antideriv_cert,
        candidate_bundle_digest=BUNDLE,
    )
    assert "checkAntideriv_sound" in text
    assert "OfflineFixtures" not in text

    ode_req = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "kind": "odeCandidate",
        "source": {"tag": "variable", "idx": 0},
        "target": {"tag": "const", "value": "1"},
        "initialConditions": [
            {
                "point": {"tag": "const", "value": "0"},
                "value": {"tag": "const", "value": "0"},
            }
        ],
        "requestDigest": DIGEST_A,
    }
    ode_cert = {
        "schemaVersion": "0.1.0",
        "capability": "analysis.analytic_calculus",
        "capabilityVersion": "0.1.0",
        "requestDigest": DIGEST_A,
        "solution": {"tag": "variable", "idx": 0},
        "rhs": {"tag": "const", "value": "1"},
        "derivProof": {"tag": "variable"},
        "initialConditions": ode_req["initialConditions"],
        "obligations": [],
        "claimsCompleteness": False,
    }
    ode_text = generate_exact_analytic_calculus_module(
        module_name="MathEvidence.Generated.Replay.an_ode",
        declaration_name="an_ode",
        request=ode_req,
        certificate=ode_cert,
        candidate_bundle_digest=BUNDLE,
    )
    assert "checkODE_sound" in ode_text
    assert "CandidateSolvesFirstOrderODE" in ode_text
    assert "OfflineFixtures" not in ode_text


def test_phase2_exact_binding_decisions() -> None:
    for cap in (
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "analysis.analytic_calculus",
    ):
        decision = decide_exact_kernel_replay(cap)
        assert decision.ok is True, cap
    # federated remain closed
    assert decide_exact_kernel_replay("logic.smt").ok is False
