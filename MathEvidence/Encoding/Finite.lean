/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.FinitePredicate.Eval
import MathEvidence.IR.FinitePredicate.Syntax

/-!
# Encoding — finite predicates

Reusable quotation lemmas for finite-domain IR: term and predicate interpretation
under environments (`interpret (quote _) = _` style), including Mathlib-facing
bridges for the Fin / Bool / bounded Nat / bounded Int forms used by CEX Meta.
-/

namespace MathEvidence.Encoding.Finite

open MathEvidence.IR.FinitePredicate

/-- Term interpretation under an environment. -/
def InterpretsTerm (t : Term) (env : Env) (v : Val) : Prop :=
  evalTerm env t = some v

/-- Predicate interpretation under an environment. -/
def InterpretsPred (p : Pred) (env : Env) (b : Bool) : Prop :=
  evalPred env p = some b

theorem interprets_lit (env : Env) (v : Val) :
    InterpretsTerm (.lit v) env v := by
  simp [InterpretsTerm, evalTerm]

theorem interprets_var (env : Env) (i : Nat) (v : Val)
    (h : env i = some v) :
    InterpretsTerm (.var i) env v := by
  simp [InterpretsTerm, evalTerm, h]

theorem interprets_neg_int (env : Env) (t : Term) (i : Int)
    (ht : InterpretsTerm t env (.int i)) :
    InterpretsTerm (.neg t) env (.int (-i)) := by
  simp [InterpretsTerm, evalTerm] at ht ⊢
  simp [ht]

theorem interprets_add_int (env : Env) (a b : Term) (x y : Int)
    (ha : InterpretsTerm a env (.int x)) (hb : InterpretsTerm b env (.int y)) :
    InterpretsTerm (.add a b) env (.int (x + y)) := by
  simp [InterpretsTerm, evalTerm] at ha hb ⊢
  simp [ha, hb]

theorem interprets_mul_int (env : Env) (a b : Term) (x y : Int)
    (ha : InterpretsTerm a env (.int x)) (hb : InterpretsTerm b env (.int y)) :
    InterpretsTerm (.mul a b) env (.int (x * y)) := by
  simp [InterpretsTerm, evalTerm] at ha hb ⊢
  simp [ha, hb]

theorem interprets_add_nat (env : Env) (a b : Term) (x y : Nat)
    (ha : InterpretsTerm a env (.nat x)) (hb : InterpretsTerm b env (.nat y)) :
    InterpretsTerm (.add a b) env (.nat (x + y)) := by
  simp [InterpretsTerm, evalTerm] at ha hb ⊢
  simp [ha, hb]

theorem interprets_eq (env : Env) (a b : Term) (va vb : Val)
    (ha : InterpretsTerm a env va) (hb : InterpretsTerm b env vb) :
    InterpretsPred (.eq a b) env (valEq va vb) := by
  simp [InterpretsPred, InterpretsTerm, evalPred, evalTerm] at ha hb ⊢
  simp [ha, hb]

theorem interprets_ne (env : Env) (a b : Term) (va vb : Val)
    (ha : InterpretsTerm a env va) (hb : InterpretsTerm b env vb) :
    InterpretsPred (.ne a b) env (!valEq va vb) := by
  simp [InterpretsPred, InterpretsTerm, evalPred, evalTerm] at ha hb ⊢
  simp [ha, hb]

theorem interprets_not (env : Env) (p : Pred) (b : Bool)
    (hp : InterpretsPred p env b) :
    InterpretsPred (.not p) env (!b) := by
  simp [InterpretsPred, evalPred] at hp ⊢
  simp [hp]

theorem interprets_and (env : Env) (p q : Pred) (bp bq : Bool)
    (hp : InterpretsPred p env bp) (hq : InterpretsPred q env bq) :
    InterpretsPred (.and p q) env (bp && bq) := by
  simp [InterpretsPred, evalPred] at hp hq ⊢
  simp [hp, hq]

theorem interprets_or (env : Env) (p q : Pred) (bp bq : Bool)
    (hp : InterpretsPred p env bp) (hq : InterpretsPred q env bq) :
    InterpretsPred (.or p q) env (bp || bq) := by
  simp [InterpretsPred, evalPred] at hp hq ⊢
  simp [hp, hq]

/-- Concrete bridge: `x = x` for a boolean literal environment. -/
theorem interprets_eq_refl_bool (b : Bool) :
    InterpretsPred
      (.eq (.lit (.bool b)) (.lit (.bool b)))
      (fun _ => none)
      true := by
  simp [InterpretsPred, evalPred, evalTerm, valEq]

/-! ## Mathlib-facing bridges (CEX Meta forms) -/

/-- Single Bool binder environment used by `¬ ∀ b : Bool, …`. -/
def envBool (b : Bool) : Env := fun
  | 0 => some (.bool b)
  | _ => none

/-- Single Fin binder as Nat (CEX Meta Fin encoding). -/
def envFin {n : Nat} (x : Fin n) : Env := fun
  | 0 => some (.nat x.val)
  | _ => none

/-- Single bounded-Nat binder. -/
def envNat (x : Nat) : Env := fun
  | 0 => some (.nat x)
  | _ => none

/-- Single bounded-Int binder. -/
def envInt (x : Int) : Env := fun
  | 0 => some (.int x)
  | _ => none

/-- Bool equality-to-literal interprets as Lean `decide (b = c)`. -/
theorem interprets_bool_eq_lit (b c : Bool) :
    InterpretsPred (.eq (.var 0) (.lit (.bool c))) (envBool b) (decide (b = c)) := by
  simp [InterpretsPred, evalPred, evalTerm, envBool, valEq]

/-- Bool `b = true` IR form used by CEX Meta. -/
theorem interprets_bool_eq_true (b : Bool) :
    InterpretsPred (.eq (.var 0) (.lit (.bool true))) (envBool b) (b == true) := by
  cases b <;> simp [InterpretsPred, evalPred, evalTerm, envBool, valEq]

/-- Fin-as-Nat equality to a constant. -/
theorem interprets_fin_eq_nat {n : Nat} (x : Fin n) (k : Nat) :
    InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envFin x) (decide (x.val = k)) := by
  simp [InterpretsPred, evalPred, evalTerm, envFin, valEq]

/-- Bounded Nat `x ≤ ub` IR form. -/
theorem interprets_nat_le (x ub : Nat) :
    InterpretsPred (.le (.var 0) (.lit (.nat ub))) (envNat x) (decide (x ≤ ub)) := by
  simp [InterpretsPred, evalPred, evalTerm, envNat, valLe]

/-- Bounded Nat `x = k` IR form. -/
theorem interprets_nat_eq (x k : Nat) :
    InterpretsPred (.eq (.var 0) (.lit (.nat k))) (envNat x) (decide (x = k)) := by
  simp [InterpretsPred, evalPred, evalTerm, envNat, valEq]

/-- Bounded Int `lo ≤ x` IR form. -/
theorem interprets_int_le_lo (x lo : Int) :
    InterpretsPred (.le (.lit (.int lo)) (.var 0)) (envInt x) (decide (lo ≤ x)) := by
  simp [InterpretsPred, evalPred, evalTerm, envInt, valLe]

/-- Bounded Int `x ≤ hi` IR form. -/
theorem interprets_int_le_hi (x hi : Int) :
    InterpretsPred (.le (.var 0) (.lit (.int hi))) (envInt x) (decide (x ≤ hi)) := by
  simp [InterpretsPred, evalPred, evalTerm, envInt, valLe]

/-- Bounded Int `x = k` IR form. -/
theorem interprets_int_eq (x k : Int) :
    InterpretsPred (.eq (.var 0) (.lit (.int k))) (envInt x) (decide (x = k)) := by
  simp [InterpretsPred, evalPred, evalTerm, envInt, valEq]

/-- Implication shape for CEX: IR `p → q` as `¬p ∨ q`. -/
def impliesPred (p q : Pred) : Pred :=
  .or (.not p) q

/-- Bounded-Nat Meta body `x ≤ ub → x = k` interprets as Lean implication. -/
theorem interprets_nat_le_imp_eq (x ub k : Nat) :
    InterpretsPred
      (impliesPred (.le (.var 0) (.lit (.nat ub))) (.eq (.var 0) (.lit (.nat k))))
      (envNat x)
      (decide (x ≤ ub → x = k)) := by
  simp [InterpretsPred, impliesPred, evalPred, evalTerm, envNat, valLe, valEq]

/-- Bridge: false IR evaluation of `b = true` yields Lean `b ≠ true`. -/
theorem bool_eq_true_cex (b : Bool)
    (h : InterpretsPred (.eq (.var 0) (.lit (.bool true))) (envBool b) false) :
    b ≠ true := by
  intro hb
  have : InterpretsPred (.eq (.var 0) (.lit (.bool true))) (envBool b) true := by
    simpa [hb] using interprets_bool_eq_true b
  simp [InterpretsPred] at h this
  simp [h] at this

/-- Bridge: false IR evaluation of Fin `x.val = 0` yields Lean `x.val ≠ 0`. -/
theorem fin_eq_zero_cex {n : Nat} (x : Fin n)
    (h : InterpretsPred (.eq (.var 0) (.lit (.nat 0))) (envFin x) false) :
    x.val ≠ 0 := by
  intro hx
  have : InterpretsPred (.eq (.var 0) (.lit (.nat 0))) (envFin x) true := by
    simpa [hx] using interprets_fin_eq_nat x 0
  simp [InterpretsPred] at h this
  simp [h] at this

/-- Concrete Fin-3 CEX Meta body used by examples. -/
theorem interprets_fin3_eq_zero (x : Fin 3) :
    InterpretsPred (.eq (.var 0) (.lit (.nat 0))) (envFin x) (decide (x.val = 0)) :=
  interprets_fin_eq_nat x 0

end MathEvidence.Encoding.Finite
