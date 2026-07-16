"""Typed Python SDK for MathEvidence Agent API (operation-level tools only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from agent.api.operations import PROTOCOL_VERSION


@dataclass
class AgentClient:
    """HTTP client for the local Agent API server."""

    base_url: str = "http://127.0.0.1:8787"
    timeout_s: float = 60.0

    def _url(self, path: str, query: dict[str, str] | None = None) -> str:
        base = self.base_url.rstrip("/")
        if query:
            return f"{base}{path}?{urllib.parse.urlencode(query)}"
        return f"{base}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self._url(path, query),
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {exc.code}: {raw}") from exc
            return payload
        if not isinstance(payload, dict):
            raise RuntimeError("Agent API response must be a JSON object")
        return payload

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")

    def list_operations(self) -> dict[str, Any]:
        return self._request("GET", "/v1/operations")

    def list_capabilities(
        self, *, status: str | None = None, domain: str | None = None
    ) -> dict[str, Any]:
        query: dict[str, str] = {}
        if status:
            query["status"] = status
        if domain:
            query["domain"] = domain
        return self._request("GET", "/v1/capabilities", query=query or None)

    def check_support(
        self,
        *,
        capability: str,
        capability_version: str | None = None,
        backend: str | None = None,
        requested_claim: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"capability": capability}
        if capability_version:
            body["capabilityVersion"] = capability_version
        if backend:
            body["backend"] = backend
        if requested_claim:
            body["requestedClaim"] = requested_claim
        return self._request("POST", "/v1/check-support", body=body)

    def compute_evidence(
        self,
        *,
        capability: str,
        backend: str,
        request: dict[str, Any],
        write_bundle_to: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "capability": capability,
            "backend": backend,
            "request": request,
        }
        if write_bundle_to:
            body["writeBundleTo"] = write_bundle_to
        return self._request("POST", "/v1/compute", body=body)

    def open_bundle(self, path: str) -> dict[str, Any]:
        return self._request("POST", "/v1/bundles/open", body={"path": path})

    def replay_bundle(self, path: str) -> dict[str, Any]:
        return self._request("POST", "/v1/bundles/replay", body={"path": path})


# In-process helpers (no HTTP) for tests / offline agents.
def list_capabilities_local(**kwargs: Any) -> dict[str, Any]:
    from agent.api import service

    return service.op_list_capabilities(**kwargs)


def check_support_local(body: dict[str, Any]) -> dict[str, Any]:
    from agent.api import service

    return service.op_check_support(body)


def open_bundle_local(path: str) -> dict[str, Any]:
    from agent.api import service

    return service.op_open_bundle({"path": path})


def replay_bundle_local(path: str) -> dict[str, Any]:
    from agent.api import service

    return service.op_replay_bundle({"path": path})


__all__ = [
    "PROTOCOL_VERSION",
    "AgentClient",
    "check_support_local",
    "list_capabilities_local",
    "open_bundle_local",
    "replay_bundle_local",
]
