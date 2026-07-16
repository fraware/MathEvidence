/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Field.Rat
import Mathlib.Data.List.Basic
import Mathlib.Tactic.Ring
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.IR.RationalExpr

/-!
Computable sparse polynomials with evaluation homomorphism lemmas used by
`Soundness` / `RationalEquality`.
-/

structure Term where
  vars : List Nat
  coeff : Int
  deriving DecidableEq, Repr, Inhabited

abbrev Poly := List Term

namespace Poly

def C (n : Int) : Poly := if n = 0 then [] else [{ vars := [], coeff := n }]
def X (i : Nat) : Poly := [{ vars := [i], coeff := 1 }]
def zero : Poly := []
def one : Poly := C 1

def insertSorted (i : Nat) : List Nat → List Nat
  | [] => [i]
  | j :: js => if i ≤ j then i :: j :: js else j :: insertSorted i js

def sortNats : List Nat → List Nat
  | [] => []
  | i :: is => insertSorted i (sortNats is)

def Term.sortVars (t : Term) : Term := { t with vars := sortNats t.vars }

def evalTerm (env : Env ℚ) (t : Term) : ℚ :=
  (t.coeff : ℚ) * t.vars.foldl (fun acc i => acc * env i) (1 : ℚ)

def eval (env : Env ℚ) (p : Poly) : ℚ :=
  p.foldl (fun acc t => acc + evalTerm env t) 0

@[simp] theorem eval_nil (env : Env ℚ) : eval env ([] : Poly) = 0 := rfl

def mulTerm (t u : Term) : Term :=
  Term.sortVars { vars := t.vars ++ u.vars, coeff := t.coeff * u.coeff }

def add (p q : Poly) : Poly := p ++ q
def neg (p : Poly) : Poly := p.map fun t => { t with coeff := -t.coeff }
def sub (p q : Poly) : Poly := add p (neg q)
def mul (p q : Poly) : Poly := p.flatMap fun t => q.map (mulTerm t)

def pow (p : Poly) : Nat → Poly
  | 0 => one
  | k + 1 => mul (pow p k) p

def combineLike (p : Poly) : Poly :=
  match p with
  | [] => []
  | t :: rest =>
    let t := Term.sortVars t
    let same := rest.filter fun u => (Term.sortVars u).vars = t.vars
    let others := rest.filter fun u => (Term.sortVars u).vars ≠ t.vars
    let c := t.coeff + same.foldl (fun acc u => acc + u.coeff) 0
    let others' := combineLike others
    if c = 0 then others' else { vars := t.vars, coeff := c } :: others'
termination_by p.length
decreasing_by
  all_goals
    simp_wf
    exact Nat.lt_succ_of_le (List.length_filter_le _ _)

/-! ### Evaluation helpers -/

private theorem foldl_add_const (env : Env ℚ) (a : ℚ) (p : Poly) :
    p.foldl (fun acc t => acc + evalTerm env t) a =
      a + p.foldl (fun acc t => acc + evalTerm env t) 0 := by
  induction p generalizing a with
  | nil => simp
  | cons t ts ih =>
    simp only [List.foldl_cons]
    rw [ih (a + evalTerm env t), ih (0 + evalTerm env t)]
    ring

theorem eval_cons (env : Env ℚ) (t : Term) (rest : Poly) :
    eval env (t :: rest) = evalTerm env t + eval env rest := by
  change (t :: rest).foldl (fun acc t => acc + evalTerm env t) 0 =
    evalTerm env t + rest.foldl (fun acc t => acc + evalTerm env t) 0
  rw [List.foldl_cons, foldl_add_const, zero_add]

theorem eval_zero (env : Env ℚ) : eval env zero = 0 := rfl

theorem eval_C (env : Env ℚ) (n : Int) : eval env (C n) = (n : ℚ) := by
  simp only [C, eval, evalTerm]
  split_ifs with h
  · simp [h]
  · simp

theorem eval_X (env : Env ℚ) (i : Nat) : eval env (X i) = env i := by
  simp [X, eval, evalTerm]

theorem eval_add (env : Env ℚ) (p q : Poly) :
    eval env (add p q) = eval env p + eval env q := by
  simp only [add, eval]
  rw [List.foldl_append, foldl_add_const]

theorem evalTerm_neg_coeff (env : Env ℚ) (t : Term) :
    evalTerm env { t with coeff := -t.coeff } = -evalTerm env t := by
  simp only [evalTerm, Int.cast_neg]
  ring

theorem eval_neg (env : Env ℚ) (p : Poly) :
    eval env (neg p) = -eval env p := by
  induction p with
  | nil => rfl
  | cons t ts ih =>
    calc
      eval env (neg (t :: ts))
          = eval env ({ t with coeff := -t.coeff } :: neg ts) := by rfl
      _ = evalTerm env { t with coeff := -t.coeff } + eval env (neg ts) :=
        eval_cons env _ _
      _ = -evalTerm env t + eval env (neg ts) := by rw [evalTerm_neg_coeff]
      _ = -evalTerm env t + -eval env ts := by rw [ih]
      _ = -(evalTerm env t + eval env ts) := by ring
      _ = -eval env (t :: ts) := by rw [eval_cons]

theorem eval_sub (env : Env ℚ) (p q : Poly) :
    eval env (sub p q) = eval env p - eval env q := by
  simp only [sub, eval_add, eval_neg, sub_eq_add_neg]

private theorem foldl_mul_insertSorted (env : Env ℚ) (i : Nat) (xs : List Nat) (acc : ℚ) :
    (insertSorted i xs).foldl (fun a j => a * env j) acc =
      xs.foldl (fun a j => a * env j) (acc * env i) := by
  induction xs generalizing acc with
  | nil => simp [insertSorted]
  | cons j js ih =>
    simp only [insertSorted]
    split_ifs
    · simp [List.foldl_cons, mul_assoc]
    · simp only [List.foldl_cons]
      rw [ih]
      congr 1
      ring

private theorem foldl_mul_sortNats (env : Env ℚ) (xs : List Nat) (acc : ℚ) :
    (sortNats xs).foldl (fun a j => a * env j) acc =
      xs.foldl (fun a j => a * env j) acc := by
  induction xs generalizing acc with
  | nil => simp [sortNats]
  | cons i is ih =>
    simp only [sortNats, List.foldl_cons]
    rw [foldl_mul_insertSorted, ih]

theorem evalTerm_sortVars (env : Env ℚ) (t : Term) :
    evalTerm env (Term.sortVars t) = evalTerm env t := by
  simp only [Term.sortVars, evalTerm]
  rw [foldl_mul_sortNats]

private theorem foldl_mul_append (env : Env ℚ) (xs ys : List Nat) (acc : ℚ) :
    (xs ++ ys).foldl (fun a j => a * env j) acc =
      ys.foldl (fun a j => a * env j) (xs.foldl (fun a j => a * env j) acc) := by
  exact List.foldl_append (fun a j => a * env j) acc xs ys

private theorem foldl_mul_const (env : Env ℚ) (a : ℚ) (xs : List Nat) :
    xs.foldl (fun acc i => acc * env i) a =
      a * xs.foldl (fun acc i => acc * env i) 1 := by
  induction xs generalizing a with
  | nil => simp
  | cons i is ih =>
    simp only [List.foldl_cons]
    rw [ih (a * env i), ih (1 * env i)]
    ring

theorem evalTerm_mulTerm (env : Env ℚ) (t u : Term) :
    evalTerm env (mulTerm t u) = evalTerm env t * evalTerm env u := by
  unfold mulTerm
  rw [evalTerm_sortVars]
  simp only [evalTerm, Int.cast_mul]
  rw [foldl_mul_append, foldl_mul_const]
  ring

private theorem eval_map_mulTerm (env : Env ℚ) (t : Term) (q : Poly) :
    eval env (q.map (mulTerm t)) = evalTerm env t * eval env q := by
  induction q with
  | nil => simp [eval]
  | cons u us ih =>
    calc
      eval env ((u :: us).map (mulTerm t))
          = eval env (mulTerm t u :: us.map (mulTerm t)) := by rfl
      _ = evalTerm env (mulTerm t u) + eval env (us.map (mulTerm t)) :=
        eval_cons env _ _
      _ = evalTerm env t * evalTerm env u + evalTerm env t * eval env us := by
        rw [evalTerm_mulTerm, ih]
      _ = evalTerm env t * (evalTerm env u + eval env us) := by ring
      _ = evalTerm env t * eval env (u :: us) := by rw [eval_cons]

theorem eval_mul (env : Env ℚ) (p q : Poly) :
    eval env (mul p q) = eval env p * eval env q := by
  induction p with
  | nil => simp [mul, eval, List.flatMap_nil]
  | cons t ts ih =>
    calc
      eval env (mul (t :: ts) q)
          = eval env (q.map (mulTerm t) ++ ts.flatMap fun s => q.map (mulTerm s)) := by
            simp [mul, List.flatMap_cons]
      _ = eval env (q.map (mulTerm t)) +
            eval env (ts.flatMap fun s => q.map (mulTerm s)) := eval_add env _ _
      _ = evalTerm env t * eval env q + eval env ts * eval env q := by
        rw [eval_map_mulTerm, ← ih]; rfl
      _ = (evalTerm env t + eval env ts) * eval env q := by ring
      _ = eval env (t :: ts) * eval env q := by rw [eval_cons]

theorem eval_pow (env : Env ℚ) (p : Poly) (k : Nat) :
    eval env (pow p k) = eval env p ^ k := by
  induction k with
  | zero => simp [pow, one, eval_C]
  | succ k ih =>
    simp only [pow, eval_mul, ih, pow_succ]

/-! ### `combineLike` preserves evaluation -/

private def monom (env : Env ℚ) (vars : List Nat) : ℚ :=
  vars.foldl (fun acc i => acc * env i) (1 : ℚ)

theorem evalTerm_eq_coeff_monom (env : Env ℚ) (t : Term) :
    evalTerm env t = (t.coeff : ℚ) * monom env (Term.sortVars t).vars := by
  simp only [evalTerm, monom, Term.sortVars]
  rw [← foldl_mul_sortNats]

private theorem foldl_coeff_add_const (a : Int) (ts : List Term) :
    ts.foldl (fun acc u => acc + u.coeff) a =
      a + ts.foldl (fun acc u => acc + u.coeff) 0 := by
  induction ts generalizing a with
  | nil => simp
  | cons u us ih =>
    simp only [List.foldl_cons]
    rw [ih (a + u.coeff), ih (0 + u.coeff)]
    ring

private theorem eval_sum_same (env : Env ℚ) (vars : List Nat) (ts : List Term)
    (h : ∀ u ∈ ts, (Term.sortVars u).vars = vars) :
    eval env ts =
      (ts.foldl (fun acc u => acc + u.coeff) 0 : Int) * monom env vars := by
  induction ts with
  | nil => simp [eval, monom]
  | cons u us ih =>
    have hu := h u (by simp)
    have hus : ∀ v ∈ us, (Term.sortVars v).vars = vars := fun v hv =>
      h v (List.mem_cons_of_mem _ hv)
    rw [eval_cons, ih hus, evalTerm_eq_coeff_monom, hu]
    simp only [List.foldl_cons]
    have hfold :
        (us.foldl (fun acc u => acc + u.coeff) (0 + u.coeff) : Int) =
          u.coeff + us.foldl (fun acc u => acc + u.coeff) 0 := by
      simpa [zero_add] using foldl_coeff_add_const u.coeff us
    rw [hfold]
    simp only [Int.cast_add]
    ring

private theorem eval_filter_partition (env : Env ℚ) (p : Poly) (pred : Term → Bool) :
    eval env p =
      eval env (p.filter pred) + eval env (p.filter fun t => !pred t) := by
  induction p with
  | nil => simp [eval]
  | cons t ts ih =>
    rw [eval_cons]
    cases hpred : pred t
    · -- t goes to the complement filter
      have h1 : (t :: ts).filter pred = ts.filter pred := by
        simp [List.filter, hpred]
      have h2 : (t :: ts).filter (fun u => !pred u) =
          t :: ts.filter (fun u => !pred u) := by
        simp [List.filter, hpred]
      rw [h1, h2, eval_cons, ih]
      ring
    · have h1 : (t :: ts).filter pred = t :: ts.filter pred := by
        simp [List.filter, hpred]
      have h2 : (t :: ts).filter (fun u => !pred u) =
          ts.filter (fun u => !pred u) := by
        simp [List.filter, hpred]
      rw [h1, h2, eval_cons, ih]
      ring

private theorem combineLike_nil : combineLike ([] : Poly) = [] := by
  simp [combineLike]

private theorem combineLike_cons (t : Term) (rest : Poly) :
    combineLike (t :: rest) =
      let t' := Term.sortVars t
      let same := rest.filter fun u => (Term.sortVars u).vars = t'.vars
      let others := rest.filter fun u => (Term.sortVars u).vars ≠ t'.vars
      let c := t'.coeff + same.foldl (fun acc u => acc + u.coeff) 0
      if c = 0 then combineLike others
      else { vars := t'.vars, coeff := c } :: combineLike others := by
  simp [combineLike]

theorem eval_combineLike (env : Env ℚ) (p : Poly) :
    eval env (combineLike p) = eval env p := by
  suffices h : ∀ n, ∀ q : Poly, q.length ≤ n → eval env (combineLike q) = eval env q by
    exact h p.length p le_rfl
  intro n
  induction n with
  | zero =>
    intro q hq
    have hq0 : q.length = 0 := Nat.eq_zero_of_le_zero hq
    have : q = [] := List.eq_nil_of_length_eq_zero hq0
    subst this
    simp [combineLike_nil, eval]
  | succ n ih =>
    intro q hq
    match q with
    | [] => simp [combineLike_nil, eval]
    | t :: rest =>
      have hlen : rest.length ≤ n := Nat.le_of_succ_le_succ (by simpa using hq)
      rw [combineLike_cons]
      set t' := Term.sortVars t with ht'
      set same := rest.filter fun u => (Term.sortVars u).vars = t'.vars
      set others := rest.filter fun u => (Term.sortVars u).vars ≠ t'.vars
      set c := t'.coeff + same.foldl (fun acc u => acc + u.coeff) 0
      have hothers_len : others.length ≤ n :=
        Nat.le_trans (List.length_filter_le _ _) hlen
      have ih_others : eval env (combineLike others) = eval env others :=
        ih others hothers_len
      have hpart : eval env rest = eval env same + eval env others := by
        -- same = filter (decide (vars = …)); others = filter (≠) which equals filter (!=)
        have hneg :
            (rest.filter fun u => (Term.sortVars u).vars ≠ t'.vars) =
              rest.filter fun u => !decide ((Term.sortVars u).vars = t'.vars) := by
          apply List.filter_congr
          intro u _
          simp [decide_not]
        -- rewrite others and apply partition
        simpa [same, others, hneg] using
          (eval_filter_partition env rest fun u =>
            decide ((Term.sortVars u).vars = t'.vars))
      have hsame :
          eval env same =
            (same.foldl (fun acc u => acc + u.coeff) 0 : Int) * monom env t'.vars := by
        refine eval_sum_same env t'.vars same ?_
        intro u hu
        simpa using (List.of_mem_filter hu)
      have ht : evalTerm env t = (t'.coeff : ℚ) * monom env t'.vars := by
        simpa [t', ht'] using evalTerm_eq_coeff_monom env t
      have hc_eval :
          (t'.coeff : ℚ) * monom env t'.vars + eval env same =
            (c : ℚ) * monom env t'.vars := by
        simp only [c, hsame, Int.cast_add]
        ring
      -- Finish by cases on c.
      dsimp only []
      split_ifs with hc
      · -- c = 0 ⇒ combined monomial vanishes; result is eval others.
        have hcZ : c = 0 := by
          simpa [c] using hc
        calc
          eval env (combineLike others)
              = eval env others := ih_others
          _ = (0 : ℚ) * monom env t'.vars + eval env others := by ring
          _ = (c : ℚ) * monom env t'.vars + eval env others := by simp [hcZ]
          _ = (t'.coeff : ℚ) * monom env t'.vars + eval env same + eval env others := by
                rw [← hc_eval, add_assoc]
          _ = evalTerm env t + eval env rest := by
                rw [ht, hpart, add_assoc]
          _ = eval env (t :: rest) := (eval_cons env t rest).symm
      · calc
          eval env ({ vars := t'.vars, coeff := c } :: combineLike others)
              = evalTerm env ⟨t'.vars, c⟩ + eval env (combineLike others) :=
                eval_cons env _ _
          _ = (c : ℚ) * monom env t'.vars + eval env others := by
                simp only [evalTerm, monom, ih_others]
          _ = (t'.coeff : ℚ) * monom env t'.vars + eval env same + eval env others := by
                rw [← hc_eval, add_assoc]
          _ = evalTerm env t + eval env rest := by
                rw [ht, hpart, add_assoc]
          _ = eval env (t :: rest) := (eval_cons env t rest).symm

theorem eval_eq_zero_of_combineLike_nil (env : Env ℚ) (p : Poly)
    (h : combineLike p = []) : eval env p = 0 := by
  have := eval_combineLike env p
  simpa [h, eval_nil] using this.symm

end Poly

def toFrac : Expr → Option (Poly × Poly)
  | .var i => some (Poly.X i, Poly.one)
  | .int n => some (Poly.C n, Poly.one)
  | .rat n d =>
    if d = 0 then none
    else some (Poly.C n, Poly.C (Int.ofNat d))
  | .neg e => do
    let (n, d) ← toFrac e
    pure (Poly.neg n, d)
  | .add a b => do
    let (n1, d1) ← toFrac a
    let (n2, d2) ← toFrac b
    pure (Poly.add (Poly.mul n1 d2) (Poly.mul n2 d1), Poly.mul d1 d2)
  | .sub a b => do
    let (n1, d1) ← toFrac a
    let (n2, d2) ← toFrac b
    pure (Poly.sub (Poly.mul n1 d2) (Poly.mul n2 d1), Poly.mul d1 d2)
  | .mul a b => do
    let (n1, d1) ← toFrac a
    let (n2, d2) ← toFrac b
    pure (Poly.mul n1 n2, Poly.mul d1 d2)
  | .pow b k => do
    let (n, d) ← toFrac b
    pure (Poly.pow n k, Poly.pow d k)
  | .div a b => do
    let (n1, d1) ← toFrac a
    let (n2, d2) ← toFrac b
    pure (Poly.mul n1 d2, Poly.mul d1 n2)

def differenceNumerator (lhs rhs : Expr) : Option Poly := do
  let (nl, dl) ← toFrac lhs
  let (nr, dr) ← toFrac rhs
  pure (Poly.sub (Poly.mul nl dr) (Poly.mul nr dl))

def polyEqual (lhs rhs : Expr) : Bool :=
  match differenceNumerator lhs rhs with
  | some p => decide (Poly.combineLike p = [])
  | none => false

def evalPoly (env : Env ℚ) (p : Poly) : ℚ := Poly.eval env p

@[simp] theorem evalPoly_zero (env : Env ℚ) : evalPoly env Poly.zero = 0 := Poly.eval_zero env
@[simp] theorem evalPoly_one (env : Env ℚ) : evalPoly env Poly.one = 1 := by
  simp [evalPoly, Poly.one, Poly.eval_C]
@[simp] theorem evalPoly_C (env : Env ℚ) (n : ℤ) : evalPoly env (Poly.C n) = (n : ℚ) :=
  Poly.eval_C env n
@[simp] theorem evalPoly_X (env : Env ℚ) (i : Nat) : evalPoly env (Poly.X i) = env i :=
  Poly.eval_X env i

theorem evalPoly_add (env : Env ℚ) (p q : Poly) :
    evalPoly env (Poly.add p q) = evalPoly env p + evalPoly env q := Poly.eval_add env p q
theorem evalPoly_mul (env : Env ℚ) (p q : Poly) :
    evalPoly env (Poly.mul p q) = evalPoly env p * evalPoly env q := Poly.eval_mul env p q
theorem evalPoly_neg (env : Env ℚ) (p : Poly) :
    evalPoly env (Poly.neg p) = -evalPoly env p := Poly.eval_neg env p
theorem evalPoly_sub (env : Env ℚ) (p q : Poly) :
    evalPoly env (Poly.sub p q) = evalPoly env p - evalPoly env q := Poly.eval_sub env p q
theorem evalPoly_pow (env : Env ℚ) (p : Poly) (k : Nat) :
    evalPoly env (Poly.pow p k) = evalPoly env p ^ k := Poly.eval_pow env p k

end MathEvidence.IR.RationalExpr
