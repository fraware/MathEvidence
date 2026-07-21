# Open problem — lift finite `x ≤ x` beyond `nat ≤ 3`

**Product:** 04 Conjecture / Falsification  
**Family:** `finite.nat_le_3`  
**Campaign artifact:** Lean `MathEvidence.Conjecture.Tests.campaignDemo`  
**Status:** `open` (not a theorem over unbounded `ℕ`)

## Statement (bounded evidence)

On the executable family with domain `x : Nat`, `x ≤ 3`, the candidate
`x ≤ x` is bounded-verified. This is **not** an unbounded theorem.

## Open problem

Produce a reusable Mathlib-facing theorem (or disproof) for the intended
unbounded reading, with an explicit object-family contract that connects the
finite enumerator to the formal type — without presenting finite evidence as
universal truth.

## Related reusable theorem from same campaign

`MathEvidence.Conjecture.Tests.eq_refl_on_nat3` — formally proved survivor for
`x = x` under `x ≤ 3` (campaign precision accounting counts this as
`formallyProved`, separate from this open problem).

## Precision accounting (campaign demo)

| Metric | Value |
| --- | --- |
| proposed | 3 |
| falsified | 1 (`x = 0`) |
| formallyProved | 1 (`x = x`) |
| openProblems | 1 (this artifact) |

Do not invent expert precision-rate sign-off; engineering accounting is recorded
in Lean `campaign_precision_accounting`.
