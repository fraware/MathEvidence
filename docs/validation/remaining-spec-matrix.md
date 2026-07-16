# Remaining spec matrix (honesty freeze)

Maps every [PROJECT_SPEC §21](../PROJECT_SPEC.md) DoD row and every
[DELIVERY_ROADMAP](../DELIVERY_ROADMAP.md) milestone exit criterion to an
in-repo artifact path or `OPEN`.

**Rules**

- `MET` — engineering artifact exists and matches the row as written (no
  invented human confirmations).
- `PARTIAL` — some required artifact exists; gaps listed.
- `OPEN` — no qualifying artifact yet (often human/external).
- Capabilities remain `"status": "experimental"` until
  [stable-capability-checklist.md](stable-capability-checklist.md) is fully
  checked. Do not treat this matrix as a promotion to `stable`.

**Baseline gate:** `just check` on branch `implement/master-plan`.

---

## PROJECT_SPEC §21 — Definition of done for version 0.1

| Row | Criterion | Status | Artifact path or OPEN |
| --- | --- | --- | --- |
| §21.1 | Rational-function equality works end to end through Mathematica and one open backend | MET (engineering) | Open: SymPy live — `adapters/sympy/`, `scripts/mathevidence_cli.py`. Mathematica: full live RationalExpr generator via `wolframscript` when `MATHEVIDENCE_WOLFRAMSCRIPT` set (`adapters/mathematica/`); else fixture/offline. Differential: `scripts/run_differential_backends.py`, `benchmarks/differential/`. LeanLink not TCB (`docs/architecture/leanlink-adapter-review.md`). Capability status remains **experimental** (governance → R2). |
| §21.2 | Same Lean checker accepts both evidence formats after adapter normalization | MET | Checker: `MathEvidence/Checkers/RationalEquality/`. Dual fixtures: `evidence/examples/rational_equality_basic/`, `evidence/examples/rational_equality_mathematica_offline/`. Conformance: `evidence/conformance/rfc0001/`. |
| §21.3 | All side conditions are explicit | MET | RFC: `docs/rfcs/0001-rational-function-equality.md`. Schema: `schemas/rational-equality-certificate.schema.json`. Capability admissibility: `registry/capabilities/algebra.rational_equality.json`. |
| §21.4 | Every example rechecks offline with backends unavailable | MET | `scripts/offline_replay_python.py`, `just replay`; Lean offline: `MathEvidence/Checkers/RationalEquality/OfflineFixtures.lean`, `scripts/generate_lean_offline_fixtures.py`. |
| §21.5 | Request/certificate mismatch and malformed evidence are rejected | MET | Conformance `hash_mismatch`: `evidence/conformance/rfc0001/hash_mismatch/`. Adversarial seed: `benchmarks/adversarial/seed/` (e.g. `wrong_request_hash.json`, `truncated_certificate.json`). Executable malformed/resource cases: `scripts/run_adversarial_executable.py` (`just adversarial-exec`, `security.yml`). |
| §21.6 | Lean package contains no forbidden axioms or incomplete proofs | MET | `just sorry-audit` / `scripts/check_sorry_axioms.py` (wired in `justfile`). |
| §21.7 | Capability discoverable through registry and Agent API | MET | `registry/capabilities/algebra.rational_equality.json` (`experimental`), `registry/catalog.json`, `agent/api/`, `just agent-held-out`. |
| §21.8 | Benchmark includes real and adversarial tasks | MET | Adversarial: `benchmarks/adversarial/seed/manifest.json` + executable runner. Real-world: `benchmarks/real_world/` (≥10 obligations from `docs/validation/bottlenecks.md`; `just real-world`). |
| §21.9 | User can invoke one stable tactic and receive precise status reporting | PARTIAL | Tactic + status: `MathEvidence/Tactic/Mathevidence.lean`, `Discovery.lean`, `Status.lean` (ops: `.rationalEquality`, `.linearAlgebra`, `.finiteCounterexample`), examples under `MathEvidence/Tactic/`. Capability status is still **experimental** (not registry `stable`). |
| §21.10 | At least one external Lean contributor or project confirms a real workflow problem | OPEN | **Owner: outreach lead.** Template: `docs/validation/workflow-win-log.md` (0 entries). Process: `docs/validation/outreach-checklist.md`. May overlap a Milestone 0 user-confirmation entry if explicitly scoped. Do not invent. |

---

## Milestone 0 — Project validation (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| At least three external users confirm the problem | OPEN | **Owner: outreach lead.** `docs/validation/user-confirmation.md` (0/3 completed entries); process: `docs/validation/outreach-checklist.md`. Do not invent. |
| Initial capability is materially useful beyond existing tactics | PARTIAL | Engineering path: RFC `docs/rfcs/0001-rational-function-equality.md`, conformance `evidence/conformance/rfc0001/`. External usefulness confirmation: **OPEN** — owners: outreach lead (§21.10 / M0) + domain reviewer (signed packet). |
| End-to-end trust theorem is understood | MET | `docs/SECURITY_AND_TRUST_MODEL.md`, `docs/PROJECT_SPEC.md` (invariants), `README.md` non-negotiable invariants. |
| Open-backend path is credible | MET | `adapters/sympy/`, `registry/backends/sympy.json` (`conformance_verified` for rational equality). |

### Milestone 0 deliverables (tracking)

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Project charter and trust model | MET | `README.md`, `docs/SECURITY_AND_TRUST_MODEL.md`, `docs/PROJECT_SPEC.md` |
| Twenty or more real computational bottlenecks | MET | `docs/validation/bottlenecks.md` (≥20 rows) |
| Adversarial semantic benchmark seed | MET | `benchmarks/adversarial/seed/` |
| Ecosystem RFC | MET | `docs/rfcs/0001-rational-function-equality.md` (rational-equality capability RFC) |
| Rational-equality capability specification | MET | `docs/rfcs/0001-rational-function-equality.md`, `registry/capabilities/algebra.rational_equality.json` |
| LeanLink adapter design review | PARTIAL | Doc: `docs/architecture/leanlink-adapter-review.md`. Executable fuzz **stubs** MET (`adapters/mathematica/leanlink_fuzz.py`, `benchmarks/adversarial/leanlink_fuzz/`, `just leanlink-fuzz`, `security.yml`). Native bridge + full WXF decoder fuzz still open; bridge disabled. |

---

## Milestone 1 — Rational equality reference path (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| Two backends share one checker | MET (engineering) | SymPy + Mathematica share `MathEvidence.Checkers.RationalEquality`. Live Mathematica: `live_generator_complete` via wolframscript; CI without Wolfram: offline fixtures + differential `skip`/`fixture`. |
| All committed results replay offline | MET | `just replay`, `evidence/examples/`, `evidence/conformance/rfc0001/` |
| Side conditions are explicit | MET | Same as §21.3 |
| Request mismatch is rejected | MET | Same as §21.5 |
| No forbidden axioms or `sorry` | MET | Same as §21.6 |

### Milestone 1 deliverables (tracking)

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Restricted rational-expression IR | MET | `MathEvidence/IR/RationalExpr/`, `schemas/rational-expr.schema.json` |
| Reifier and soundness theorem | MET | `MathEvidence/Tactic/ReifyRational.lean`, `MathEvidence/Checkers/RationalEquality/Soundness.lean` |
| Solver-independent request and evidence schema | MET | `schemas/rational-equality-request.schema.json`, `schemas/rational-equality-certificate.schema.json` |
| Mathematica adapter through LeanLink | PARTIAL | Adapter: `adapters/mathematica/` via **wolframscript** (supported live path; full rational generator). LeanLink scaffold + fuzz stubs (`leanlink_fuzz.py`); not integrated as TCB transport. |
| SymPy or SageMath adapter | MET | `adapters/sympy/` (primary open). Sage: `adapters/sage/` placeholder / fixture-only (`registry/backends/sage.json`). |
| Verified equality checker | MET | `MathEvidence/Checkers/RationalEquality/` |
| Offline evidence bundle | MET | `evidence/examples/rational_equality_*`, `evidence/conformance/rfc0001/` |
| `mathevidence` tactic | MET | `MathEvidence/Tactic/Mathevidence.lean` |
| Conformance suite | MET | `evidence/conformance/rfc0001/`, `just conformance` |

---

## Milestone 2 — Cross-domain proof (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| Common core remains small | MET | Core packages under `MathEvidence/Core/`; LA/cex checkers + full conformance (`registry/capabilities/algebra.linear_algebra.json`, `logic.finite_counterexample.json` `conformanceVerified: true`). |
| No unsafe generic escape hatch is required | MET | Domain-specific IR/checkers; no generic trusted backend Boolean path in `docs/PROJECT_SPEC.md` invariants / adapters. |
| Agent integration improves a held-out task set | MET (engineering) | Suite: `benchmarks/agent/held_out/` (`T05_compute_replay_linear_algebra.json` compute+replay). Measured improvement vs no-MathEvidence baseline: `scripts/run_agent_held_out.py` / `just agent-held-out-baseline`. |
| One external Lean project adopts a component | OPEN | **Owner: outreach lead.** Template: `docs/validation/adoption-log.md` (0 entries). Do not invent. |

### Milestone 2 deliverables (tracking)

| Deliverable | Status | Artifact |
| --- | --- | --- |
| Exact matrix inverse and system-solution witnesses | MET | Lean: `MathEvidence/Checkers/LinearAlgebra/` (+ `Tests.lean` offline fixtures). Conformance: `evidence/conformance/linear_algebra/` (all `requiredCases`). SymPy `conformance_verified`. Mathematica/Sage: `declared` / backend `placeholder`. |
| Finite counterexample checker | MET | `MathEvidence/Checkers/Counterexample/` (+ `Tests.lean`). Conformance: `evidence/conformance/finite_counterexample/` (all `requiredCases`). SymPy `conformance_verified`. Mathematica/Sage: `declared` / backend `placeholder`. |
| Capability registry | MET | `registry/`, `scripts/validate_registry.py` |
| First Agent API release | PARTIAL | `agent/api/`, SDKs present; not a versioned external release claim. |
| VS Code evidence inspector | MET (eng) | `studio/vscode/` Certified-iff-Lean + proposition-before-Certified; goldens `studio/golden/`; usability human OPEN (`docs/validation/studio/usability/`). |
| `mathevidence` ops for LA/CEX | MET | `MathEvidence/Tactic/Status.lean` `Operation.linearAlgebra` / `.finiteCounterexample`; replay BundleIds + examples in `Tactic/Examples.lean`. Lean Meta discovery remains rational-focused; **SymPy CLI discovery** for LA/CEX/calculus via `adapters/common/discovery.py` `discover()` + `mathevidence_cli.py discover`. |

---

## Milestone 3 — Hypothesis intelligence (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| Repaired statements pass semantic expert review | OPEN | **Owner: domain / Semantic IR.** Rubric: `docs/validation/expert-review-rubric.md`; review packet slots (unsigned): `docs/validation/review-packets/HYPOTHESIS-IFACE-{A,B,C}-*-unsigned.md`. No signed packet yet. |
| Weaker variants receive certified counterexamples where claimed | MET (eng) | Lean `buildConditionLatticeWithCex` / `verifyCounterexample`; Agent lattice `weakerVariantRequest` + certified CEX ids. Acceptance: `docs/validation/products/03_hypothesis_synthesis.md`. |
| Minimality is never asserted without proof | MET | Agent tests assert `claimsMinimal is False` (`agent/test_agent_api.py`); lattice schema discipline. |

---

## Milestone 4 — Ecosystem federation (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| MathEvidence adds interoperability without replacing specialized checkers | PARTIAL | Federated registry entries: `registry/capabilities/algebra.groebner_membership.json`, `logic.sat_unsat.json`, `logic.pseudo_boolean.json`, `logic.smt.json`; plan: `docs/architecture/collaboration-cslib-lean-auto-smt.md`. |
| At least two existing projects consume or emit shared metadata | OPEN (live) / PARTIAL (fixture harness) | **Live emit/consume: OPEN** — agreements ledger empty: `docs/architecture/federation-agreements.md`. Fixture emit→consume patterns + digest pairing: `evidence/federation/examples/`, `scripts/validate_federation.py`, `scripts/run_federation_harness.py` (`integrationMode=fixture_only`). Upgrade path: `evidence/federation/examples/UPGRADE_PATH.md`. Do not invent maintainer sign-off. |

---

## Milestone 5 — Symbolic calculus vertical (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| Repeated evidence patterns support several results | PARTIAL | Conformance: `evidence/conformance/symbolic_calculus/`; examples under `evidence/examples/calculus_*`. SymPy live; Mathematica live derivative/antiderivative via wolframscript when `MATHEVIDENCE_WOLFRAMSCRIPT` set (same R1a ToIR patterns); CI offline fixtures when Wolfram absent. Capability status remains **experimental**. |
| Branch and singularity conditions are explicit | MET | `registry/capabilities/analysis.symbolic_calculus.json` admissibility; schemas under `schemas/*calculus*`. |
| Candidate validity remains separate from completeness | MET | Capability `knownLimitations` and claim classes; checker package `MathEvidence/Checkers/Calculus/`; Mathematica notes enforce candidate≠completeness. |

---

## Milestone 6 — Foundry and frontier research (exit criteria)

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| Data improves held-out verified tool use | OPEN (research) / PARTIAL (eng) | Sample corpus: `foundry/`; tool-selection: `benchmarks/tool_selection/`. Measured **reference vs naive baseline** accuracy: `scripts/metrics/foundry_tool_selection.py` / `just foundry-metrics`. **Trained selector uplift: OPEN** (`docs/foundry/exit-gate-status.md`). |
| At least one frontier program is materially accelerated | OPEN | Human/research exit; do not invent. |
| Maintenance funding and ownership are established | OPEN | Human/org exit; ownership plan only — funding not secured. |

---

## Dual-backend honesty snapshot (R1 + R7/M5)

| Capability | SymPy | Mathematica | Sage |
| --- | --- | --- | --- |
| `algebra.rational_equality` | `conformance_verified` (live) | `live_generator_complete` (wolframscript when env set; CI offline/fixture otherwise) | `declared` / backend `placeholder` |
| `algebra.linear_algebra` | `conformance_verified` (live + offline fixtures) | `placeholder` / capability `declared` | `placeholder` / capability `declared` |
| `logic.finite_counterexample` | `conformance_verified` (live + offline fixtures) | `placeholder` / capability `declared` | `placeholder` / capability `declared` |
| `analysis.symbolic_calculus` | `conformance_verified` (live) | `live_generator_complete` (derivative/antiderivative via wolframscript; CI offline fixtures; candidate≠completeness) | n/a |

LeanLink: scaffold until review checkboxes close — not claimed as integrated Mathematica transport.
Supported Mathematica live transport: `MATHEVIDENCE_WOLFRAMSCRIPT` → wolframscript.

---

## TESTING_AND_CI / SECURITY layers (R3)

| Layer | Status | Artifact |
| --- | --- | --- |
| Property (reify/eval, digest, alpha/permutation) | MET | `adapters/common/test_property.py`, `scripts/run_property_tests.py`, `just property` |
| Metamorphic (rename / reassoc / redundant assumptions) | MET | `scripts/run_metamorphic.py`, `just metamorphic` |
| Adversarial executable (hash, truncate, oversized, nesting, path) | MET | `scripts/run_adversarial_executable.py`, `just adversarial-exec`, `.github/workflows/security.yml` |
| Perf budgets | MET | `perfBudgets` in owned capability JSON; `scripts/run_perf_budgets.py`, `just perf-budgets` |
| Real-world ≥10 | MET | `benchmarks/real_world/` (12 obligations from `docs/validation/bottlenecks.md`) |
| Isolation (CPU/memory/wall + cancel→kill) | MET | `docs/architecture/process-isolation.md`, `adapters/common/test_isolation.py` |
| Release provenance | MET | `scripts/generate_release_provenance.py`, `.github/workflows/release.yml` |

Capability `"status"` remains **experimental** (R2 governance); R3 does not promote to `stable`.

---

## Workstream R4 — Cross-domain Milestone 2 honesty

| Item | Status | Artifact |
| --- | --- | --- |
| LA conformance all `requiredCases` | MET | `evidence/conformance/linear_algebra/`; `conformanceVerified: true` |
| CEX conformance all `requiredCases` | MET | `evidence/conformance/finite_counterexample/`; `conformanceVerified: true` |
| SymPy certificate parity + Lean offline fixtures | MET | SymPy generators + Python mirrors; Lean `Checkers/*/Tests.lean` |
| Mathematica/Sage honesty | MET | Remain `declared` / backend `placeholder` (no false `implemented`) |
| `mathevidence` `.linearAlgebra` / `.finiteCounterexample` | MET | `Tactic/Status.lean`, replay BundleIds, `Tactic/Examples.lean` |
| Agent held-out T05 compute/replay + baseline | MET | `T05_compute_replay_linear_algebra.json`; `just agent-held-out` |
| External Lean adoption | OPEN | Template: `docs/validation/adoption-log.md` (human fills) |

---

## Workstream R5 — Products 03–07 productization

| Item | Status | Artifact |
| --- | --- | --- |
| Product 03 Hypothesis E2E + Lean-authoritative Agent ops | MET (eng) | Lean `Hypothesis` + `buildConditionLatticeWithCex`; Agent `authorityStatus=lean_checker_mirror`; report `docs/validation/products/03_hypothesis_synthesis.md` |
| Product 03 expert review ≥3 interfaces | OPEN | Unsigned slots `docs/validation/review-packets/HYPOTHESIS-IFACE-{A,B,C}-*-unsigned.md` — human signatures not invented |
| Product 04 formal family campaign + precision accounting | MET (eng) | `MathEvidence.Conjecture.Tests.campaignDemo` + `Precision.lean`; Agent `run_family_campaign` |
| Product 04 theorem or open-problem artifact | MET | Theorem `eq_refl_on_nat3`; open problem `docs/validation/products/artifacts/conjecture-open-problem-nat-le-family.md` |
| Product 04 expert precision-rate judgment | OPEN | Engineering accounting recorded; expert sign-off not invented |
| Product 05 multi-step reconstructible vs final-answer-only | MET (eng) | `just trace-to-plan-demo`; `benchmarks/trace_to_plan/multistep_rational_demo.json` |
| Product 05 expert lemma-graph coherence | OPEN | Human |
| Product 06 independent algorithm-contract docs | MET | `docs/assurance/*.md` (beyond thin re-exports); completeness null |
| Product 07 historical replay independent of mutable registry | MET | Version pins in bundles; `just registry-historical-replay` |
| Acceptance reports 03–07 | MET | `docs/validation/products/` |

Capability `"status"` remains **experimental** (R2). R5 does not invent expert signatures or flip `stable`.

---

## Workstream R6 — Studio (Product 09) readiness

| Item | Status | Artifact |
| --- | --- | --- |
| Certified iff Lean status (VS Code + Wolfram) | MET | `studio/vscode/epistemic.js`, `studio/wolfram/MathEvidenceStudio.wl`, `studio/epistemic_contract.py` |
| Integration tests / golden transcripts | MET | `studio/golden/transcripts/`; `adapters/common/test_epistemic_studio.py`; `just studio-test` |
| Lean proposition + assumptions before Certified affordance | MET | `buildCertificationSurface` / `CertificationSurface`; VS Code panel `data-section` order |
| Usability protocol + ≥3 scripted sessions | MET (protocol) | `docs/validation/studio/usability/PROTOCOL.md`, sessions `S01`–`S03`, facilitator `FACILITATOR_CARD.md` |
| Human usability session results | OPEN | **Owner: Studio / UX lead.** Session result rows + `defect-log.md` — do not invent. One-sitting pack: `human-gates-one-sitting.md` |
| No unique MathEvidence semantics outside Lean/IR | MET | Studio READMEs + acceptance report discipline |
| Product 09 acceptance report | MET (eng) | `docs/validation/products/09_studio.md` (criterion 1 human OPEN) |

Capability `"status"` remains **experimental** (R2). R6 does not invent usability outcomes or flip `stable`.

---

## Workstream R2 — Governance packaging (engineering done; humans OPEN)

Engineering prerequisites on
[`stable-capability-checklist.md`](stable-capability-checklist.md) are ticked
with CI / `just check` evidence. Capability JSON remains
`"status": "experimental"`. Draft-only promotion note (not applied):
[`stable-promotion-draft.md`](stable-promotion-draft.md).

| R2 human gate | Status | Owner | Artifact when closed |
| --- | --- | --- | --- |
| Domain expert signed review packet | OPEN | Domain / Semantic IR | Completed file under `review-packets/` (not SAMPLE-unsigned) |
| Trust-model review (second maintainer area) | OPEN | Core and trust model (+ different-area approver) | Sign-off on promotion PR; checklist box |
| Milestone 0: ≥3 external user confirmations | OPEN | Outreach lead | `user-confirmation.md` (≥3); process `outreach-checklist.md` + emails `outreach-email-templates.md` |
| §21.10 workflow win (≥1) | OPEN | Outreach lead | `workflow-win-log.md` (≥1 entry) |
| Capability JSON → `stable` PR + two-area approvals | OPEN | Registry + Core/trust; domain co-review | PR using body in `stable-promotion-draft.md` after gates |
| One-sitting human pack | MET (eng packaging) | — | `human-gates-one-sitting.md`, Studio `FACILITATOR_CARD.md` |

**Reviewer verification (engineering):** `just check`; workflows `lean.yml`,
`adapter-conformance.yml`, `offline-replay.yml`, `adversarial.yml`. Green CI
does **not** flip `stable`.

---

## Workstream R7 — Federation / Foundry / §19 (engineering)

| Item | Status | Artifact |
| --- | --- | --- |
| Federation harness emit→consume patterns | MET (fixture_only) | `scripts/run_federation_harness.py`, digest pairing in `validate_federation.py` |
| Federation upgrade path + agreements ledger | MET (docs) | `evidence/federation/examples/UPGRADE_PATH.md`, `docs/architecture/federation-agreements.md` (all OPEN) |
| Live external federation (≥2 peers) | OPEN | Human/maintainer agreements — do not invent |
| M5 Mathematica calculus live (R1a ToIR) | MET (eng) | `adapters/mathematica/adapter.py` `compute_symbolic_calculus`; supportLevel `live_generator_complete`; CI fixture when Wolfram absent |
| Foundry tool-selection baseline vs reference | MET (eng) | `scripts/metrics/foundry_tool_selection.py` — not trained uplift |
| Foundry corpus quality + contribution tracking | MET (eng) | `scripts/metrics/foundry_corpus_quality.py`, `track_contributions.py` (0 records) |
| §19 metrics instrumentation | MET (eng) | `scripts/metrics/` — verified coverage, open replay, semantic defect placeholders |
| Trained selector uplift / frontier accel / funding | OPEN | Human/research — see `docs/foundry/exit-gate-status.md` |

Capability `"status"` remains **experimental**. R7 does not flip `stable`, invent
federation liveness, funding, or frontier acceleration.
