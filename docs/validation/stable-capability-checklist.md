# Stable promotion checklist: `algebra.rational_equality`

This checklist is the **only** in-repo path to mark
`registry/capabilities/algebra.rational_equality.json` `"status": "stable"`.

Do **not** flip `stable` from documentation alone. Each box requires an
artifact or CI-green evidence. Capability JSON remains `"experimental"` until
every box below is checked with real human artifacts and a separate governance
PR lands.

> **BLOCKED:** Do not flip `status: stable` while the human gates in
> [`KNOWN_TRUST_GAPS.md`](../../KNOWN_TRUST_GAPS.md) remain open (0 external
> confirmations today). Engineering packaging is not human confirmation.
> Ownership reality: [`.github/CODEOWNERS`](../../.github/CODEOWNERS) is still a
> single-owner stub — see [`GOVERNANCE.md`](../../GOVERNANCE.md).

## Prerequisites (engineering)

Local gate: `just check` (see `justfile`). Public workflows under
`.github/workflows/` (index: `.github/workflows/README.md`).

Do not re-tick boxes from memory. Prefer immutable workflow URLs on the
candidate commit plus forensic-green evidence under `tests/forensic/`.

- [ ] Conformance suite `evidence/conformance/rfc0001` passing in **immutable CI**
      on the candidate commit (not only local `just conformance`)
- [ ] Checker soundness with coverage⇒Defined bridge (ℚ)
- [ ] Offline replay with Lean-recomputed request digests and theorem-producing
      rational replay (not status-only)
- [ ] Adversarial + forensic suites green (`tests/forensic/`)
- [ ] Compiled axiom + import-graph audits preferred over regex-only
- [ ] Agent `bundleId`-only public surface + registry-driven dispatch
- [ ] Live request-digest binding; checker theorem remains closing authority
- [ ] Typed digests / receipts present

## Governance gates (human — required for `stable`; still OPEN)

- [ ] **Domain review:** independent mathematical review using
      `docs/validation/expert-review-rubric.md` (completed packet under
      `docs/validation/review-packets/`, real reviewer identity). Start from
      `review-packets/SAMPLE-rational-equality-unsigned.md` (copy without
      `-unsigned`) + `review-packets/TEMPLATE.md`.
- [ ] **Trust-model review:** second maintainer from a different area confirms
      replay, digest binding, and claim-strength guarantees are not weakened
      (`GOVERNANCE.md`). Fill `review-packets/TRUST-MODEL-TEMPLATE.md`.
- [ ] **Milestone 0 external confirmations:** ≥3 non-maintainer entries in
      `docs/validation/user-confirmation.md`. Process:
      `docs/validation/outreach-checklist.md`. Status: **0/3**.
- [ ] **Project Spec §21 item 10:** at least one external Lean contributor or
      project confirms a real workflow win. Log:
      `docs/validation/workflow-win-log.md`. Status: **0 entries**.
- [ ] **Capability JSON update PR:** status → `stable`, `knownLimitations`
      updated, reviewers from Core/trust + domain recorded in the PR
      (two-area approvals per `GOVERNANCE.md` once teams exist).

## Explicitly out of scope for this checklist

- Funding or Foundry frontier acceleration claims
- Live Mathematica/Sage availability on public CI runners
- Fake maintainer sign-off or fabricated user confirmations

## How to promote

1. Complete every box above with links to CI runs / review packets / log entries.
2. Open a PR that only changes registry status (+ limitation text) after gates.
3. Require two approvals from different maintainer areas before merge (when
   multi-area CODEOWNERS is real; until then, do not pretend dual-area review
   happened).

## Reviewer verification (engineering prerequisites)

```text
just check
pytest tests/forensic -q
```

Minimum CI workflows that must be green on the PR:

| Workflow | Engineering boxes covered |
| --- | --- |
| `lean.yml` | soundness build path, import-boundary, sorry-audit |
| `adapter-conformance.yml` | RFC 0001 conformance, registry validate, Agent tests |
| `offline-replay.yml` | SymPy/Mathematica offline replay + Tactic.Examples |
| `adversarial.yml` | adversarial seed catalog |

Do **not** treat a green `just check` as permission to set `"status": "stable"`.
Human governance boxes must still be filled with real artifacts.
