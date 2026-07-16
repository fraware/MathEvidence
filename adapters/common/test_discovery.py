"""Tests for discovery orchestration and JSON-RPC client."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.common.canonical import bind_request_digest, verify_request_digest
from adapters.common.discovery import discover_rational_equality, discovery_env_enabled
from adapters.common.rpc_client import RpcClient, default_adapter_argv

ROOT = Path(__file__).resolve().parents[2]
BASIC = ROOT / "evidence" / "examples" / "rational_equality_basic" / "request.json"


def test_discovery_env_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MATHEVIDENCE_DISCOVERY", raising=False)
    assert discovery_env_enabled() is False
    monkeypatch.setenv("MATHEVIDENCE_DISCOVERY", "1")
    assert discovery_env_enabled() is True


def test_discover_direct_sympy_writes_bundle(tmp_path: Path) -> None:
    request = json.loads(BASIC.read_text(encoding="utf-8"))
    out = tmp_path / "bundle"
    result = discover_rational_equality(
        request, backend="sympy", bundle_dir=out, use_rpc=False
    )
    assert result.via_rpc is False
    assert (out / "certificate.json").is_file()
    assert (out / "request.json").is_file()
    assert result.certificate.get("requestDigest") == request["requestDigest"]
    assert result.warnings == [] or all(isinstance(w, str) for w in result.warnings)


def test_discover_rpc_sympy(tmp_path: Path) -> None:
    request = json.loads(BASIC.read_text(encoding="utf-8"))
    out = tmp_path / "bundle_rpc"
    result = discover_rational_equality(
        request, backend="sympy", bundle_dir=out, use_rpc=True
    )
    assert (out / "certificate.json").is_file()
    # May fall back to direct if RPC fails; either path must yield a certificate.
    assert "denominatorFactors" in result.certificate


def test_rpc_client_initialize_shutdown() -> None:
    argv = default_adapter_argv("sympy", root=ROOT)
    with RpcClient.spawn(argv, cwd=ROOT) as client:
        init = client.request("initialize", {"client": "test", "version": "0"})
        assert init["backendId"] == "sympy"
        caps = client.request("listCapabilities", {})
        assert any(c["id"] == "algebra.rational_equality" for c in caps["capabilities"])


def test_bind_request_matches_committed_basic() -> None:
    request = json.loads(BASIC.read_text(encoding="utf-8"))
    digest = request.pop("requestDigest")
    rebound = bind_request_digest(request)
    assert rebound["requestDigest"] == digest
    verify_request_digest(rebound)
