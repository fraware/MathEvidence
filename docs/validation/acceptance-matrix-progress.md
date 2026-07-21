# Acceptance matrix — engineering closure progress

Authority: closure specs `22_ACCEPTANCE_MATRIX.md` + `KNOWN_TRUST_GAPS.md`.
This file tracks **in-repo evidence** only. Do not invent CI run URLs or human
confirmations.

Baseline audit commit: `f17ab395`.

Gap ledger: `docs/validation/engineering-closure-gap-ledger.md`.

| Gate family | Row (short) | Status | Evidence |
| --- | --- | --- | --- |
| Trust | Lean expected request digest (live) | MET | `Discovery.lean` + `Wire.lean`; forensic digest tests |
| Trust | Joint forgery hard-fail (Python) | MET | `adapters/common/bundle.py`; forensic joint forgery |
| Trust | Lean offline ofClaim digest == wire | MET | `Request.ofClaim` via wire JSON; OfflineFixtures `digest_matches_ofClaim_*` |
| Trust | Typed digests | MET | `Core/Digest/Types.lean`; Bundle `ContentDigest` |
| Trust | Coverage ⇒ Defined | MET (ℚ) | `RationalEquality/Soundness.lean` |
| Trust | Theorem-producing replay | MET (rational) | Tactic closes ℚ goals; Lake `mathevidence-replay` emits receipt with `claimEstablished` after checkBool+goal match; Agent wires Lean authority |
| Trust | Checker receipt | PARTIAL→advanced | Lean receipt + Studio/Agent verify; content digest; optional **dev-only** HMAC/Ed25519; `operationalBase`; exe writes `checker-receipt.cjson` |
| Trust | Agent path jail | MET | Public schemas require `bundleId` only (raw `path` rejected); content-addressed store |
| Trust | Registry-driven Agent dispatch | MET | `registry_allows_compute` |
| Trust | Encoding package | PARTIAL→advanced | Mathlib densify/quote (`densify_interpret_quote`), Fin/Bool/bounded CEX bridges, sparse↔Polynomial/MvPolynomial eval; `Encoding.Examples` |
| Trust | Bundle v0.2 `.cjson` | MET (writers + fixtures) | Writers + dual-read; **34/34** full Evidence Bundle trees migrated; case-only/federation/foundry excluded (documented) |
| Trust | Compiled audits | PARTIAL | Lake axiom/import exes (source-scan drivers) |
| Quality | CI pin + local gates | PARTIAL | SHA-pinned Actions; `just check`; SBOM script; perf **p95 distributions**; local `uv.lock` TLS-blocked |
| Quality | Toolchain current | BLOCKED (PR8 done) | Stay on 4.14.0; checklist + blocker in `toolchain-migration-notes.md` |
| Semantic | Rational E2E ordinary goals | PARTIAL | Replay/discovery close under denom hyps; candidate lifecycle open |
| Semantic | LA / CEX Mathlib bridge | PARTIAL→advanced | Meta paths + Encoding densify/quote + Fin/Bool bridges; full Mathlib search still open |
| Semantic | Formal calculus rename | MET (capability ID) | No live `analysis.symbolic_calculus` registry id |
| Semantic | Analytic vertical | PARTIAL→advanced | Quotient + log-under-positivity + ODE residual/IC; completeness rejected |
| Value | Ideal membership | PARTIAL→advanced | Meta Ideal.span + MvPolynomial (incl. multi-gen non-monomial pair); SymPy + offline Mathematica/Sage fixtures; 55 tasks |
| Products | ME-301–307 | MET (eng code) / PARTIAL (scale) | Prior product scaffolding; Agent TTP ops honest unsupported |
| Community | ME-401–408 | PACKAGED / OPEN | Prep complete; **0 human confirmations** |
| Registry | Support matrix | PARTIAL→advanced | Sage rational **un-advertised**; JCS vectors + JS third impl |
| Federation | Fixture agreements | PARTIAL (live OPEN) | Agreement schema + ≥2 fixture peer records |

**Release cuts:** do not claim `v0.1.1-trust-repair` / `v0.2.0` / stable until
immutable CI + remaining OPEN rows + human gates close. Promotion to stable is
**blocked on ME-401–408 human confirmations** even when engineering packaging is done.
