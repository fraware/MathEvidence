# Wave 4 Lean build status (ME-RV-040..043)

Date: 2026-07-26

## Intent

Wave 4 converts exact linear algebra and finite counterexample tactics from
"checker gate plus independent proof" into proof-producing evidence workflows:

- Proof-producing matrix / finite-predicate reifiers (`eqProof` /
  `interpretationProof` objects)
- Tactics apply Bridge / `replaySound` / `checkBool_sound` (no independent
  `native_decide` as final theorem authority)
- Kernel-replay Certification Record path for LA and CEX examples
- Agent conjecture: Python mirror → `candidate_witness` / `mirror_accepted`
  only; `falsified` only after verified Certification Record

## Local Lake / Mathlib

**Resolution fixed** (see [`MATHLIB_RESOLUTION.md`](MATHLIB_RESOLUTION.md)).
Previous `revision not found 'v4.14.0'` was a corrupted local package checkout.
Core + verify-bundle exes build; full Checkers/Mathlib compile not claimed here.

Correct Lean sources are committed under:

- `MathEvidence/Checkers/LinearAlgebra/{Bridge,ReplaySound,OfflineFixtures}.lean`
- `MathEvidence/Checkers/Counterexample/{Bridge,ReplaySound,OfflineFixtures}.lean`
- `MathEvidence/Tactic/{ReifyMatrix,LinearAlgebra,ReifyFinitePredicate,Counterexample}.lean`

When Mathlib resolves:

```text
lake build MathEvidenceCheckers
lake env lean MathEvidence/Checkers/LinearAlgebra/Bridge.lean
lake env lean MathEvidence/Checkers/Counterexample/Bridge.lean
```

## Verification without Lean

```text
python -m pytest adapters/common/test_wave4_la_cex.py \
  adapters/common/test_lean_mirrors_la_cex.py \
  agent/test_agent_api.py agent/test_finite_graph.py -q
```

Kernel replay with `require_lean=False` still emits Certification Records with
theorem identity / axiom report scaffolding; Lean compile fields report
`pending_lean` / `leanOk=false` when Lake is blocked.

## GitHub issues

- https://github.com/fraware/MathEvidence/issues/25 — ME-RV-040
- https://github.com/fraware/MathEvidence/issues/26 — ME-RV-041
- https://github.com/fraware/MathEvidence/issues/27 — ME-RV-042
- https://github.com/fraware/MathEvidence/issues/28 — ME-RV-043

Milestone: [Wave 4 — Cross-domain theorem production](https://github.com/fraware/MathEvidence/milestone/7)
