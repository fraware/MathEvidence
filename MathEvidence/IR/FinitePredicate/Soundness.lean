/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.FinitePredicate.Eval

namespace MathEvidence.IR.FinitePredicate

/-!
# Soundness

`isCounterexample` means the predicate evaluates to `false` at the witness.
Exhaustive search / absence claims are out of scope.
-/

theorem isCounterexample_iff (σ : Assignment) (p : Pred) :
    isCounterexample σ p = true ↔ eval σ p = some false := by
  unfold isCounterexample
  cases h : eval σ p with
  | none => simp
  | some b =>
    cases b <;> simp

theorem eval_not_true_of_counterexample (σ : Assignment) (p : Pred)
    (h : isCounterexample σ p = true) :
    ¬ (eval σ p = some true) := by
  rw [isCounterexample_iff] at h
  intro ht
  simp [h] at ht

end MathEvidence.IR.FinitePredicate
