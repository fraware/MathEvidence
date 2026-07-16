"""SageMath adapter smoke tests (fixture mode + offline LA assembly)."""

from __future__ import annotations

from adapters.common.canonical import bind_request_digest
from adapters.common.errors import AdapterError
from adapters.common.lean_mirrors import check_finite_counterexample, check_linear_algebra
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.schema_validate import SchemaStore
from adapters.sage import discover_runtime
from adapters.sage.adapter import (
    SageRuntime,
    check_support,
    compute_finite_counterexample,
    compute_linear_algebra,
    compute_rational_equality,
    la_certificate_from_sage_payload,
)


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


def test_la_certificate_from_sage_payload() -> None:
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
    raw = {
        "operation": "inverse_witness",
        "sageVersion": "test",
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
    cert = la_certificate_from_sage_payload(raw, req, req["requestDigest"])
    SchemaStore().validate("linear-algebra-certificate.schema.json", cert)
    assert cert["provenance"]["backendId"] == "sage"
    assert check_linear_algebra(req, cert) is True


def test_la_fixture_unavailable() -> None:
    req = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": "algebra.linear_algebra",
            "capabilityVersion": "0.1.0",
            "operation": "det_identity",
            "matrix": {
                "tag": "matrix",
                "rows": 2,
                "cols": 2,
                "entries": [
                    [{"tag": "rat", "num": "1", "den": "1"}, {"tag": "rat", "num": "0", "den": "1"}],
                    [{"tag": "rat", "num": "0", "den": "1"}, {"tag": "rat", "num": "1", "den": "1"}],
                ],
            },
            "claimedDet": {"tag": "rat", "num": "1", "den": "1"},
            "requestedClaim": "witness",
            "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 4096},
        }
    )
    try:
        compute_linear_algebra(
            req, ResourceTracker(ResourceLimits()), runtime=SageRuntime(False, None, "fixture", "t")
        )
        raise AssertionError("expected backend_unavailable")
    except AdapterError as exc:
        assert exc.code == "backend_unavailable"


def test_cex_live_enumeration() -> None:
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
    rt = SageRuntime(True, "/fake/sage", "live", "test")
    result = compute_finite_counterexample(
        req, ResourceTracker(ResourceLimits()), runtime=rt
    )
    cert = result.result["certificate"]
    SchemaStore().validate("finite-counterexample-certificate.schema.json", cert)
    assert cert["provenance"]["backendId"] == "sage"
    assert check_finite_counterexample(req, cert) is True
