# ADR 0004 — Wolframscript is the v0.1 Mathematica live transport

## Decision

For v0.1, the supported live Mathematica transport is `MATHEVIDENCE_WOLFRAMSCRIPT` / wolframscript driving the JSON-RPC Mathematica adapter (`adapters/mathematica/`).

LeanLink remains a future optional path. It stays disabled (`adapters/mathematica/leanlink.py` `enabled=False`) and outside the theorem TCB until the fuzz and design-review checkboxes in `docs/architecture/leanlink-adapter-review.md` are closed with evidence.

## Rationale

Milestone 1 and PROJECT_SPEC §21 require end-to-end Mathematica generation for rational equality, not a specific native bridge. Wolframscript already provides a full live RationalExpr generator, offline replay of committed bundles, and public CI that does not require Mathematica. Treating LeanLink as a hard Milestone 1 requirement would block §21 / v0.1 on an unfinished native path that is intentionally out of TCB.

## Consequence

- Roadmap and validation matrix treat wolframscript as the MET Mathematica adapter deliverable for M1.
- Native LeanLink integration is DEFERRED; design-review and fuzz stubs remain tracking artifacts, not blockers for §21.
- Studio and product docs may still describe LeanLink as a longer-term Mathematica substrate; they must not imply LeanLink is required for v0.1 live generation.

## Revisit condition

Revisit when LeanLink review checkboxes are evidenced closed and a conformance + adversarial fuzz path justifies enabling the native bridge alongside (or instead of) wolframscript.
