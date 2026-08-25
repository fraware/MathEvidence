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
authority. Current `main` may still use fixture-substitution semantics; this
branch’s live status is exact candidate binding.

## Current assurance maturity

Independent booleans. Checker or fixture existence does not imply exact binding
or Certification Record eligibility. Six owned exact-bound capabilities are
`cr_eligible=true` after Lean exact-replay E2E; federated logic remains false.

<!-- maturity-inventory-table:begin -->
| Capability | adapter_exists | checker_exists | lean_soundness_exists | bridge_replay_exists | exact_candidate_binding_exists | offline_replay_exists | cr_eligible |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `algebra.ideal_membership_witness` | true | true | true | true | true | true | true |
| `algebra.rational_equality` | true | true | true | true | true | true | true |
| `algebra.linear_algebra` | true | true | true | true | true | true | true |
| `logic.finite_counterexample` | true | true | true | true | true | true | true |
| `algebra.formal_rational_calculus` | true | true | true | true | true | true | true |
| `analysis.analytic_calculus` | true | true | true | true | true | true | true |
| `logic.sat_unsat` | true | false | false | false | false | false | false |
| `logic.pseudo_boolean` | true | false | false | false | false | false | false |
| `logic.smt` | true | false | false | false | false | false | false |
<!-- maturity-inventory-table:end -->

**Outcomes:** owned CR-eligible capabilities mint `proved` except
`logic.finite_counterexample` (`refuted`). Federated SAT / PB / SMT stay
fail-closed for theorem CR.

## What this preview is

Protocol, semantic IR, verified checkers, untrusted adapters, Agent API, Studio
surfaces, registry, Foundry schemas/corpus samples, and offline evidence
bundles.

It is **not**:

- a stable computational-evidence layer;
- completed human gates (external confirmations, dual-area review, live
  federation, usability studies);
- attested immutable CI green on a tagged release with required checks
  (branch protection is on; release attestation still open — see
  [`validation/ci/`](validation/ci/));
- a production signing / PKI story (dev keys under `dev/receipt-keys/` only);
- a Foundry Q2 formally-verified corpus at scale (v0.1 samples remain
  `Q1_checker_preview` pending Certification Records).

## Honest limits (summary)

| Topic | Status |
| --- | --- |
| Exact binding | Required for theorem CR; see ADR 0005 |
| CR-eligible set | Six owned capabilities above; federated logic never eligible under exact binding |
| Offline exact inspect | Defaults to `theorem_pending`; `MATHEVIDENCE_OFFLINE_LEAN=1` / `require_lean=True` may yield `theorem_proved` when Lake is available — still not a CR mint |
| Analytic ODE | Empty domain obligations + at most one initial condition; multi-IC / obligation-bearing ODE fail closed |
| Formal vs analytic calculus | Separate IDs; formal is not Mathlib `HasDerivAt` / analytic ODE |
| Bundle / CR schemas | Candidate Bundle v0.3; Certification Record **v0.4** for exact promotion. Legacy v0.3 records must not be silently upgraded |
| Bundle verifier | `mathevidence-verify-bundle` emits `native_checked` / `checker_accepted` only — not theorem Certified |
| OfflineFixtures | Protocol self-tests — not Certification Record authority for a submitted candidate |
| Windows kernel-replay | Required path: `scripts/link_exe_via_rsp.py`; degrade honestly — never fake Certified |
| Stable promotion | Frozen; mechanical promotion-record gate only |

## Engineering surface (preview)

| Area | Notes |
| --- | --- |
| Agent API | v0.1.0; open / inspect / replay by opaque `bundleId` only |
| Ideal membership | Witness identity; no Groebner / non-membership completeness |
| Linear algebra | Exact int/rational ops; practical matrix size bounded by IR policy |
| Rational tactic | Fixtures + live `eq_of_replaySound` Bridge close; not independent `field_simp; ring` |
| CODEOWNERS | Single-owner incubation stub — see `GOVERNANCE.md` |
| Python lock | `uv.lock` committed; see `docs/architecture/python-deps.md` |

## How to build and test

See [`getting-started/`](getting-started/) and the root
[`README.md`](../README.md). Typical local gate: `just check`. Forensic subset:

```text
pytest tests/forensic -q
```

Workflow definitions: `.github/workflows/`. Local green alone is not promotion
evidence.

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
| [`validation/ci/`](validation/ci/) | Machine-readable CI truth records |
| [`architecture/python-deps.md`](architecture/python-deps.md) | Frozen `uv.lock` policy |
| [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md) | Spec / milestone honesty matrix |
| [`release/RELEASE_NOTES_DRAFT.md`](release/RELEASE_NOTES_DRAFT.md) | Public-preview release notes draft |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Normative specification |
| [`README.md`](README.md) | Documentation landing |
