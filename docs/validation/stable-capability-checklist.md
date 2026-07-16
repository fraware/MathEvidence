# Stable promotion checklist: `algebra.rational_equality`

This checklist is the **only** in-repo path to mark
`registry/capabilities/algebra.rational_equality.json` `"status": "stable"`.

Do **not** flip `stable` from documentation alone (`registry/README.md`,
`GOVERNANCE.md`). Each box requires an artifact or CI-green evidence.

## Prerequisites (engineering — already expected for experimental)

- [ ] Conformance suite `evidence/conformance/rfc0001` passing in CI
      (`adapter-conformance.yml` / `just conformance`)
- [ ] Checker soundness theorems present (`MathEvidence.Checkers.RationalEquality.Soundness`)
- [ ] Offline replay green for SymPy and Mathematica committed bundles
      (`just replay`)
- [ ] Adversarial seed validation green (`just adversarial`)
- [ ] Import-boundary + sorry/axiom audit green (`just import-boundary`,
      `just sorry-audit`)
- [ ] Agent API lists the capability; registry schemas validate
- [ ] Meta reification + discovery offline path documented and tested
      (`MathEvidence.Tactic.Examples`)

## Governance gates (human — required for `stable`)

- [ ] **Domain review:** independent mathematical review of repaired /
      canonical statement interface using
      `docs/validation/expert-review-rubric.md` (at least one completed
      sample packet under `docs/validation/review-packets/`, with a real
      reviewer identity — not a placeholder)
- [ ] **Trust-model review:** second maintainer from a different area
      confirms replay, digest binding, and claim-strength guarantees are
      not weakened (`GOVERNANCE.md`)
- [ ] **Milestone 0 external confirmations:** ≥3 non-maintainer entries in
      `docs/validation/user-confirmation.md` (outreach; cannot be invented)
- [ ] **Project Spec §21 item 10:** at least one external Lean contributor
      or project confirms a real workflow win (may overlap with user
      confirmations if explicitly scoped)
- [ ] **Capability JSON update PR:** status → `stable`, `knownLimitations`
      updated, reviewers from Core/trust + domain recorded in the PR

## Explicitly out of scope for this checklist

- Funding or Foundry frontier acceleration claims
- Live Mathematica/Sage availability on public CI runners
- Fake maintainer sign-off or fabricated user confirmations

## How to promote

1. Complete every box above with links to CI runs / review packets / log entries.
2. Open a PR that only changes registry status (+ limitation text) after gates.
3. Require two approvals from different maintainer areas before merge.
