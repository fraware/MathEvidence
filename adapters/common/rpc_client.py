"""JSON-RPC 2.0 client over a stdio subprocess (ADR 0003)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.common.errors import AdapterError, stable_error
from adapters.common.limits import ResourceLimits


@dataclass
class RpcClient:
    """Newline-delimited JSON-RPC client for one adapter process."""

    proc: subprocess.Popen[str]
    limits: ResourceLimits
    _next_id: int = 1

    @classmethod
    def spawn(
        cls,
        argv: list[str],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        limits: ResourceLimits | None = None,
    ) -> RpcClient:
        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(cwd) if cwd is not None else None,
                env=env,
            )
        except OSError as exc:
            raise stable_error(
                "backend_unavailable", f"failed to spawn adapter: {exc}"
            ) from exc
        return cls(proc=proc, limits=limits or ResourceLimits())

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                self.request("shutdown", {})
            except AdapterError:
                pass
            try:
                self.proc.terminate()
            except OSError:
                pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()

    def __enter__(self) -> RpcClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        if self.proc.stdin is None or self.proc.stdout is None:
            raise stable_error("backend_unavailable", "adapter stdio closed")
        msg_id = self._next_id
        self._next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params or {},
        }
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        if len(line.encode("utf-8")) > self.limits.max_request_bytes:
            raise stable_error("resource_limit_exceeded", "RPC request too large")
        try:
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
        except OSError as exc:
            raise stable_error("backend_unavailable", f"write failed: {exc}") from exc
        while True:
            raw = self.proc.stdout.readline()
            if not raw:
                err = ""
                if self.proc.stderr is not None:
                    err = self.proc.stderr.read()
                raise stable_error(
                    "backend_unavailable",
                    f"adapter closed stdout during {method}: {err}",
                )
            text = raw.strip()
            if not text:
                continue
            if len(text.encode("utf-8")) > self.limits.max_output_bytes:
                raise stable_error("resource_limit_exceeded", "RPC response too large")
            try:
                msg = json.loads(text)
            except json.JSONDecodeError as exc:
                raise stable_error(
                    "malformed_evidence", f"invalid JSON from adapter: {exc}"
                ) from exc
            if msg.get("id") != msg_id:
                # Skip unrelated notifications / out-of-order noise.
                continue
            if "error" in msg:
                err = msg["error"]
                data = err.get("data", {}) if isinstance(err, dict) else {}
                code = data.get("errorCode") if isinstance(data, dict) else None
                message = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                raise stable_error(
                    str(code or "backend_crash"),
                    message,
                    details=err if isinstance(err, dict) else {"error": err},
                )
            return msg.get("result")


def default_adapter_argv(backend: str, *, root: Path) -> list[str]:
    """Fixed argv for known backends (no shell interpolation)."""
    py = sys.executable
    if backend == "sympy":
        return [py, "-m", "adapters.sympy"]
    if backend == "mathematica":
        return [py, "-m", "adapters.mathematica"]
    if backend == "sage":
        return [py, "-m", "adapters.sage"]
    raise stable_error("backend_unsupported", f"unknown backend: {backend}")
