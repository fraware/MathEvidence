"""SageMath adapter smoke tests (fixture mode)."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.errors import AdapterError
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.sage import discover_runtime
from adapters.sage.adapter import SageRuntime, check_support, compute_rational_equality


def test_fixture_mode_when_forced(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    rt = discover_runtime()
    assert rt.mode == "fixture"
    assert rt.available is False


def test_compute_unavailable_in_fixture() -> None:
    tracker = ResourceTracker(ResourceLimits())
    request = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.rational_equality",
            "capabilityVersion": "0.1.0",
            "variables": [{"name": "x", "type": "Rat"}],
            "lhs": {"tag": "var", "name": "x"},
            "rhs": {"tag": "var", "name": "x"},
            "knownAssumptions": [],
            "requestedClaim": "soundResult",
            "resourcePolicy": {"maxWallTimeMs": 5000, "maxOutputBytes": 65536},
        }
    )
    rt = SageRuntime(False, None, "fixture", "test")
    try:
        compute_rational_equality(request, tracker, runtime=rt)
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_check_support_reports_fixture(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ADAPTER_MODE", "fixture")
    tracker = ResourceTracker(ResourceLimits())
    out = check_support({"capability": "algebra.rational_equality"}, tracker)
    assert out.result["supported"] is False
    assert out.result["reasonCode"] == "backend_unavailable"
