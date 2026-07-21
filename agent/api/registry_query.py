"""Load capability/backend registry for Agent API discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = REPO_ROOT / "registry"


def load_capabilities() -> list[dict[str, Any]]:
    caps: list[dict[str, Any]] = []
    for path in sorted((REGISTRY_DIR / "capabilities").glob("*.json")):
        caps.append(json.loads(path.read_text(encoding="utf-8")))
    return caps


def load_backends() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted((REGISTRY_DIR / "backends").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out[data["id"]] = data
    return out


def find_capability(capability_id: str) -> dict[str, Any] | None:
    for cap in load_capabilities():
        if cap["id"] == capability_id:
            return cap
    return None


def capability_public_summary(cap: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": cap["id"],
        "version": cap["version"],
        "status": cap["status"],
        "domain": cap["domain"],
        "claimClasses": list(cap["claimClasses"]),
        "requestSchema": cap.get("requestSchema"),
        "evidenceSchema": cap.get("evidenceSchema"),
        "supportClaims": cap.get("supportClaims", {}),
        "role": cap.get("role"),
        "externalSearchEssential": cap.get("externalSearchEssential"),
        "lifecycle": cap.get("lifecycle"),
    }


# Agent compute is implemented for these owned capabilities only.
_COMPUTE_CAPABILITIES = frozenset(
    {
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "algebra.groebner_membership",
    }
)

_ROUTABLE_SUPPORT_LEVELS = frozenset(
    {
        "implemented",
        "conformance_verified",
        "offline_fixtures_passing",
        "live_generator_complete",
    }
)


def capability_backend_support_level(
    cap: dict[str, Any], backend_id: str
) -> str | None:
    backends = (cap.get("supportClaims") or {}).get("backends") or []
    for entry in backends:
        if isinstance(entry, dict) and entry.get("id") == backend_id:
            level = entry.get("supportLevel")
            return level if isinstance(level, str) else None
    return None


def registry_allows_compute(capability_id: str, backend_id: str) -> tuple[bool, str]:
    """Return whether registry + Agent compute surface allow this pair."""
    if capability_id not in _COMPUTE_CAPABILITIES:
        return False, f"compute not implemented for {capability_id} in Agent API"
    cap = find_capability(capability_id)
    if cap is None:
        return False, f"unknown capability: {capability_id}"
    if cap.get("status") not in (None, "experimental", "candidate", "stable"):
        return False, f"capability status not dispatchable: {cap.get('status')}"
    level = capability_backend_support_level(cap, backend_id)
    if level is None:
        return False, f"backend {backend_id} not declared for {capability_id}"
    if level == "declared" or level == "placeholder":
        return (
            False,
            f"backend {backend_id} is {level}-only for {capability_id} "
            "(not executable via Agent compute)",
        )
    if level not in _ROUTABLE_SUPPORT_LEVELS:
        return False, f"backend {backend_id} supportLevel={level} not routable"
    backends = load_backends()
    be = backends.get(backend_id)
    if be is None:
        return False, f"backend registry entry missing: {backend_id}"
    supported = be.get("supportedCapabilities") or []
    for entry in supported:
        if isinstance(entry, dict) and entry.get("id") == capability_id:
            be_level = entry.get("supportLevel", "declared")
            if be_level in ("declared", "placeholder"):
                return (
                    False,
                    f"backend {backend_id} lists {capability_id} as {be_level}",
                )
            return True, "ok"
    return False, f"backend {backend_id} does not list capability {capability_id}"
