# Stable promotion checklist: `algebra.rational_equality`

This checklist is the **only** in-repo path to mark
`registry/capabilities/algebra.rational_equality.json` `"status": "stable"`.

Do **not** flip `stable` from documentation alone (`registry/README.md`,
`GOVERNANCE.md`). Each box requires an artifact or CI-green evidence.

**Promotion draft (not applied):** see
[`stable-promotion-draft.md`](stable-promotion-draft.md). Capability JSON
remains `"experimental"` until every box below is checked with real human
artifacts and a separate governance PR lands.

## Prerequisites (engineering — evidenced by CI / `just check`)

Local gate: `just check` (see `justfile`). Public workflows under
`.github/workflows/` (index: `.github/workflows/README.md`).

- [x] Conformance suite `evidence/conformance/rfc0001` passing in CI
      (`adapter-conformance.yml` → `python scripts/run_adapter_conformance.py`;
      local: `just conformance`)
- [x] Checker soundness theorems present
      (`MathEvidence/Checkers/RationalEquality/Soundness.lean`; module
      `MathEvidence.Checkers.RationalEquality.Soundness`; built by
      `just lean-build` / `lean.yml` → `lake build`)
- [x] Offline replay green for SymPy and Mathematica committed bundles
      (`offline-replay.yml` → `scripts/offline_replay_python.py` +
      `lake build MathEvidence.Checkers.RationalEquality.OfflineFixtures`;
      local: `just replay`)
- [x] Adversarial seed validation green
      (`adversarial.yml` → `scripts/validate_adversarial_seed.py`;
      local: `just adversarial`)
- [x] Import-boundary + sorry/axiom audit green
      (`lean.yml` → `scripts/check_import_boundaries.py`,
      `scripts/audit_sorry_axioms.py`; local: `just import-boundary`,
      `just sorry-audit`)
- [x] Agent API lists the capability; registry schemas validate
      (`adapter-conformance.yml` → `scripts/validate_registry.py` +
      `pytest adapters agent`; Agent
      `list_capabilities` includes `algebra.rational_equality`
      (`agent/test_agent_api.py`); local: `just registry-validate`,
      `just test`, `just agent-held-out`)
- [x] Meta reification + discovery offline path documented and tested
      (`MathEvidence/Tactic/Examples.lean` → `MathEvidence.Tactic.Examples`;
      built in `offline-replay.yml` and `just replay-lean`)

## Governance gates (human — required for `stable`; still OPEN)

- [ ] **Domain review:** independent mathematical review of repaired /
      canonical statement interface using
      `docs/validation/expert-review-rubric.md` (at least one completed
      sample packet under `docs/validation/review-packets/`, with a real
      reviewer identity — not a placeholder). Owner: domain checker /
      Semantic IR maintainer area. Start from
      `review-packets/SAMPLE-rational-equality-unsigned.md` +
      `review-packets/TEMPLATE.md`.
- [ ] **Trust-model review:** second maintainer from a different area
      confirms replay, digest binding, and claim-strength guarantees are
      not weakened (`GOVERNANCE.md`). Owner: Core and trust model area
      (second approver from a different area).
- [ ] **Milestone 0 external confirmations:** ≥3 non-maintainer entries in
      `docs/validation/user-confirmation.md` (outreach; cannot be invented).
      Owner: outreach lead (process:
      `docs/validation/outreach-checklist.md`). Status: **0/3**.
- [ ] **Project Spec §21 item 10:** at least one external Lean contributor
      or project confirms a real workflow win (may overlap with user
      confirmations if explicitly scoped). Owner: outreach lead. Log:
      `docs/validation/workflow-win-log.md`. Status: **0 entries**.
- [ ] **Capability JSON update PR:** status → `stable`, `knownLimitations`
      updated, reviewers from Core/trust + domain recorded in the PR.
      Owner: Registry + Core/trust (two-area approvals per `GOVERNANCE.md`).
      Exact proposed diff: `docs/validation/stable-promotion-draft.md`
      (**draft only — not applied**).

## Explicitly out of scope for this checklist

- Funding or Foundry frontier acceleration claims
- Live Mathematica/Sage availability on public CI runners
- Fake maintainer sign-off or fabricated user confirmations

## How to promote

1. Complete every box above with links to CI runs / review packets / log entries.
2. Open a PR that only changes registry status (+ limitation text) after gates
   (use the JSON sketch in `stable-promotion-draft.md`).
3. Require two approvals from different maintainer areas before merge.

## Reviewer verification (engineering prerequisites)

After cloning `implement/master-plan` (or the candidate promotion PR branch):

```text
just check
```

That runs lean-build, import-boundary, sorry-audit, schema/registry/federation/
assurance validate, python import smoke, pytest, conformance, differential,
replay, adversarial, agent-held-out, foundry-validate, and tool-selection.

Minimum CI workflows that must be green on the PR:

| Workflow | Engineering boxes covered |
| --- | --- |
| `lean.yml` | soundness build path, import-boundary, sorry-audit |
| `adapter-conformance.yml` | RFC 0001 conformance, registry validate, Agent tests |
| `offline-replay.yml` | SymPy/Mathematica offline replay + Tactic.Examples |
| `adversarial.yml` | adversarial seed catalog |

Do **not** treat a green `just check` as permission to set `"status": "stable"`.
Human governance boxes must still be filled with real artifacts.
