"""Cancel → process kill and resource-limit documentation smoke tests."""

from __future__ import annotations

import time
from pathlib import Path

from adapters.common.limits import (
    DEFAULT_MAX_CPU_TIME_MS,
    DEFAULT_MAX_MEMORY_BYTES,
    DEFAULT_MAX_WALL_TIME_MS,
    ResourceLimits,
)
from adapters.common.rpc_client import RpcClient, default_adapter_argv


ROOT = Path(__file__).resolve().parents[2]


def test_documented_default_limits() -> None:
    lim = ResourceLimits()
    assert lim.max_wall_time_ms == DEFAULT_MAX_WALL_TIME_MS
    assert lim.max_cpu_time_ms == DEFAULT_MAX_CPU_TIME_MS
    assert lim.max_memory_bytes == DEFAULT_MAX_MEMORY_BYTES
    assert lim.max_nesting_depth == 64


def test_cancel_and_kill_leaves_no_orphan() -> None:
    argv = default_adapter_argv("sympy", root=ROOT)
    client = RpcClient.spawn(argv, cwd=ROOT, limits=ResourceLimits(max_wall_time_ms=30_000))
    try:
        client.request("initialize", {})
        pid = client.proc.pid
        assert client.proc.poll() is None
        client.cancel_and_kill(grace_s=3.0)
        # Process must exit; poll() returns exit code, not None.
        deadline = time.monotonic() + 5.0
        while client.proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert client.proc.poll() is not None, f"orphan adapter pid={pid}"
    finally:
        if client.proc.poll() is None:
            client.proc.kill()
            client.proc.wait(timeout=5)
