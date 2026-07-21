# Known trust gaps (audit freeze)

**Baseline commit:** `f17ab39599018590b435fc2583688ffc5682fbdd`  
**Authority:** engineering-closure audit (`00_REPOSITORY_AUDIT.md`) supersedes optimistic in-repo `MET` labels until each gap is closed with failing-then-passing forensic tests and immutable CI evidence.

**Promotion rule:** no capability may leave `experimental`; no stable-promotion draft may be treated as ready while any P0 below remains open.

---

## P0 defects (still present at freeze)

| ID | Defect | Citation | Forensic test | Closing PR |
| --- | --- | --- | --- | --- |
| P0-1 | Live request-binding bypass: expected digest overwritten with `cert.requestDigest` before `checkBool` | `MathEvidence/Tactic/Discovery.lean:322` | `tests/forensic/test_digest_substitution.py` | PR-Request-Binding |
| P0-2 | Offline fixtures embed wire digests; Lean does not recompute from claim payload | `MathEvidence/Checkers/RationalEquality/OfflineFixtures.lean` (generated); `scripts/generate_lean_offline_fixtures.py` | `tests/forensic/test_joint_forgery.py` | PR-Request-Binding |
| P0-3 | Status-only replay: requires goal `True`, closes with `True.intro` | `MathEvidence/Tactic/Mathevidence.lean:70-73` | `tests/forensic/test_status_only_replay.py` | PR-Receipt-Replay |
| P0-4 | Coverage ≠ Defined: soundness takes separate `Defined` premises; `coverOk` is not the soundness bridge | `MathEvidence/Checkers/RationalEquality/Spec.lean`; `Soundness.lean` | Covered by binding/coverage suite after PR-Digest-Types | PR-Request-Binding |
| P0-5 | Agent path escape: absolute paths accepted; no root jail | `agent/api/service.py:57-63` (`_resolve_path`) | `tests/forensic/test_path_jail.py` | PR-Agent-Sandbox |
| P0-6 | Missing closure artifacts (`Core/Digest/Types.lean`, `Core/Receipt.lean`, `bundle_store.py`, `mathevidence-replay`) | Audit §3.9 / plan missing-artifacts list | Presence checks in forensic suite | PR-Digest-Types / Receipt / Agent |
| P0-7 | Independent close via `field_simp; ring` after certificate accept (bypasses checker theorem as closing authority) | `MathEvidence/Tactic/Discovery.lean:326-342` | Documented; closed with theorem replay | PR-Request-Binding / Rational-E2E |
| P0-8 | Bundle digest type confusion (request digest used as file content digest) | `MathEvidence/Core/Bundle.lean` / rational replay metadata | Typed digest migration tests | PR-Digest-Types |
| P0-9 | Registry/API support divergence (registry advertises Mathematica/Sage beyond Agent routing) | `agent/api/service.py:241-251` vs `registry/capabilities/*.json` | `tests/forensic/test_registry_api_divergence.py` | PR-Agent-Sandbox |
| P0-10 | Positive-characteristic denom cast: `rat` literal checks `d ≠ 0` as `Nat`, not cast nonzero | `MathEvidence/IR/RationalExpr/Eval.lean:20-22`, `Defined` at `:46` | `tests/forensic/test_positive_char_denom.py` + Lean | PR-Request-Binding / Rational-E2E |
| P0-11 | CI evidence absent on audited commit; docs claim engineering gates complete | `docs/validation/remaining-spec-matrix.md`; `stable-capability-checklist.md` | Honesty freeze in this file + docs | PR-CI-Supply-Chain |
| P0-12 | Symbolic calculus ID overstates analytic math | `registry/capabilities/algebra.formal_rational_calculus.json` | Rename note; closed by PR-Calculus-Reclassification | PR-Calculus-Reclassification |

---

## Honest classifications (freeze)

| Surface | Honest status |
| --- | --- |
| Rational equality | Protocol / semantic-boundary **reference**; `externalSearchEssential: false`; Lean can close via `field_simp; ring` independently of backend output |
| Linear algebra / finite CEX | LA Meta tactic covers inverse + system solve + kernel + det ordinary examples; finite CEX Meta path covers Fin/Bool/bounded Nat/**bounded Int** with budget-exhaust `unknown` e2e; not full Mathlib search completeness |
| `algebra.formal_rational_calculus` | Formal rational-expression calculus only — analytic `HasDerivAt` is a separate vertical |
| Analytic calculus | `HasDerivAt` / `HasDerivWithinAt` product/inverse/domain-positivity fragments + ODE residual/IC + antiderivative Bool certificate; broad primitives and completeness claims remain rejected |
| Ideal membership | Lean normalize+detailed reject + univariate `Ideal.span` Meta auto-bridge (singleton + two-generator) + **MvPolynomial (Fin 2/3/4) Meta** with grevlex exact division for **non-monomial principal generators** (when an exact ℤ quotient exists) + **multi-gen pair with a non-monomial generator** (e.g. `X₀³−X₀X₁ ∈ ⟨X₀²−X₁, X₁⟩`) + monomial gens; SymPy Agent compute + CA bundles; Mathematica/Sage **offline fixtures** for ≥2 shared requests (live only if env/binary present — not advertised otherwise); adversarial wrong-witness / wrong-generator-order / multivariate wrong-witness rejects; 55-task harness (≥50) |
| Agent API | Experimental orchestration; path jail + content-addressed store; verified/`claimEstablished` only with content-bound receipt; optional receipt content digest + dev HMAC/Ed25519 verify when present |
| CI / `just check` | Local/workflow **definitions** exist; immutable green runs still open; `uv.lock` blocked locally (TLS) — CI `uv-lock.yml` on ubuntu-latest is the authoritative generation path |
| Stable promotion | **Blocked** by human gates ME-401–408 (packaging complete; confirmations OPEN) |

---

## Tracking

Forensic regressions live under `tests/forensic/`. They assert correct trust behavior.

**Status after continued engineering-closure pass (working tree, not a release tag):**

| ID | Status |
| --- | --- |
| P0-1 live digest substitution | **Fixed** |
| P0-2 offline digest recompute | **Fixed** — `Request.ofClaim` uses wire JSON; OfflineFixtures prove digest match |
| P0-3 status-only replay | **Fixed** — theorem-producing rational replay closes goals |
| P0-4 coverage⇒Defined | **Fixed** (ℚ) |
| P0-5 Agent path escape | **Fixed** |
| P0-6 missing artifacts | **Fixed** — Types/Receipt/store present; `mathevidence-replay` theorem-produces for rational equality (receipt + `claimEstablished`); content-addressed Agent open/replay; receipt content digest + optional **dev-only** HMAC/Ed25519 (not production PKI) |
| P0-7 field_simp independent closer | **Mitigated** — only after checker accept on matched claim |
| P0-8 digest type confusion | **Fixed** |
| P0-9 registry/API divergence | **Fixed** — registry-driven dispatch |
| P0-10 positive-char denom | **Fixed** |
| P0-11 CI evidence | **Partial** — pins/gates; immutable green still open; local `uv.lock` TLS-blocked; CI `uv-lock.yml` generates lock on ubuntu-latest |
| P0-12 calculus rename | **Fixed (capability ID)** — `algebra.formal_rational_calculus`; live `analysis.analytic_calculus` is a separate experimental fragment |

**Working-tree advances (this session):** Encoding package + LA/CEX/Ideal Encoding imports; ReifierRegistry liveKinds; Sage rational un-advertised; AnalyticExpr quotient/log/ODE advances; Agent path jail + TTP honest unsupported; federation fixture agreements; JCS + JS third impl; replay hard-fail codes; perf p95 distributions; SBOM; receipt `operationalBase`; **`mathevidence-replay` theorem-produces for rational equality**; **bundle v0.2 `.cjson`**: all **34** full Evidence Bundle trees under `evidence/` migrated (`scripts/migrate_bundles_v02.py`; dual-read kept; case-only/federation/foundry excluded — see `docs/validation/bundle-v0.2-migration-notes.md`); Ideal Meta multi-gen mv non-monomial pair ordinary theorem without `sorry`.

Acceptance matrix: `docs/validation/acceptance-matrix-progress.md`. Gap ledger: `docs/validation/engineering-closure-gap-ledger.md`. Human gates remain OPEN for interviews/signatures; preparable packaging is recorded in `human-gates-status.md`.

**Still needs humans (not inventable):** ME-401–408 confirmations; Q3 semantic review labels (≥100 packets queued); Conjecture expert precision judgment; Hypothesis ≥30 interface reviews; TTP lemma-graph coherence; Studio usability sessions; immutable CI green evidence on a release commit.
