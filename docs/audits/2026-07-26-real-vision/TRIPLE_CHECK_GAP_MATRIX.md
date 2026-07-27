# Triple-check gap matrix — real-vision audit

**Date:** 2026-07-26  
**Normative sources:** `docs/audits/2026-07-26-real-vision/` (promoted from `temp_audit_specs/`; pointer-only README remains in `temp_audit_specs/`)  
**Method:** Code search + file reads + local `lake build` oleans; wave status markdown treated as claims only.  
**Statuses:** `MET` | `PARTIAL` | `MISSING` | `BLOCKED(human|org|mathlib|env)`

Legend for evidence: cite concrete paths. Stubs, smoke-only paths, docs theater, or uncompiled soundness → never `MET`.

---

## Executive counts (this pass)

| Class | Count (approx.) |
| --- | ---: |
| MET | 65 |
| PARTIAL | 6 |
| MISSING | 0 |
| BLOCKED | 12 |

**Note:** Prior draft listed `MISSING = 2` with no `MISSING` rows in the
tables; corrected to **0**. Remaining engineering gaps are `PARTIAL` (or
hybrid MET/PARTIAL). Human/org items stay `BLOCKED`. Counts refreshed
2026-07-27 post-crash verification after local commits `1eb1e15` + `c1c3303`
(ahead of `origin/main`; **not pushed**).

**Top remaining gaps**

1. Push + attested Actions on protected main (P0-G); signed 0.x prerelease unpublished (ME-RV-074 **BLOCKED(human)** publish).
2. Human/org gates: federation, adoption, teams, held-out external benchmark interviews (templates only — stay **BLOCKED**).
3. Windows kernel-replay: **rsp is the required local path**; native Lake 4.14 link remains PARTIAL(toolchain); Linux CI authoritative.
4. Live rational Bridge (ME-RV-023 / E-12) and in-repo ideal release-grade Certification Record (P0-F / ME-RV-035) are **MET** for their owned fragments; external held-out stays **BLOCKED(human)**.

**Fixed in this continuation pass**

- ME-RV-040 det: **general-n** Mathlib transport via non-partial fuel `detRats` /
  `detRatsFuel` + `minorRats`=`eraseIdx` + `det_succ_row_zero`;
  `det_of_isDetIdentity` for all `Fin n`; examples `det_fin5_example` /
  `det_fin6_example`; tactic closes via Bridge (no n>4 hard-fail).
  Practical scale: `IR/MatrixExpr.defaultSizeLimit` (64 entries) + factorial
  Laplace cost are an **intentional resource policy** (A5), not a missing proof.
- ME-RV-020 proof-term: `proofTermSerializationOfConst?` / `proofTermDigestOfConst?` via structural `serializeExpr` (not `Expr.hash`); `#test_theorem_identity_expr` + forensic coverage.
- ME-RV-022/054 Windows: `scripts/link_exe_via_rsp.py` is the **required** Windows local path; `smoke_exe` / `just exe-smoke` always attempt rsp and degrade with `replay_dependency_missing` (never fake Certified); Linux CI still required.
- Docs: `15_ACCEPTANCE_MATRIX.md` split into historical `c7040e6` snapshot vs living score reconciled to this matrix.
- Prior pass: rectangular LA sys/ker; Ideal triple/live Meta; timeout taxonomy / forgery forensic; Fin-4 det Laplace.

---

## P0 findings (`00_EXECUTIVE_REAUDIT.md`)

| ID | Status | Evidence |
| --- | --- | --- |
| P0-A Standalone replay overclaim | **MET** | `MathEvidence/Exe/Replay.lean` emits `native_checked` / `checker_accepted`; MUST NOT emit `kernel_replay` / `soundness_verified`. Forensic: `tests/forensic/test_verify_bundle_no_theorem_status.py`. |
| P0-B Untruthful receipt digests | **MET** | Tactic refuses request-digest collision. Live replay uses `ExprSerialize` digests. Proof-term digests via `serializeExpr` (`proofTermDigestOfConst?`); Lean `Expr.hash` not used. |
| P0-C Theorem/axiom placeholders | **MET** | `adapters/common/bundle.py` rejects placeholders; forensic `test_no_placeholders.py`. |
| P0-D Store keyed by request digest | **MET** | `bundle_store.py` keys by bundle digest; collision hard-fail. |
| P0-E Ideal semantics bridge | **MET** | `IR/Polynomial/Soundness.olean` + `IdealMembership/Soundness.olean` (`mem_span_*_of_check` + `mem_span_triple_of_check`) + live Meta `ExamplesIdealMembership.olean` (`live_x2_minus_1_span`, `live_xy_span`, `live_xyz_span`). |
| P0-F Ideal benchmark scores oracle | **MET** (scoring + in-repo certification) | Candidate tier: propose ∧ decode ∧ checkMembership. Release tier: OfflineFixtures + `replaySound` Certification Record (`--tier release` / nightly `benchmarks.yml`). External held-out (ME-RV-081) stays **BLOCKED(human)**. |
| P0-G CI unverified / incomplete | **PARTIAL** | Forensic + kernel-replay + analytic self-test + Environment import/axiom audits in `lean.yml`; `uv.lock` committed at `1eb1e15`. Remains PARTIAL until push + Actions green on protected main (`docs/validation/ci/post_push_ci_attestation.md`). |

### P1 findings

| ID | Status | Evidence |
| --- | --- | --- |
| P1-A Rational protocol reference | **MET** | Registry `role: protocol_reference`, `externalSearchEssential: false`. |
| P1-B LA/CEX parallel proof paths | **MET** (general-n inverse + rectangular system/kernel + general-n det + CEX Bridge) | Bridge oleans + Fin-5/6 det examples + rectangular sys/ker; CEX Bridge olean. |
| P1-C Analytic scaffolding | **MET** (soundness + fixture replay) / **PARTIAL→improved** (Windows exe via rsp) | Soundness + ReplaySound; generator `cert_product`; Linux CI + Windows `link_exe_via_rsp.py` + `--self-test-analytic`. |
| P1-D Agent product overclaim | **MET** | Hypothesis/conjecture/TTP require Certification Record. |

---

## Wave 0 — ME-RV-001..003

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-001 | **MET** | Exe + `adapters/common/replay.py` + forensic strip theorem statuses. |
| ME-RV-002 | **MET** | Placeholder reject + evidence migration reports. |
| ME-RV-003 | **PARTIAL** | CI truth JSON + protection; local lock-in-history MET (`uv.lock` @ `1eb1e15`); remote Actions attestation open. |

---

## Wave 1 — ME-RV-010..013

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-010 Candidate Bundle v0.3 | **MET** | `Core/Bundle.lean`, schemas, example manifests `bundleVersion:0.3.0`. |
| ME-RV-011 Content-addressed store | **MET** | `bundle_store.py` + forensic collision tests. |
| ME-RV-012 Certification Record | **MET** | `CertificationRecord.lean`, schemas, `agent/api/receipt.py` (stale env lock downgrades `verified`). |
| ME-RV-013 Migrate evidence | **MET** | Migration report; examples candidate-only. |

---

## Wave 2 — ME-RV-020..024

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-020 Theorem identity | **MET** (type + proof-term via `serializeExpr`) | `ExprSerialize` type + `proofTermDigestOfConst?`; `#test_theorem_identity_expr`; forensic `test_proof_term_serialize_not_expr_hash`. Lean `Expr.hash` explicitly not claimed. |
| ME-RV-021 Bundle verifier exe | **MET** | `mathevidence-verify-bundle`; operational-only statuses; `resource_limit_exceeded` on oversized role files. |
| ME-RV-022 Rational kernel replay | **MET** (Linux CI + Windows **required** rsp path) / residual **PARTIAL(toolchain)** (Lake 4.14 native link) | Lake exe + `replaySound`; Linux CI `--self-test`; Windows must use `link_exe_via_rsp.py`; `smoke_exe` / `just exe-smoke` always attempt rsp and degrade with `replay_dependency_missing` (never fake Certified). |
| ME-RV-023 Rational tactic authority | **MET** (fixtures + supported live fragment) | Bridge closers + `RationalClose` live quoting/`eq_of_replaySound`; Discovery emits Candidate Bundle + Certification Record digests; non-fixture examples + adversarial negatives in `Tactic/Examples.olean`. |
| ME-RV-024 Agent/Studio gate | **MET** | Certification Record fields required for Certified; stale env lock visible. |

---

## Wave 3 — Ideal membership ME-RV-030..036

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-030 Fixed-arity IR | **MET** | Mathlib `Vector Nat m`; `Syntax.olean`. |
| ME-RV-031 Interpret/soundness | **MET** | `Interpret.olean` + `Soundness.olean`. |
| ME-RV-032 Checker → Ideal.span | **MET** | `checkBool_sound` / `checkMembership_sound` / `mem_span_*_of_check` oleans. |
| ME-RV-033 Proof-producing reifier | **MET** | `ReifyPolynomial.olean` + `polyE` on `PolyResult`. |
| ME-RV-034 External-search tactic | **MET** | Live Meta: `live_x2_minus_1_span` / `live_xy_span` / `live_xyz_span`; Fin-4 IR `ir_four_var_product_span`; `proposeTripleWitness?`; adversarial checker rejects in `ExamplesIdealMembership.olean`. |
| ME-RV-035 Benchmark | **MET** (in-repo release-grade) / external **BLOCKED(human)** | Candidate smoke never claims `soundness_verified`. Release tier requires Certification Record via Ideal OfflineFixtures (`xy`/`x2m1`). In-repo `held_out` is synthetic; ME-RV-081 external library-derived held-out remains open. |
| ME-RV-036 Rename | **MET** | `algebra.ideal_membership_witness`. |

---

## Wave 4 — LA / CEX ME-RV-040..043

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-040 LA reifier bridge | **MET** (general-n inverse + rectangular system/kernel + general-n det) | `Bridge.olean` + `BridgeDet.olean` (`det_of_isDetIdentity`); examples `det_fin5_example` / `det_fin6_example`; tactic applies Bridge for all square `n`. Practical `n` bounded by intentional `defaultSizeLimit` (64) / Laplace cost — resource policy, not a proof gap. |
| ME-RV-041 LA kernel replay | **MET** (inv/sys/ker/det fixtures) | `OfflineFixtures.replay_*_sound`; generator fixtures `inv`/`sys`/`ker`/`det`; `kernel_replay` op→fixture; forensic claim-surface tests. |
| ME-RV-042 CEX reifier bridge | **MET** | `Counterexample/Bridge.olean`. |
| ME-RV-043 CEX kernel replay | **MET** (nat_eq0 + bool_false fixtures) | `OfflineFixtures.replay_*_sound`; generator `nat_eq0`/`bool_false`; forensic claim-surface tests. |

---

## Wave 5 — Analytic ME-RV-050..054

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-050 Interpretation/domain | **MET** | `IR/AnalyticExpr/Interpret.olean`. |
| ME-RV-051 DerivProof certificate | **MET** (source) | Inductive `DerivProof`. |
| ME-RV-052 Inductive HasDerivAt | **MET** | `AnalyticCalculus/Soundness.olean`. |
| ME-RV-053 ODE candidate | **MET** (candidate residual) | `checkODE_sound` (no completeness/uniqueness). |
| ME-RV-054 Adapter/reifier/kernel | **MET** (fixture kernel path) / **PARTIAL→improved** (Windows rsp link) | ReplaySound + `cert_product` + CI `--self-test-analytic`; Windows rsp helper + smoke dual self-test. |

---

## Wave 6 — Product epistemology ME-RV-060..062

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-060 Hypothesis | **MET** | Mirror ≠ certified. |
| ME-RV-061 Conjecture | **MET** | Mirror → preview only. |
| ME-RV-062 Trace-to-Plan | **MET** | `verify_certification_record` required. |

---

## Wave 7 — Reproducibility ME-RV-070..074

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-070 Frozen Python deps | **MET** (lock in history) | `uv.lock` committed in `1eb1e15`; workflows use `uv sync --frozen`. Remote attested green still under P0-G. |
| ME-RV-071 Import audit | **MET** | `mathevidence-import-graph` + `Lean.importModules` / `ModuleData.imports`; `environmentLevel: true` in CI bundle. |
| ME-RV-072 Axiom audit | **MET** | `mathevidence-axiom-report` + `CollectAxioms` on soundness decls + project-axiom filter; classical markers reported; `environmentLevel: true`. |
| ME-RV-073 Complete required CI | **PARTIAL→improved** | Protection + forensic + rational/analytic kernel-replay + env audits; lock committed; push/Actions attestation open. |
| ME-RV-074 Signed experimental release | **PARTIAL** → publish **BLOCKED(human)** | Hooks present; no published release. |

---

## Wave 8 — Foundry / governance / adoption ME-RV-080..087

| ID | Status | Evidence |
| --- | --- | --- |
| ME-RV-080 Foundry Q2 redefine | **MET** | `foundry/pipelines/quality.py`; corpus 0 Q2. |
| ME-RV-081 Held-out external | **BLOCKED(human)** | Fillable `docs/validation/held-out-external-benchmark.md` (0/20) + OPEN #43. |
| ME-RV-082 Federation peer 1 | **BLOCKED(human)** | `fixture_only`; `federation-live-checklist.md` + OPEN #44. |
| ME-RV-083 Federation peer 2 | **BLOCKED(human)** | Same; OPEN #45. |
| ME-RV-084 Maintainer teams | **BLOCKED(org)** | CODEOWNERS `@fraware`; teams runbook exists. |
| ME-RV-085 External validation | **BLOCKED(human)** | Interview script `external-validation-interview.md` (0/3) + OPEN #47. |
| ME-RV-086 External adoption | **BLOCKED(human)** | Checklist `external-adoption-checklist.md` (0) + OPEN #48. |
| ME-RV-087 Promotion record | **MET** (mechanism) / stable **BLOCKED(human)** | Schema + validator; 0 stable. |

---

## Acceptance matrix (`15_ACCEPTANCE_MATRIX.md`) — ruthlessly scored

### Program-level gates

| Gate | Status |
| --- | --- |
| Exact request binding | **MET** (rational) |
| Immutable evidence | **MET** |
| Real theorem identity | **MET** (elaborated type + proof-term via `serializeExpr`; not `Expr.hash`) |
| Checker authority | **MET** (rational + ideal live Meta Fin≤3 + LA general sys/ker + general-n det + CEX + analytic) |
| Kernel acceptance | **MET** (rational + analytic fixtures; Linux CI required) / **PARTIAL(toolchain)** (Windows via required `link_exe_via_rsp.py`) |
| Axiom transparency | **MET** (Environment CollectAxioms + classical markers) |
| Honest receipt | **MET→improved** (forgery + stale env lock forensic) |
| Replay independence | **PARTIAL→improved** |
| CI attestation | **PARTIAL** (awaiting push + Actions on `1eb1e15`/`c1c3303`) |
| Reproducibility | **MET** (lock in history @ `1eb1e15`) / remote attestation under P0-G |
| Governance | **BLOCKED(org/human)** |
| Adoption | **BLOCKED(human)** |

### Stable promotion

**BLOCKED(human)** — forbidden until every relevant box closes.

---

## Build evidence (local, this pass)

| Target | Result |
| --- | --- |
| `MathEvidence.Checkers.LinearAlgebra.Bridge` | **olean** (`det_of_isDetIdentity` general-n + rectangular sys/ker; via `BridgeDet`) |
| `MathEvidence.Checkers.LinearAlgebra.BridgeDet` | **olean** (`detRatsFuel_ofFnSquare` / `det_of_isDetIdentity`) |
| `MathEvidence.Tactic.ExamplesLinearAlgebra` | **olean** (`det_fin5_example`, `det_fin6_example`, `det_fin4_*`, rectangular, kernel Fin-4) |
| `MathEvidence.Core.ExprSerialize` / `ExprSerializeTests` | **olean** (proof-term serialize + digest Meta tests) |
| `mathevidence-kernel-replay` | **exe** on Windows via required `scripts/link_exe_via_rsp.py`; `--self-test` + `--self-test-analytic` |
| Forensic suite | pytest `tests/forensic` (proof-term + kernel-replay codes) |
| Rational SymPy conformance (`rfc0001`) | **ok** (8 cases via `scripts/run_adapter_conformance.py`); Mathematica live skipped (`MATHEVIDENCE_WOLFRAMSCRIPT` unset) |

---

## What must not be faked

Do **not** mark MET: live federation, adoption interviews, org teams without `admin:org`, stable promotion, published signed release, or Mathlib-heavy soundness without oleans.
