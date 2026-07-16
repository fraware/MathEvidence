# Product 07 — Capability Registry — acceptance report

**Workstream:** R5  
**Spec:** [docs/products/07_CAPABILITY_REGISTRY.md](../../products/07_CAPABILITY_REGISTRY.md)  
**Date:** 2026-07-16

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Every stable capability schema-valid + conformance-backed | **N/A / PASS discipline** | No capability is `stable` yet (R2 OPEN). Experimental entries validate via `just registry-validate` |
| 2 | Agents select tools without parsing prose | **PASS** | `list_capabilities` / `check_support` Agent API |
| 3 | Unsupported combinations rejected before backend invocation | **PASS** | `op_check_support` + compute gate |
| 4 | Registry updates versioned and reviewed by owners | **PASS (process)** | Capability JSON semantic versions + GOVERNANCE; no silent unversioned flips |
| 5 | Historical bundle replay independent of mutable registry | **PASS** | Manifest/request `capabilityVersion` pins; `scripts/test_registry_historical_replay.py` mutates current registry entry and still replays pinned bundles |

## Overall engineering gate

**PASS** for R5. Capability `stable` promotion remains blocked on R2 human gates.
