"""Unit tests for adapters/common digests and framing."""

from __future__ import annotations

import json

import pytest

from adapters.common.canonical import (
    CanonicalJsonError,
    bind_request_digest,
    canonical_dumps,
    reject_duplicate_keys,
    sha256_digest,
    verify_request_digest,
)
from adapters.common.errors import AdapterError
from adapters.common.protocol import AdapterServer, CapabilityDescriptor, HandlerResult
from adapters.common.limits import ResourceTracker, ResourceLimits


def test_canonical_key_order() -> None:
    assert canonical_dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_digest_stable() -> None:
    d1 = sha256_digest({"z": 1, "a": [True, None]})
    d2 = sha256_digest({"a": [True, None], "z": 1})
    assert d1 == d2
    assert d1.startswith("sha256:")
    assert len(d1) == 7 + 64


def test_reject_duplicate_keys() -> None:
    with pytest.raises(CanonicalJsonError):
        reject_duplicate_keys('{"a":1,"a":2}')


def test_request_digest_roundtrip() -> None:
    req = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.rational_equality",
        "capabilityVersion": "0.1.0",
        "variables": [],
        "lhs": {"tag": "int", "value": "1"},
        "rhs": {"tag": "int", "value": "1"},
        "knownAssumptions": [],
        "requestedClaim": "soundResult",
        "resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 1024},
    }
    bound = bind_request_digest(req)
    assert verify_request_digest(bound) == bound["requestDigest"]
    bad = dict(bound)
    bad["requestDigest"] = "sha256:" + ("00" * 32)
    with pytest.raises(CanonicalJsonError):
        verify_request_digest(bad)


def test_adapter_server_initialize_compute() -> None:
    calls: list[str] = []

    def compute(params, tracker: ResourceTracker) -> HandlerResult:
        calls.append("compute")
        tracker.check()
        return HandlerResult({"ok": True, "requestDigest": "sha256:" + ("11" * 32)})

    server = AdapterServer(
        backend_id="test",
        backend_version="0",
        adapter_version="0.1.0",
        capabilities=[
            CapabilityDescriptor(
                id="algebra.rational_equality",
                version="0.1.0",
                claim_classes=["soundResult"],
                request_schema="rational-equality-request.schema.json",
                evidence_schema="rational-equality-certificate.schema.json",
            )
        ],
        compute=compute,
        limits=ResourceLimits(max_wall_time_ms=5000),
    )
    init = server.handle_message(
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    )
    assert init is not None and "result" in init
    resp = server.handle_message(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "compute",
                "params": {"request": {"resourcePolicy": {"maxWallTimeMs": 1000, "maxOutputBytes": 1024}}},
            }
        )
    )
    assert resp is not None and resp["result"]["ok"] is True
    assert calls == ["compute"]


def test_adapter_error_stable_code() -> None:
    with pytest.raises(ValueError):
        AdapterError(code="not_a_real_code", message="x")
