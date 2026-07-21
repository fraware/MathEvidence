# Engineering closure — code gap ledger

**Authority:** closure specs `02`–`20`, `23`–`24`, `26` vs working tree.  
**Rule:** status reflects **code**, not aspirational docs. Human gates ME-401–408 stay OPEN.  
**Do not invent:** live Mathematica/Sage, CI green URLs, or human confirmations.

Updated: 2026-07-21 (v0.2 full Evidence Bundle migration + ideal multi-gen Meta slice).

Priority order: trust → semantic E2E → product → ops.

| Pri | MUST (short) | Spec | Tree today | Status |
| --- | --- | --- | --- | --- |
| T1 | Trusted-path theorem shape (quote+bind+check→original) for all theorem ops | 02 | Rational strong; Encoding Mathlib densify/quote + Fin/Bool/sparse eval bridges; tactics import Encoding | PARTIAL→advanced |
| T2 | Replay exe proves goal / emits bound receipt | 03 | `mathevidence-replay` runs rational `checkBool` + goal match → receipt with `claimEstablished` | MET (rational reference) |
| T3 | Hard-fail replay error codes (full set) | 03 / 26 | Digest/request/cert/goal codes in Lean exe + Agent mapping | PARTIAL→advanced |
| T4 | `native_checked` records enlarged ops base + small kernel replay | 03 | Schema enum + ops-base field; small-kernel replay still thin | PARTIAL |
| T5 | Bundle v0.2 `.cjson` + receipt/theorem/axiom roles | 03 | Writers + dual-read; **34/34** full Evidence Bundle trees under `evidence/` migrated; case-only/federation/foundry excluded | MET (writers + fixtures) |
| T6 | Encoding/ package home for reification correctness | 01 / 23 | Encoding Rat + Matrix densify/quote + Finite CEX + Polynomial/MvPolynomial eval identities + Examples | PARTIAL→advanced |
| S1 | ReifierRegistry drives discovery (rat/LA/CEX/ideal) | 02 / 23 | Registry live + discovery helpers | PARTIAL→advanced |
| S2 | Sage rational: live+conformance **or** un-advertise | 05 | Un-advertised from rational supportClaims | MET (honesty) |
| S3 | Analytic: quotient/log/ODE ordinary theorems | 08 | Inverse/ODE + div/log IR + positivity theorems | PARTIAL→advanced |
| S4 | Rational/LA/CEX ordinary E2E completeness | 05–07 | Meta + exe rational replay; full Mathlib search still open | PARTIAL→advanced |
| P1 | Studio Certified only via receipt | 16 | Shared verify + goldens; usability human OPEN | PARTIAL (eng MET) |
| P2 | Agent: no public raw path; all spec-15 ops | 15 | path removed; replay wires Lean authority; TTP ops honest unsupported | PARTIAL→advanced |
| P3 | Federation: agreement schema + ≥2 fixture peers | 14 | Schema + fixture agreements (`federationLevel: fixture`) | PARTIAL (live OPEN) |
| O1 | JCS vectors + third impl | 02 / 24 | Expanded vectors + JS tool under `tools/jcs/` | PARTIAL→advanced |
| O2 | Perf budget **distributions** (not single JSON) | 18 / 24 | Distributions under `benchmarks/perf/distributions/` | PARTIAL→advanced |
| O3 | SBOM / provenance scripts runnable | 18 | Provenance + SBOM script | PARTIAL→advanced |
| O4 | Compiled axiom/import audits | 18 | Lake exes are source-scan drivers | PARTIAL |
| O5 | Lean/Mathlib bump | 18 | Stays 4.14.0; bump BLOCKED | BLOCKED |
| G1 | CODEOWNERS real dual-area teams | 19 | Nine-area stubs; still single owner — honest | OPEN (packaging) |
| H1 | ME-401–408 human confirmations | 19 / 22 | Packaging only; **0 confirmations** | OPEN |

## This pass moved

- Migrated remaining calculus / ideal / LA / CEX / symbolic_calculus Evidence Bundle trees to v0.2 `.cjson` (`scripts/migrate_bundles_v02.py`); dual-read kept; receipt-aware remigrate for Lean-proven rational reference
- Ideal Meta slice: ordinary theorem `X₀³−X₀X₁ ∈ ⟨X₀²−X₁, X₁⟩` (multi-gen mv with non-monomial generator) closed by `mathevidence_ideal_membership` without `sorry`

## Remaining MUST blockers (ranked)

1. Full Mathlib search completeness for LA/CEX/ideal beyond Meta + Encoding bridges (e.g. broader Gröbner / LA solution discovery from goal without witness in context)
2. Immutable CI green on a release commit + toolchain bump path
3. Human ME-401–408 + live federation agreements
4. Case-only conformance / federation JSON remain non-bundle layouts (documented; not T5 blockers)
