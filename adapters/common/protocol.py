"""JSON-RPC 2.0 adapter server (ADR 0003)."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TextIO

from adapters.common.canonical import reject_duplicate_keys, sha256_digest
from adapters.common.errors import AdapterError, stable_error
from adapters.common.framing import iter_ndjson_messages, write_ndjson_message
from adapters.common.limits import ResourceLimits, ResourceTracker

PROTOCOL_VERSION = "0.1.0"

METHODS = (
    "initialize",
    "listCapabilities",
    "checkSupport",
    "compute",
    "proposeConditions",
    "cancel",
    "shutdown",
)


@dataclass(frozen=True)
class CapabilityDescriptor:
    id: str
    version: str
    claim_classes: list[str]
    request_schema: str
    evidence_schema: str
    deterministic: bool = True
    notes: list[str] = field(default_factory=list)


@dataclass
class HandlerResult:
    result: dict[str, Any]
    resource_usage: dict[str, int] | None = None


ComputeFn = Callable[[dict[str, Any], ResourceTracker], HandlerResult]
SupportFn = Callable[[dict[str, Any], ResourceTracker], HandlerResult]
ProposeConditionsFn = Callable[[dict[str, Any], ResourceTracker], HandlerResult]


class AdapterServer:
    """Stdio JSON-RPC server for one backend adapter process."""

    def __init__(
        self,
        *,
        backend_id: str,
        backend_version: str,
        adapter_version: str,
        capabilities: list[CapabilityDescriptor],
        compute: ComputeFn,
        check_support: SupportFn | None = None,
        propose_conditions: ProposeConditionsFn | None = None,
        limits: ResourceLimits | None = None,
        extra_initialize: dict[str, Any] | None = None,
    ) -> None:
        self.backend_id = backend_id
        self.backend_version = backend_version
        self.adapter_version = adapter_version
        self.capabilities = {c.id: c for c in capabilities}
        self._compute = compute
        self._check_support = check_support
        self._propose_conditions = propose_conditions
        self.limits = limits or ResourceLimits()
        self.extra_initialize = extra_initialize or {}
        self._initialized = False
        self._shutdown = False
        self._active: ResourceTracker | None = None
        self._request_count = 0

    def _identity(self) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "backendId": self.backend_id,
            "backendVersion": self.backend_version,
            "adapterVersion": self.adapter_version,
        }

    def handle_message(self, text: str) -> dict[str, Any] | None:
        try:
            payload = reject_duplicate_keys(text)
        except Exception as exc:  # noqa: BLE001 — parse boundary
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"parse error: {exc}",
                },
            }

        if not isinstance(payload, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "invalid request: not an object"},
            }

        req_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", {})

        if payload.get("jsonrpc") != "2.0":
            return self._error_response(
                req_id,
                -32600,
                "invalid request: jsonrpc must be '2.0'",
            )
        if not isinstance(method, str):
            return self._error_response(req_id, -32600, "invalid request: method required")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return self._error_response(req_id, -32602, "params must be an object")

        # Notifications (no id) are acknowledged silently except shutdown.
        is_notification = "id" not in payload

        try:
            result = self._dispatch(method, params)
        except AdapterError as exc:
            if is_notification:
                return None
            return {"jsonrpc": "2.0", "id": req_id, "error": exc.to_rpc_error()}
        except Exception as exc:  # noqa: BLE001
            if is_notification:
                return None
            err = stable_error("backend_crash", f"internal error: {exc}")
            return {"jsonrpc": "2.0", "id": req_id, "error": err.to_rpc_error()}

        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "shutdown":
            self._shutdown = True
            if self._active is not None:
                self._active.cancelled = True
            return {**self._identity(), "shutdown": True}

        if method == "cancel":
            if self._active is not None:
                self._active.cancelled = True
            return {**self._identity(), "cancelled": True}

        if method == "initialize":
            self._initialized = True
            return {
                **self._identity(),
                "capabilities": [self._cap_public(c) for c in self.capabilities.values()],
                **self.extra_initialize,
            }

        if not self._initialized and method != "initialize":
            raise stable_error(
                "schema_version_unsupported",
                "adapter not initialized; call initialize first",
            )

        if method == "listCapabilities":
            return {
                **self._identity(),
                "capabilities": [self._cap_public(c) for c in self.capabilities.values()],
            }

        if method == "checkSupport":
            tracker = ResourceTracker(self.limits)
            self._active = tracker
            try:
                if self._check_support is not None:
                    hr = self._check_support(params, tracker)
                else:
                    hr = self._default_check_support(params, tracker)
                return self._wrap_result(hr)
            finally:
                self._active = None

        if method == "compute":
            policy = None
            request = params.get("request")
            if isinstance(request, dict):
                policy = request.get("resourcePolicy")
            limits = ResourceLimits.from_policy(
                policy if isinstance(policy, dict) else None
            )
            # Keep process defaults as upper bounds.
            limits = ResourceLimits(
                max_wall_time_ms=min(limits.max_wall_time_ms, self.limits.max_wall_time_ms),
                max_output_bytes=min(limits.max_output_bytes, self.limits.max_output_bytes),
                max_request_bytes=self.limits.max_request_bytes,
                max_nesting_depth=self.limits.max_nesting_depth,
            )
            tracker = ResourceTracker(limits)
            self._active = tracker
            try:
                hr = self._compute(params, tracker)
                tracker.check()
                return self._wrap_result(hr)
            finally:
                self._active = None

        if method == "proposeConditions":
            if self._propose_conditions is None:
                raise stable_error(
                    "backend_unsupported",
                    "proposeConditions not implemented by this adapter",
                )
            tracker = ResourceTracker(self.limits)
            self._active = tracker
            try:
                hr = self._propose_conditions(params, tracker)
                tracker.check()
                return self._wrap_result(hr)
            finally:
                self._active = None

        raise stable_error(
            "backend_unsupported",
            f"unknown method: {method}",
            details={"method": method, "known": list(METHODS)},
        )

    def _default_check_support(
        self, params: dict[str, Any], tracker: ResourceTracker
    ) -> HandlerResult:
        tracker.check()
        cap_id = params.get("capability")
        version = params.get("capabilityVersion")
        if not isinstance(cap_id, str) or cap_id not in self.capabilities:
            return HandlerResult(
                {
                    "supported": False,
                    "reasonCode": "backend_unsupported",
                    "message": f"capability not offered: {cap_id!r}",
                }
            )
        cap = self.capabilities[cap_id]
        if isinstance(version, str) and version != cap.version:
            return HandlerResult(
                {
                    "supported": False,
                    "reasonCode": "schema_version_unsupported",
                    "message": f"capability version {version} != {cap.version}",
                }
            )
        return HandlerResult({"supported": True, "capability": self._cap_public(cap)})

    def _cap_public(self, cap: CapabilityDescriptor) -> dict[str, Any]:
        return {
            "id": cap.id,
            "version": cap.version,
            "claimClasses": cap.claim_classes,
            "requestSchema": cap.request_schema,
            "evidenceSchema": cap.evidence_schema,
            "deterministic": cap.deterministic,
            "notes": list(cap.notes),
        }

    def _wrap_result(self, hr: HandlerResult) -> dict[str, Any]:
        out = {**self._identity(), **hr.result}
        if hr.resource_usage:
            out["resourceUsage"] = hr.resource_usage
        if "requestDigest" not in out and isinstance(hr.result.get("request"), dict):
            # Prefer explicit digest from compute handlers.
            pass
        return out

    def _error_response(
        self, req_id: Any, code: int, message: str
    ) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def serve(
        self,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> int:
        """Run until EOF or shutdown. Returns process exit code."""
        in_stream = stdin or sys.stdin
        out_stream = stdout or sys.stdout
        for text in iter_ndjson_messages(in_stream, limits=self.limits):
            response = self.handle_message(text)
            if response is not None:
                encoded = json.dumps(response, separators=(",", ":"), ensure_ascii=False)
                write_ndjson_message(encoded, stream=out_stream, limits=self.limits)
            if self._shutdown:
                break
        return 0


def envelope_digest(obj: dict[str, Any]) -> str:
    """Helper for handlers that need a digest over an arbitrary object."""
    return sha256_digest(obj)
