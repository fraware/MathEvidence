/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Encoding.Finite
import MathEvidence.IR.FinitePredicate.Soundness

/-!
# Finite-counterexample Mathlib bridge (ME-RV-042)

Transport theorems from `isCounterexample = true` / `checkBool_sound` into
ordinary negated universal / existential-refutation propositions.

Bounded Int theorems explicitly carry lower and upper bounds.
-/

namespace MathEvidence.Checkers.Counterexample.Bridge

open MathEvidence.IR.FinitePredicate
open MathEvidence.Encoding.Finite
open MathEvidence.Checkers.Counterexample

/-- Package: checker acceptance implies the IR claim proposition. -/
theorem checkBool_implies_proposition
    (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.witness :=
  checkBool_sound req cert h

/-- Shared contradiction: IR false vs Mathlib-true interpretation. -/
private theorem interprets_false_true_false {p : Pred} {env : Env}
    (hfalse : InterpretsPred p env false) (htrue : InterpretsPred p env true) :
    False := by
  simp [InterpretsPred] at hfalse htrue
  simp [hfalse] at htrue

/-- Fin-as-Nat: IR counterexample at `w` implies ¬∀ x : Fin n, ↑x = k. -/
theorem fin_nat_eq_refutation {n k : Nat}
    (w : Fin n)
    (h : isCounterexample [.nat w.val] (.eq (.var 0) (.lit (.nat k))) = true) :
    ¬ ∀ x : Fin n, (x : Nat) = k := by
  intro hall
  have hp := (isCounterexample_iff [.nat w.val] (.eq (.var 0) (.lit (.nat k)))).1 h
  have hfalse : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envFin w) false := by
    simpa [InterpretsPred, eval, envOfAssignment, envFin] using hp
  have hw : (w : Nat) = k := hall w
  have htrue : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envFin w) true := by
    -- Use `decide (w.val = k)` form, then close with `hw`.
    have := interprets_fin_eq_nat w k
    simpa [InterpretsPred, hw, decide_eq_true_eq] using this
  exact interprets_false_true_false hfalse htrue

/-- Bool: IR counterexample implies ¬∀ b : Bool, b = target. -/
theorem bool_eq_refutation (target : Bool) (w : Bool)
    (h : isCounterexample [.bool w] (.eq (.var 0) (.lit (.bool target))) = true) :
    ¬ ∀ b : Bool, b = target := by
  intro hall
  have hp := (isCounterexample_iff [.bool w] (.eq (.var 0) (.lit (.bool target)))).1 h
  have hfalse : InterpretsPred (.eq (.var 0) (.lit (.bool target))) (envBool w) false := by
    simpa [InterpretsPred, eval, envOfAssignment, envBool] using hp
  have hw : w = target := hall w
  have htrue : InterpretsPred (.eq (.var 0) (.lit (.bool target))) (envBool w) true := by
    have := interprets_bool_eq_lit w target
    simpa [InterpretsPred, hw, decide_eq_true_eq] using this
  exact interprets_false_true_false hfalse htrue

/-- Bounded Nat: IR counterexample implies ¬∀ x : Nat, x ≤ ub → x = k. -/
theorem bounded_nat_eq_refutation (ub k w : Nat)
    (hwBound : w ≤ ub)
    (h : isCounterexample [.nat w] (.eq (.var 0) (.lit (.nat k))) = true) :
    ¬ ∀ x : Nat, x ≤ ub → x = k := by
  intro hall
  have hp := (isCounterexample_iff [.nat w] (.eq (.var 0) (.lit (.nat k)))).1 h
  have hfalse : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envNat w) false := by
    simpa [InterpretsPred, eval, envOfAssignment, envNat] using hp
  have hw : w = k := hall w hwBound
  have htrue : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envNat w) true := by
    have := interprets_nat_eq w k
    simpa [InterpretsPred, hw, decide_eq_true_eq] using this
  exact interprets_false_true_false hfalse htrue

/-- Bounded Int: IR counterexample implies ¬∀ x : Int, lo ≤ x → x ≤ hi → x = k.

Bounds `lo`/`hi` are explicit parameters of the theorem (ME-RV-042). -/
theorem bounded_int_eq_refutation (lo hi k w : Int)
    (hlo : lo ≤ w) (hhi : w ≤ hi)
    (h : isCounterexample [.int w] (.eq (.var 0) (.lit (.int k))) = true) :
    ¬ ∀ x : Int, lo ≤ x → x ≤ hi → x = k := by
  intro hall
  have hp := (isCounterexample_iff [.int w] (.eq (.var 0) (.lit (.int k)))).1 h
  have hfalse : InterpretsPred (.eq (.var 0) (.lit (.int k))) (envInt w) false := by
    simpa [InterpretsPred, eval, envOfAssignment, envInt] using hp
  have hw : w = k := hall w hlo hhi
  have htrue : InterpretsPred (.eq (.var 0) (.lit (.int k))) (envInt w) true := by
    have := interprets_int_eq w k
    simpa [InterpretsPred, hw, decide_eq_true_eq] using this
  exact interprets_false_true_false hfalse htrue

/-- Existential Fin form: IR counterexample yields ∃ x : Fin n, ¬(↑x = k). -/
theorem exists_fin_nat_ne {n k : Nat}
    (w : Fin n)
    (h : isCounterexample [.nat w.val] (.eq (.var 0) (.lit (.nat k))) = true) :
    ∃ x : Fin n, ¬ ((x : Nat) = k) := by
  refine ⟨w, ?_⟩
  intro hw
  have hp := (isCounterexample_iff [.nat w.val] (.eq (.var 0) (.lit (.nat k)))).1 h
  have hfalse : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envFin w) false := by
    simpa [InterpretsPred, eval, envOfAssignment, envFin] using hp
  have htrue : InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envFin w) true := by
    have := interprets_fin_eq_nat w k
    simpa [InterpretsPred, hw, decide_eq_true_eq] using this
  exact interprets_false_true_false hfalse htrue

end MathEvidence.Checkers.Counterexample.Bridge
