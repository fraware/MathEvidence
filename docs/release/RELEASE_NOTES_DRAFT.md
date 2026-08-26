# Release notes draft — experimental public preview

**Status:** draft for the final experimental 0.x public preview.  
**Not a stable release.** No capability is promoted to `"stable"`.

## Summary

MathEvidence is published as an **experimental** open computational-evidence
platform for Lean. This preview packages protocol, checkers, adapters, Agent
API v0.1.0, Studio surfaces, registry, Foundry samples, benchmark/conformance
corpora, and replayable evidence under explicit limitation documentation
([`KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md),
[`STATUS.md`](../STATUS.md)).

The theorem-promotion rule is candidate-bound and fail-closed: a theorem-level
Certification Record requires the exact submitted candidate to pass the
registered production verification path. Fixtures, nearby theorems, adapter
booleans, and benchmark scores cannot grant theorem status.

## Assurance scope in this preview

Five owned capability fragments are theorem-CR eligible under exact candidate
binding:

- `algebra.ideal_membership_witness` — witness identity only;
- `algebra.linear_algebra` — exact rational `inverse_witness`,
  `system_solution`, `kernel_vector`, and `det_identity`;
- `logic.finite_counterexample` — exact witness establishes `refuted`;
- `algebra.formal_rational_calculus` — registered formal/algebraic operations;
- `analysis.analytic_calculus` — strict theorem-form whitelist with explicit
  hypotheses.

`algebra.rational_equality` remains an experimental checker/soundness/bridge
capability, but theorem Certification Record promotion is disabled for the
pinned Lean 4.14 public-preview path. The candidate-specific checker proposition
does not currently elaborate through the production native-reduction path
without an unacceptable `sorryAx` dependency, so the release fails closed
instead of substituting fixture evidence.

Federated SAT/PB/SMT metadata remains non-CR-eligible in this repository.

## Protocol and evidence versions

- Candidate Bundle: **v0.3**.
- Certification Record for exact theorem promotion: **v0.4**.
- Legacy records retain their original semantics and must not be silently
  upgraded.
- Offline bundle replay and offline kernel theorem replay are separate maturity
  properties; the stronger release-wide offline-kernel property is not claimed.

## Highlights

- **Trust posture explicit:** untrusted adapters propose; checker/Lean authority
  is capability-specific and proposition-scoped.
- **Production exact gate:** CR-eligible paths are exercised through
  `scripts/ci/run_cr_exact_lean_e2e_production.py` and declaration identity is
  read from `Lean.Environment` rather than inferred from source presence.
- **Agent API v0.1.0:** public bundle open/inspect/replay accepts opaque
  **`bundleId` only**; raw filesystem paths are rejected.
- **Capability separation:** formal rational calculus is
  `algebra.formal_rational_calculus`; analytic calculus is a separate strict
  whitelist capability.
- **Forensic suite:** `tests/forensic/` guards exact-binding, tamper, policy,
  adapter/checker, and assurance-boundary regressions.
- **Benchmark discipline:** conformance/regression scores never grant theorem
  Certification Record eligibility.

## Explicit non-claims

- No stable capability promotion.
- No universal solver soundness or broad mathematical completeness claim.
- No claim that the frozen benchmark corpus estimates population false-accept
  probability or generalization.
- No live external federation agreements.
- No completed external user-confirmation / workflow-win / usability study
  counts invented for this draft.
- No attested immutable CI green on a release tag claimed in-tree before that
  tag is actually created and checked.
- Dev receipt HMAC/Ed25519 material is **not** production PKI; production release
  signing remains deferred unless separately established by release evidence.
- Repository branch/ruleset configuration is operational governance, not
  mathematical assurance evidence for this experimental preview.

## Upgrade / migration notes for users

1. Prefer Agent `bundleId` flows; do not pass filesystem paths to public open /
   inspect / replay endpoints.
2. Treat Candidate Bundle v0.3 and Certification Record v0.4 as the current
   exact-promotion protocol surface.
3. Use registry ID `algebra.formal_rational_calculus`; treat legacy
   `symbolic_calculus` path names under `evidence/conformance/` as fixture
   directory names only.
4. Do not treat rational-equality fixtures or bridge theorems as authority for
   an arbitrary submitted candidate; theorem CR is disabled for that capability
   in this pinned Lean 4.14 preview.
5. Read [`docs/security/KNOWN_TRUST_GAPS.md`](../security/KNOWN_TRUST_GAPS.md)
   before relying on any experimental capability.

## Separate stable-promotion work

External confirmations, independent domain/trust review, federation agreements,
usability evidence, multi-area review, and other checklist items remain future
requirements for a `stable` lifecycle promotion. They are not fabricated or
relabelled as completed by this experimental release.
