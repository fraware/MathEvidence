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
    }
