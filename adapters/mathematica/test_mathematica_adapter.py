"""Mathematica adapter fixture-mode tests."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.errors import AdapterError
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.rational_ir import var_expr
from adapters.mathematica.adapter import compute_rational_equality, discover_runtime


def test_fixture_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    rt = discover_runtime()
    assert rt.mode == "fixture"
    req = bind_request_digest(
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
    try:
        compute_rational_equality(req, ResourceTracker(ResourceLimits()), runtime=rt)
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"
