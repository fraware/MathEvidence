/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.IR.RationalExpr.Eval

/-!
# Rational equality claim proposition (Mathlib `ℚ`)

Separated from `Spec.lean` so checkers/exes that only need structures avoid
linking Mathlib evaluation.
-/

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.IR.RationalExpr

/-- Proposition established on success: for every environment where all listed
conditions are defined and nonzero, `eval lhs = eval rhs`.

Checker soundness derives definedness of `lhs`/`rhs` from accepted denominator
coverage; callers should not supply separate, unconnected `Defined` premises. -/
def Claim.proposition (c : Claim) (conditions : List Expr) : Prop :=
  ∀ env : Env ℚ,
    (∀ e ∈ conditions ++ c.knownAssumptions, Defined env e ∧
      ∃ v, eval env e = some v ∧ v ≠ 0) →
    eval env c.lhs = eval env c.rhs

end MathEvidence.Checkers.RationalEquality
