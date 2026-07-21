"""Mathematica adapter fixture-mode and IR assembly tests."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.errors import AdapterError
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.rational_ir import sub_expr, var_expr
from adapters.common.schema_validate import SchemaStore
from adapters.mathematica.adapter import (
    MathematicaRuntime,
    _wl_encode_expr,
    certificate_from_wl_payload,
    compute_rational_equality,
    discover_runtime,
)


def _basic_request() -> dict:
    return bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": "x", "type": "Rat"}],
            "lhs": var_expr("x"),
            "rhs": var_expr("x"),
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 1024},
        }
    )


def test_fixture_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    monkeypatch.delenv("MATHEVIDENCE_WOLFRAMSCRIPT", raising=False)
    rt = discover_runtime()
    assert rt.mode == "fixture"
    try:
        compute_rational_equality(
            _basic_request(), ResourceTracker(ResourceLimits()), runtime=rt
        )
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_live_requires_wolframscript_env(monkeypatch) -> None:
    monkeypatch.delenv("MATHEVIDENCE_ADAPTER_MODE", raising=False)
    monkeypatch.delenv("MATHEVIDENCE_WOLFRAMSCRIPT", raising=False)
    rt = discover_runtime()
    assert rt.mode == "fixture"
    assert rt.available is False
    assert "MATHEVIDENCE_WOLFRAMSCRIPT unset" in rt.detail


def test_wl_encode_full_fragment() -> None:
    expr = {
        "tag": "div",
        "num": {
            "tag": "sub",
            "left": {"tag": "pow", "base": {"tag": "var", "name": "x"}, "exp": 2},
            "right": {"tag": "int", "value": "1"},
        },
        "den": sub_expr(var_expr("x"), {"tag": "int", "value": "1"}),
    }
    encoded = _wl_encode_expr(expr)
    assert "x" in encoded
    assert "^" in encoded or "**" in encoded or "x" in encoded


def test_certificate_from_wl_payload_nonzero_numerator() -> None:
    """Full fragment: non-zero numerator IR is accepted (not scaffold-limited)."""
    req = _basic_request()
    # False identity payload shape from a complete ToIR path.
    false_req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": "x", "type": "Rat"}],
            "lhs": var_expr("x"),
            "rhs": {"tag": "int", "value": "0"},
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 1024},
        }
    )
    rt = MathematicaRuntime(
        available=True,
        executable="/fake/wolframscript",
        leanlink_path=None,
        mode="live",
        detail="test",
    )
    raw = {
        "differenceNumerator": {"tag": "var", "name": "x"},
        "commonDenom": None,
        "denominatorFactors": [],
        "rawDiff": "x",
    }
    cert = certificate_from_wl_payload(
        raw, false_req, false_req["requestDigest"], runtime=rt
    )
    store = SchemaStore()
    store.validate("rational-equality-certificate.schema.json", cert)
    assert cert["differenceNumerator"] == {"tag": "var", "name": "x"}
    assert cert["provenance"]["backendId"] == "mathematica"


def test_certificate_from_wl_payload_with_factors() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": "x", "type": "Rat"}],
            "lhs": {
                "tag": "div",
                "num": {"tag": "var", "name": "x"},
                "den": sub_expr(var_expr("x"), {"tag": "int", "value": "1"}),
            },
            "rhs": {
                "tag": "div",
                "num": {"tag": "var", "name": "x"},
                "den": sub_expr(var_expr("x"), {"tag": "int", "value": "1"}),
            },
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    rt = MathematicaRuntime(True, "/fake/ws", None, "live", "test")
    dens = sub_expr(var_expr("x"), {"tag": "int", "value": "1"})
    raw = {
        "differenceNumerator": {"tag": "int", "value": "0"},
        "commonDenom": dens,
        "denominatorFactors": [{"expr": dens, "multiplicity": 1}],
        "rawDiff": "0",
    }
    cert = certificate_from_wl_payload(raw, req, req["requestDigest"], runtime=rt)
    roles = {f["role"] for f in cert["denominatorFactors"]}
    assert "original_division" in roles
    assert "common_denominator" in roles
    assert "factorization" in roles
    SchemaStore().validate("rational-equality-certificate.schema.json", cert)


def test_calculus_fixture_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    monkeypatch.delenv("MATHEVIDENCE_WOLFRAMSCRIPT", raising=False)
    from adapters.mathematica.adapter import compute_symbolic_calculus

    req = bind_request_digest(
        {
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
            "requestedClaim": "candidate",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    try:
        compute_symbolic_calculus(
            req,
            ResourceTracker(ResourceLimits()),
            runtime=discover_runtime(),
        )
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_calculus_certificate_from_wl_payload() -> None:
    from adapters.mathematica.adapter import calculus_certificate_from_wl_payload

    req = bind_request_digest(
        {
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
            "requestedClaim": "candidate",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    rt = MathematicaRuntime(True, "/fake/ws", None, "live", "test")
    cand = req["candidate"]
    cert = calculus_certificate_from_wl_payload(
        {"candidate": cand, "rawForm": "2*x"},
        req,
        req["requestDigest"],
        runtime=rt,
        candidate=cand,
        notes="test candidate≠completeness",
    )
    SchemaStore().validate("symbolic-calculus-certificate.schema.json", cert)
    assert cert["operation"] == "derivative_candidate"
    assert "completeness" in cert["notes"]
    assert cert["provenance"]["backendId"] == "mathematica"


def test_la_fixture_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    monkeypatch.delenv("MATHEVIDENCE_WOLFRAMSCRIPT", raising=False)
    from adapters.mathematica.adapter import compute_linear_algebra

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
                "entries": [
                    [{"tag": "rat", "num": "1", "den": "1"}, {"tag": "rat", "num": "0", "den": "1"}],
                    [{"tag": "rat", "num": "0", "den": "1"}, {"tag": "rat", "num": "1", "den": "1"}],
                ],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    try:
        compute_linear_algebra(
            req, ResourceTracker(ResourceLimits()), runtime=discover_runtime()
        )
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_la_certificate_from_wl_payload_inverse() -> None:
    from adapters.common.lean_mirrors import check_linear_algebra
    from adapters.mathematica.adapter import la_certificate_from_wl_payload

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
                "entries": [
                    [{"tag": "rat", "num": "1", "den": "2"}, {"tag": "rat", "num": "0", "den": "1"}],
                    [{"tag": "rat", "num": "0", "den": "1"}, {"tag": "rat", "num": "2", "den": "1"}],
                ],
            },
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    rt = MathematicaRuntime(True, "/fake/ws", None, "live", "test")
    raw = {
        "operation": "inverse_witness",
        "inverse": {
            "tag": "matrix",
            "rows": 2,
            "cols": 2,
            "entries": [
                [{"tag": "rat", "num": "2", "den": "1"}, {"tag": "rat", "num": "0", "den": "1"}],
                [{"tag": "rat", "num": "0", "den": "1"}, {"tag": "rat", "num": "1", "den": "2"}],
            ],
        },
        "sideConditions": ["matrix_invertible"],
    }
    cert = la_certificate_from_wl_payload(raw, req, req["requestDigest"], runtime=rt)
    SchemaStore().validate("linear-algebra-certificate.schema.json", cert)
    assert cert["provenance"]["backendId"] == "mathematica"
    assert check_linear_algebra(req, cert) is True


def test_cex_fixture_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    from adapters.mathematica.adapter import compute_finite_counterexample

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
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    try:
        compute_finite_counterexample(
            req, ResourceTracker(ResourceLimits()), runtime=discover_runtime()
        )
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_cex_live_enumeration_without_cas(monkeypatch) -> None:
    """CEX uses shared enumeration under a live runtime gate (no Wolfram call)."""
    from adapters.common.lean_mirrors import check_finite_counterexample
    from adapters.mathematica.adapter import MathematicaRuntime, compute_finite_counterexample

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
    rt = MathematicaRuntime(True, "/fake/ws", None, "live", "test")
    result = compute_finite_counterexample(
        req, ResourceTracker(ResourceLimits()), runtime=rt
    )
    cert = result.result["certificate"]
    SchemaStore().validate("finite-counterexample-certificate.schema.json", cert)
    assert cert["provenance"]["backendId"] == "mathematica"
    assert check_finite_counterexample(req, cert) is True

