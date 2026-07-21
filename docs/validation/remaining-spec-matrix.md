# Remaining spec matrix (honesty freeze)

Maps every [PROJECT_SPEC §21](../PROJECT_SPEC.md) DoD row and every
[DELIVERY_ROADMAP](../DELIVERY_ROADMAP.md) milestone exit criterion to an
in-repo artifact path or `OPEN`.

**Authority:** [`docs/security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md) and
[`STATUS.md`](../STATUS.md) supersede optimistic labels when they conflict.
Do not invent human confirmations. Capabilities remain
`"status": "experimental"` until
[stable-capability-checklist.md](stable-capability-checklist.md) is fully
checked with real artifacts.

**Status labels**

- `MET` — qualifying engineering artifact exists and matches the row as written.
- `PARTIAL` — some required artifact exists; gaps listed.
- `OPEN` — no qualifying artifact yet (often human/external).

Local `just check` ≠ attested immutable CI green on a release commit.

---

## PROJECT_SPEC §21 — Definition of done for version 0.1

| Row | Criterion | Status | Artifact path or OPEN |
| --- | --- | --- | --- |
| §21.1 | Rational-function equality works end to end through Mathematica and one open backend | PARTIAL — protocol reference | Dual adapters (`adapters/sympy/`, `adapters/mathematica/`). Not proof of indispensable external search (`externalSearchEssential: false`). Capability **experimental**. |
| §21.2 | Same Lean checker accepts both evidence formats after adapter normalization | MET (eng) | `MathEvidence/Checkers/RationalEquality/` + conformance fixtures. |
| §21.3 | All side conditions are explicit | MET (eng) | RFC/schemas; coverage⇒Defined bridge for ℚ present in checker soundness path. |
| §21.4 | Every example rechecks offline with backends unavailable | MET (eng) | Offline packaging + Lean request digest recompute from claim payload. |
| §21.5 | Request/certificate mismatch and malformed evidence are rejected | MET (eng) | Conformance + forensic binding/forgery suites under `tests/forensic/`. |
| §21.6 | Lean package contains no forbidden axioms or incomplete proofs | PARTIAL | Regex audits (`scripts/audit_sorry_axioms.py`); compiled axiom/import audits still desired. |
| §21.7 | Capability discoverable through registry and Agent API | MET (eng) | Registry + Agent; public API is `bundleId`-only; registry-driven dispatch. |
| §21.8 | Benchmark includes real and adversarial tasks | MET (eng) | Suites under `benchmarks/` + `tests/forensic/`. |
| §21.9 | User can invoke one stable tactic and receive precise status reporting | PARTIAL | Tactic remains **experimental**; theorem-producing rational replay exists — not a `stable` claim. |
| §21.10 | At least one external Lean contributor or project confirms a real workflow problem | OPEN | Template: `docs/validation/workflow-win-log.md` (0 entries). Do not invent. |

---

## Milestone 0 — Project validation

| Exit criterion | Status | Artifact path or OPEN |
| --- | --- | --- |
| At least three external users confirm the problem | OPEN | `docs/validation/user-confirmation.md` (0/3); process: `outreach-checklist.md`. |
| Initial capability is materially useful beyond existing tactics | PARTIAL | Engineering path exists; external usefulness confirmation OPEN. |
| End-to-end trust theorem is understood | MET | `docs/security/SECURITY_AND_TRUST_MODEL.md`, `docs/PROJECT_SPEC.md`, `README.md`. |
| Open-backend path is credible | MET | `adapters/sympy/`, `registry/backends/sympy.json`. |

---

## Milestone 1 — Rational equality reference path

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Two backends share one checker | MET (eng) | SymPy + Mathematica → `MathEvidence.Checkers.RationalEquality` |
| Offline replay | MET (eng) | `just replay`, `evidence/examples/`, `evidence/conformance/rfc0001/` |
| Side conditions / mismatch reject / no forbidden axioms | See §21.3–§21.6 | |

Evidence Bundle trees for full bundles use schema **v0.2** (`.cjson`).

---

## Milestone 2 — Cross-domain proof

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Common core remains small | MET (eng) | Core + LA/CEX checkers and conformance |
| No unsafe generic escape hatch | MET | Domain-specific IR/checkers |
| Agent held-out improvement | MET (eng) | `benchmarks/agent/held_out/`, `just agent-held-out` |
| External Lean project adoption | OPEN | `docs/validation/adoption-log.md` (0 entries) |
| First Agent API release | MET (eng) | Agent API **v0.1.0** (`agent/api/openapi.yaml`, `agent/CHANGELOG.md`) |

---

## Milestone 3 — Hypothesis intelligence

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Repaired statements pass semantic expert review | OPEN | Unsigned packets under `docs/validation/review-packets/` |
| Weaker variants receive certified counterexamples where claimed | MET (eng) | Lean + Agent lattice/CEX paths; product spec `docs/products/03_HYPOTHESIS_SYNTHESIS.md` |
| Minimality never asserted without proof | MET (eng) | Agent tests assert `claimsMinimal is False` |

---

## Milestone 4 — Ecosystem federation

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Interoperability without replacing specialized checkers | PARTIAL | Federated registry entries + `docs/architecture/collaboration-cslib-lean-auto-smt.md` |
| ≥2 projects consume or emit shared metadata | OPEN (live) / PARTIAL (fixture) | Ledger: `docs/architecture/federation-agreements.md`; fixtures under `evidence/federation/` |

---

## Milestone 5 — Symbolic / formal calculus

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Repeated evidence patterns | PARTIAL | `evidence/conformance/symbolic_calculus/` (fixture path name); capability id `algebra.formal_rational_calculus` |
| Branch/singularity conditions explicit | MET (eng) | Capability admissibility + schemas |
| Candidate ≠ completeness | MET (eng) | Claim classes + checker package |

Analytic Mathlib calculus is a separate experimental id: `analysis.analytic_calculus`.

---

## Milestone 6 — Foundry and frontier research

| Exit criterion | Status | Artifact |
| --- | --- | --- |
| Data improves held-out verified tool use | PARTIAL | `foundry/`, `benchmarks/tool_selection/`; trivial trained lift on tiny suite only |
| Frontier program materially accelerated | OPEN | Do not invent |
| Maintenance funding and ownership established | OPEN | Ownership plan only — funding not secured |

---

## Dual-backend honesty snapshot

| Capability | SymPy | Mathematica | Sage |
| --- | --- | --- | --- |
| `algebra.rational_equality` | `conformance_verified` | `live_generator_complete` (wolframscript / CI fixtures) | `declared` / placeholder |
| `algebra.linear_algebra` | `conformance_verified` | `live_generator_complete` (gated) | `live_generator_complete` (gated) |
| `logic.finite_counterexample` | `conformance_verified` | `live_generator_complete` (gated) | `live_generator_complete` (gated) |
| `algebra.formal_rational_calculus` | `conformance_verified` | `live_generator_complete` (derivative/antiderivative gated) | n/a |

Supported Mathematica live transport: `MATHEVIDENCE_WOLFRAMSCRIPT` → wolframscript.
LeanLink native bridge remains deferred.

---

## Governance packaging (humans OPEN)

Engineering may be packaging-ready; humans are not. See
[`stable-capability-checklist.md`](stable-capability-checklist.md).

| Gate | Status | Artifact when closed |
| --- | --- | --- |
| Domain expert signed review packet | OPEN | Completed file under `review-packets/` |
| Trust-model review (second area) | OPEN | `TRUST-MODEL-TEMPLATE.md` → dated packet or PR note |
| ≥3 external user confirmations | OPEN | `user-confirmation.md` |
| §21.10 workflow win | OPEN | `workflow-win-log.md` |
| Capability JSON → `stable` + dual approvals | OPEN | Governance PR after checklist |
| Live federation ≥2 peers | OPEN | `federation-agreements.md` |
| Studio usability ≥3 sessions | OPEN | `studio/usability/sessions/` result rows |

Capability `"status"` remains **experimental**.
