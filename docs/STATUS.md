# Project status (public preview)

MathEvidence is an **experimental** computational-evidence platform for Lean.
Adapters propose; Lean decides. No registry capability is `"stable"`.

**Assurance invariant:** a theorem-level Certification Record may be issued only
when the **exact submitted candidate** was verified by the declared trusted path
([ADR 0005](adr/0005-exact-candidate-binding.md)). Fixture or nearby theorems
cannot certify a different claim.

**Authoritative maturity / CR eligibility:**
[`registry/maturity-inventory.json`](../registry/maturity-inventory.json)
(validated against this page). **Limitations:**
[`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md).
**Operator runbook:** [`HANDOFF.md`](HANDOFF.md).

Historical dated audits under
[`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) and older
`MET` labels are engineering-archive records — not current Certification Record
authority. Current code uses exact candidate binding for the registry-enabled
exact paths; protocol fixtures remain self-tests and cannot certify a different
submitted candidate.

## Current assurance maturity

These are independent dimensions. Checker or fixture existence does not imply
exact binding or Certification Record eligibility. The registry currently marks
five owned exact-bound capabilities `cr_eligible=true`; rational equality keeps
its checker/soundness/bridge surface but is deliberately fail-closed for theorem
Certification Records under the pinned Lean 4.14 public-preview path. Federated
logic remains non-eligible. The required `lean` release gate executes
production-generated candidates for every CR-eligible capability and every
exact-enabled linear-algebra operation.

Offline maturity is intentionally split. `offline_bundle_replay_exists` means a
sealed bundle can be deterministically regenerated/validated without consulting
the solver or network after materialization. `offline_kernel_replay_exists`
means release CI requires successful offline Lean theorem execution; no capability
claims that stronger maturity today. The legacy `offline_replay_exists` JSON
field is only a compatibility alias for bundle replay and is not an independent
column below.

<!-- maturity-inventory-table:begin -->
| Capability | adapter_exists | checker_exists | lean_soundness_exists | bridge_replay_exists | exact_candidate_binding_exists | offline_bundle_replay_exists | offline_kernel_replay_exists | cr_eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `algebra.ideal_membership_witness` | true | true | true | true | true | true | false | true |
| `algebra.rational_equality` | true | true | true | true | false | true | false | false |
| `algebra.linear_algebra` | true | true | true | true | true | true | false | true |
| `logic.finite_counterexample` | true | true | true | true | true | true | false | true |
| `algebra.formal_rational_calculus` | true | true | true | true | true | true | false | true |
| `analysis.analytic_calculus` | true | true | true | true | true | true | false | true |
| `logic.sat_unsat` | true | false | false | false | false | false | false | false |
| `logic.pseudo_boolean` | true | false | false | false | false | false | false | false |
| `logic.smt` | true | false | false | false | false | false | false | false |
<!-- maturity-inventory-table:end -->

**Outcomes:** CR-eligible owned capabilities mint `proved` except
`logic.finite_counterexample` (`refuted`). Rational equality and federated SAT /
PB / SMT stay fail-closed for theorem CR.

## What this preview is

Protocol, semantic IR, verified checkers, untrusted adapters, Agent API, Studio
surfaces, registry, Foundry schemas/corpus samples, and replayable evidence
bundles.

It is **not**:

- a stable computational-evidence layer;
- completed human gates (external confirmations, dual-area review, live
  federation, usability studies);
- attested immutable CI green on a tagged release;
- a production signing / PKI story (dev keys under `dev/receipt-keys/` only);
- a Foundry Q2 formally-verified corpus at scale (v0.1 samples remain
  `Q1_checker_preview` pending Certification Records).

Repository branch/ruleset configuration is an operational governance choice for
this experimental preview; it is not mathematical assurance evidence and is not
a prerequisite for the public-preview release.

## Honest limits (summary)

| Topic | Status |
| --- | --- |
| Exact binding | Required for theorem CR; see ADR 0005 |
| CR-eligible set | Five owned capabilities above; rational equality and federated logic are not theorem-CR eligible in this release |
| Rational equality | Checker, soundness theorem, bridge, and exact-source generator remain; theorem CR is disabled fail-closed under pinned Lean 4.14 because the candidate-specific checker proposition cannot be admitted on the production native-reduction path without an unacceptable `sorryAx` dependency |
| Exact Lean release gate | `scripts/ci/run_cr_exact_lean_e2e_production.py` executes production-generated candidates through the production kernel-replay staging and declaration-inspection path under pinned Lean; structural generation or standalone temporary-file execution is insufficient |
| Offline bundle replay | Available for owned capability bundles where declared; deterministic integrity/re-generation may end at `theorem_pending` |
| Offline kernel replay | Not claimed as release maturity today; optional `require_lean=True` may prove when the materialized closure is available, but setup failure does not count as proof |
| Analytic calculus | Strict theorem-form whitelist; unsupported forms fail closed |
| Analytic ODE | Empty domain obligations + at most one initial condition; multi-IC / obligation-bearing ODE fail closed |
| Formal vs analytic calculus | Separate IDs; formal rational calculus is not general Mathlib analysis |
| Bundle / CR schemas | Candidate Bundle v0.3; Certification Record **v0.4** for exact promotion. Legacy v0.3 records must not be silently upgraded |
| Bundle verifier | `mathevidence-verify-bundle` emits `native_checked` / `checker_accepted` only — not theorem Certified |
| OfflineFixtures | Protocol self-tests — not Certification Record authority for a submitted candidate |
| Windows kernel-replay | Required path: `scripts/link_exe_via_rsp.py`; degrade honestly — never fake Certified |
| Stable promotion | Blocked until the repository-defined stable-promotion and human/trust gates are genuinely closed |

## Engineering surface (preview)

| Area | Notes |
| --- | --- |
| Agent API | v0.1.0; open / inspect / replay by opaque `bundleId` only |
| Ideal membership | Witness identity; no Groebner / non-membership completeness |
| Rational equality | Exact rational checker/soundness/bridge surface remains experimental; theorem Certification Record promotion is disabled for the pinned Lean 4.14 release path |
| Linear algebra | Exact rational `inverse_witness`, `system_solution`, `kernel_vector`, `det_identity`; no broad linear-algebra completeness claim |
| Finite counterexample | Exact witness establishes `refuted`; no-witness search does not prove the universal claim |
| Formal rational calculus | Formal/algebraic grammar only; candidate-only requests remain evidence-only |
| Analytic calculus | Exact whitelist only; capability name must not be read as arbitrary analytic proof support |
| Rational tactic | Fixtures + live `eq_of_replaySound` Bridge close; not independent `field_simp; ring`; fixture closure is not candidate CR authority |
| CODEOWNERS | Single-owner incubation stub — see `GOVERNANCE.md` |
| Python lock | `uv.lock` committed; see `docs/architecture/python-deps.md` |

## How to build and test

See [`getting-started/`](getting-started/) and the root
[`README.md`](../README.md). Typical local gate: `just check`. Forensic subset:

```text
pytest tests/forensic -q
```

Production-generated exact Lean E2E:

```text
python scripts/ci/run_cr_exact_lean_e2e_production.py
```

The companion `scripts/ci/run_cr_exact_lean_e2e.py` module owns the checked-in
case/coverage matrix and a standalone diagnostic runner. Its temporary-file Lean
execution is not the authoritative release path.

Workflow definitions: `.github/workflows/`. Local green alone is not promotion
or release evidence; the exact release SHA must have the required remote gates
green.

## Related docs

| Doc | Role |
| --- | --- |
| [`HANDOFF.md`](HANDOFF.md) | Engineering / exact-certification runbook |
| [`adr/0005-exact-candidate-binding.md`](adr/0005-exact-candidate-binding.md) | Exact-candidate-binding invariant |
| [`validation/handoff-2026-08-25-delta.md`](validation/handoff-2026-08-25-delta.md) | Dated delta vs exact-certification baseline pin |
| [`../registry/maturity-inventory.json`](../registry/maturity-inventory.json) | Machine-readable maturity / CR eligibility |
| [`audits/2026-07-26-real-vision/`](audits/2026-07-26-real-vision/) | Historical re-audit (not current CR authority) |
| [`security/KNOWN_TRUST_GAPS.md`](security/KNOWN_TRUST_GAPS.md) | Known limitations |
| [`validation/stable-capability-checklist.md`](validation/stable-capability-checklist.md) | Only path to `stable` |
| [`validation/ci/`](validation/ci/) | Machine-readable CI configuration and truth records |
| [`architecture/python-deps.md`](architecture/python-deps.md) | Frozen `uv.lock` policy |
| [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md) | Spec / milestone honesty matrix |
| [`release/RELEASE_NOTES_DRAFT.md`](release/RELEASE_NOTES_DRAFT.md) | Public-preview release notes draft |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Normative specification |
| [`README.md`](README.md) | Documentation landing |
