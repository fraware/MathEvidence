# ME-RV-081 — External held-out benchmark request

Fillable package for an **external-project** held-out evaluation set.
Normative: `docs/audits/2026-07-26-real-vision/10_FOUNDRY_BENCHMARKS_AND_FEDERATION.md`.

**Status: BLOCKED(human)** — 0 / 20 slots filled with real provenance.
Do not invent library sources, licenses, or permissions. In-repo synthetic
`held_out` benchmark strata do **not** close this gate.

**GitHub:** https://github.com/fraware/MathEvidence/issues/43  
**Issue form:** `.github/ISSUE_TEMPLATE/held_out_benchmark.yml`

## Acceptance (all required)

- [ ] ≥5 Mathlib-derived algebra obligations with permissions + provenance
- [ ] ≥5 SciLean / Physlib (or equivalent) analytic obligations
- [ ] ≥5 CSLib / finite-structure obligations
- [ ] ≥5 independent contributor problems
- [ ] No train/eval contamination with adapter-development or conformance fixtures
- [ ] Not claimed as adoption (adoption is ME-RV-086)

## Provenance fields (every slot)

| Field | Required |
| --- | --- |
| Slot ID | yes (family prefix + index) |
| Source project / library | yes |
| Source URL + commit / tag | yes |
| License | yes |
| Explicit redistribution / evaluation permission | yes (link or quote) |
| Obligation summary (1–2 sentences) | yes |
| Capability family (rational / ideal / LA / analytic / cex / other) | yes |
| Contamination check (not in train/conformance) | yes |
| Contact (optional, consented) | optional |
| Notes / issue link | optional |

## Family A — Mathlib-derived algebra (slots A01–A05)

| Slot | Source | Commit/tag | License | Permission recorded? | Obligation summary | Capability | Contamination OK? | Contact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | | | | no | | | no | | |
| A02 | | | | no | | | no | | |
| A03 | | | | no | | | no | | |
| A04 | | | | no | | | no | | |
| A05 | | | | no | | | no | | |

## Family B — SciLean / Physlib analytic (slots B01–B05)

| Slot | Source | Commit/tag | License | Permission recorded? | Obligation summary | Capability | Contamination OK? | Contact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | | | | no | | | no | | |
| B02 | | | | no | | | no | | |
| B03 | | | | no | | | no | | |
| B04 | | | | no | | | no | | |
| B05 | | | | no | | | no | | |

## Family C — CSLib / finite structures (slots C01–C05)

| Slot | Source | Commit/tag | License | Permission recorded? | Obligation summary | Capability | Contamination OK? | Contact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | | | | no | | | no | | |
| C02 | | | | no | | | no | | |
| C03 | | | | no | | | no | | |
| C04 | | | | no | | | no | | |
| C05 | | | | no | | | no | | |

## Family D — Independent contributor problems (slots D01–D05)

| Slot | Source | Commit/tag | License | Permission recorded? | Obligation summary | Capability | Contamination OK? | Contact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01 | | | | no | | | no | | |
| D02 | | | | no | | | no | | |
| D03 | | | | no | | | no | | |
| D04 | | | | no | | | no | | |
| D05 | | | | no | | | no | | |

## Summary

| Metric | Status |
| --- | --- |
| Slots with full provenance | **0 / 20** |
| ME-RV-081 | **BLOCKED(human)** |
| Gap matrix row | stays BLOCKED until humans fill ≥20 |

## How to fill (do not invent)

1. Obtain explicit permission to evaluate / redistribute each obligation.
2. Record license + source commit before copying any statement into benchmarks.
3. Open or update issue #43 (or a child issue via `held_out_benchmark.yml`).
4. Link filled slots from `benchmarks/` or Foundry held-out split only after provenance is complete.
5. Leave empty cells empty until real artifacts exist.
