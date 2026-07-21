"""Forensic: registry advertised backends must match Agent executable routing.

P0-9 — If registry claims live Mathematica/Sage for a capability, Agent compute
must route it (or registry must downgrade the claim).
"""

from __future__ import annotations

import json
from pathlib import Path

from agent.api import service

ROOT = Path(__file__).resolve().parents[2]
CAP_DIR = ROOT / "registry" / "capabilities"

# Agent thin compute currently only wires non-rational caps to sympy
# (service.py). Registry must not advertise higher support than routing.
LIVE_LEVELS = {"live_generator_complete", "conformance_verified"}


def _registry_backends(cap_id: str) -> dict[str, str]:
    path = CAP_DIR / f"{cap_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    backends = (data.get("supportClaims") or {}).get("backends") or []
    return {b["id"]: b.get("supportLevel", "declared") for b in backends}


def test_registry_does_not_overclaim_agent_routing_for_la() -> None:
    levels = _registry_backends("algebra.linear_algebra")
    for backend in ("mathematica", "sage"):
        level = levels.get(backend)
        if level in LIVE_LEVELS:
            probe = service.op_compute_evidence(
                {
                    "capability": "algebra.linear_algebra",
                    "backend": backend,
                    "request": {
                        "schemaVersion": "0.1.0",
                        "capability": "algebra.linear_algebra",
                        "capabilityVersion": "0.1.0",
                    },
                }
            )
            assert probe["resultStatus"] != "unsupported", (
                f"P0-9: registry claims {backend}={level} for linear_algebra but "
                f"Agent returns unsupported: {probe.get('error')}"
            )


def test_registry_does_not_overclaim_agent_routing_for_cex() -> None:
    levels = _registry_backends("logic.finite_counterexample")
    for backend in ("mathematica", "sage"):
        level = levels.get(backend)
        if level in LIVE_LEVELS:
            probe = service.op_compute_evidence(
                {
                    "capability": "logic.finite_counterexample",
                    "backend": backend,
                    "request": {
                        "schemaVersion": "0.1.0",
                        "capability": "logic.finite_counterexample",
                        "capabilityVersion": "0.1.0",
                    },
                }
            )
            assert probe["resultStatus"] != "unsupported", (
                f"P0-9: registry claims {backend}={level} for finite_counterexample "
                f"but Agent returns unsupported: {probe.get('error')}"
            )


def test_sage_rational_is_not_advertised() -> None:
    """Spec 05: Sage rational must be implemented+conformance OR removed from support."""
    levels = _registry_backends("algebra.rational_equality")
    sage = levels.get("sage")
    assert sage is None, (
        f"Sage rational must be un-advertised (removed from supportClaims); got {sage}"
    )
