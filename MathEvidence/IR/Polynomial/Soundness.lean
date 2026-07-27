/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.List
import Mathlib.Algebra.MvPolynomial.Basic
import Mathlib.Algebra.MvPolynomial.CommRing
import Mathlib.Data.Finsupp.Basic
import Mathlib.Data.Vector.Basic
import Mathlib.RingTheory.Ideal.Basic
import Mathlib.RingTheory.Ideal.BigOperators
import Mathlib.RingTheory.Ideal.Span
import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring
import MathEvidence.IR.Polynomial.Interpret
import MathEvidence.IR.Polynomial.Normalize

/-!
# Soundness of sparse polynomial arithmetic / normalization

ME-RV-031: computational IR operations preserve `MvPolynomial` semantics.
-/

namespace MathEvidence.IR.Polynomial

open MvPolynomial
open MvPolynomial (C monomial_mul monomial_zero')

-- `Term.monomial` shadows bare `MvPolynomial.monomial`.
local notation "mvMonomial" => MvPolynomial.monomial

@[simp] theorem Monomial.toFinsupp_one (m : Nat) :
    (Monomial.one m).toFinsupp = 0 := by
  ext i
  simp [Monomial.toFinsupp, Monomial.one, Mathlib.Vector.get_replicate]

@[simp] theorem evalTerms_nil {m : Nat} : evalTerms ([] : List (Term m)) = 0 := by
  simp [evalTerms]

@[simp] theorem evalTerms_cons {m : Nat} (t : Term m) (ts : List (Term m)) :
    evalTerms (t :: ts) = t.eval + evalTerms ts := by
  simp [evalTerms, List.sum_cons]

theorem RawSparsePoly.eval_zero (m : Nat) :
    (RawSparsePoly.zero m).eval = 0 := by
  simp [RawSparsePoly.eval, RawSparsePoly.zero]

theorem SparsePoly.eval_zero (m : Nat) :
    (SparsePoly.zero m).eval = 0 := by
  simp [SparsePoly.eval, SparsePoly.zero]

theorem RawSparsePoly.eval_add {m : Nat} (a b : RawSparsePoly m) :
    (a.add b).eval = a.eval + b.eval := by
  simp [RawSparsePoly.add, RawSparsePoly.eval, evalTerms, List.map_append, List.sum_append]

private theorem Term.eval_neg {m : Nat} (t : Term m) :
    Term.eval { t with coefficient := -t.coefficient } = -t.eval := by
  simp [Term.eval, map_neg]

theorem RawSparsePoly.eval_neg {m : Nat} (a : RawSparsePoly m) :
    a.neg.eval = -a.eval := by
  simp only [RawSparsePoly.neg, RawSparsePoly.eval, evalTerms, List.map_map]
  induction a.terms with
  | nil => simp
  | cons t ts ih =>
    simp only [List.map_cons, List.sum_cons, Function.comp_apply, Term.eval_neg, ih]
    abel

theorem RawSparsePoly.eval_sub {m : Nat} (a b : RawSparsePoly m) :
    (a.sub b).eval = a.eval - b.eval := by
  simp [RawSparsePoly.sub, RawSparsePoly.eval_add, RawSparsePoly.eval_neg, sub_eq_add_neg]

private theorem Monomial.toFinsupp_mul {m : Nat} (a b : Monomial m) :
    (Monomial.mul a b).toFinsupp = a.toFinsupp + b.toFinsupp := by
  ext i
  simp [Monomial.toFinsupp, Monomial.mul, Mathlib.Vector.get_map₂]

private theorem Term.eval_mul {m : Nat} (ta tb : Term m) :
    Term.eval ⟨ta.coefficient * tb.coefficient, Monomial.mul ta.monomial tb.monomial⟩ =
      ta.eval * tb.eval := by
  simp only [Term.eval, Monomial.toMv, Monomial.toFinsupp_mul]
  have hmon :
      (mvMonomial (ta.monomial.toFinsupp + tb.monomial.toFinsupp) (1 : ℤ) :
          MvPolynomial (Fin m) ℤ) =
        mvMonomial ta.monomial.toFinsupp (1 : ℤ) *
          mvMonomial tb.monomial.toFinsupp (1 : ℤ) := by
    simp [monomial_mul]
  rw [hmon, map_mul]
  ring

private theorem evalTerms_map_mul_left {m : Nat} (ta : Term m) (tbs : List (Term m)) :
    evalTerms
        (tbs.map fun tb =>
          ({
            coefficient := ta.coefficient * tb.coefficient
            monomial := Monomial.mul ta.monomial tb.monomial
          } : Term m)) =
      ta.eval * evalTerms tbs := by
  induction tbs with
  | nil => simp [evalTerms, mul_zero]
  | cons tb tbs ih =>
    simp only [List.map_cons, evalTerms_cons, Term.eval_mul, ih, mul_add]

private theorem evalTerms_flatMap_mul {m : Nat} (tas tbs : List (Term m)) :
    evalTerms
        (tas.flatMap fun ta =>
          tbs.map fun tb =>
            ({
              coefficient := ta.coefficient * tb.coefficient
              monomial := Monomial.mul ta.monomial tb.monomial
            } : Term m)) =
      evalTerms tas * evalTerms tbs := by
  induction tas with
  | nil => simp [evalTerms, List.flatMap_nil, mul_zero]
  | cons ta tas ih =>
    have happ :
        evalTerms
            ((tbs.map fun tb =>
                ({
                  coefficient := ta.coefficient * tb.coefficient
                  monomial := Monomial.mul ta.monomial tb.monomial
                } : Term m)) ++
              (tas.flatMap fun ta =>
                tbs.map fun tb =>
                  ({
                    coefficient := ta.coefficient * tb.coefficient
                    monomial := Monomial.mul ta.monomial tb.monomial
                  } : Term m))) =
          evalTerms
              (tbs.map fun tb =>
                ({
                  coefficient := ta.coefficient * tb.coefficient
                  monomial := Monomial.mul ta.monomial tb.monomial
                } : Term m)) +
            evalTerms
              (tas.flatMap fun ta =>
                tbs.map fun tb =>
                  ({
                    coefficient := ta.coefficient * tb.coefficient
                    monomial := Monomial.mul ta.monomial tb.monomial
                  } : Term m)) := by
      simp [evalTerms, List.map_append, List.sum_append]
    simp only [List.flatMap_cons]
    rw [happ, evalTerms_map_mul_left, ih, evalTerms_cons, add_mul]

theorem RawSparsePoly.eval_mul {m : Nat} (a b : RawSparsePoly m) :
    (a.mul b).eval = a.eval * b.eval := by
  simpa [RawSparsePoly.mul, RawSparsePoly.eval] using evalTerms_flatMap_mul a.terms b.terms

private theorem mergeTerm_eval {m : Nat} (acc : List (Term m)) (t : Term m) :
    evalTerms (mergeTerm acc t) = evalTerms acc + t.eval := by
  induction acc with
  | nil =>
    by_cases hc : t.coefficient = 0
    · simp [mergeTerm, hc, Term.eval]
    · have hcB : (t.coefficient == 0) = false := by
        simp [beq_eq_false_iff_ne, hc]
      simp [mergeTerm, hcB]
  | cons u us ih =>
    by_cases hc : t.coefficient = 0
    · simp [mergeTerm, hc, Term.eval]
    · have hcB : (t.coefficient == 0) = false := by
        simp [beq_eq_false_iff_ne, hc]
      by_cases hm : u.monomial = t.monomial
      · by_cases hz : u.coefficient + t.coefficient = 0
        · have hzB : (u.coefficient + t.coefficient == 0) = true := by
            simpa [beq_iff_eq] using hz
          have hmB : (u.monomial == t.monomial) = true := by
            simpa [beq_iff_eq] using hm
          have hmerge : mergeTerm (u :: us) t = us := by
            simp [mergeTerm, hcB, hmB, hzB]
          rw [hmerge, evalTerms_cons]
          have hcancel : u.eval + t.eval = 0 := by
            simp only [Term.eval]
            rw [hm, ← add_mul, ← map_add (f := C (R := ℤ)), hz, map_zero, zero_mul]
          -- evalTerms us = u.eval + evalTerms us + t.eval
          rw [show u.eval + evalTerms us + t.eval =
                evalTerms us + (u.eval + t.eval) by abel, hcancel, add_zero]
        · have hzB : (u.coefficient + t.coefficient == 0) = false := by
            simp [beq_eq_false_iff_ne, hz]
          have hmB : (u.monomial == t.monomial) = true := by
            simpa [beq_iff_eq] using hm
          have hmerge :
              mergeTerm (u :: us) t =
                ({ u with coefficient := u.coefficient + t.coefficient } : Term m) :: us := by
            simp [mergeTerm, hcB, hmB, hzB]
          rw [hmerge, evalTerms_cons, evalTerms_cons]
          -- merged term eval = u.eval + t.eval when monoms equal
          have hterm :
              Term.eval
                  ({ u with coefficient := u.coefficient + t.coefficient } : Term m) =
                u.eval + t.eval := by
            simp only [Term.eval]
            rw [hm, map_add, add_mul]
          rw [hterm]
          abel
      · have hmB : (u.monomial == t.monomial) = false := by
          simp [beq_eq_false_iff_ne, hm]
        have hmerge : mergeTerm (u :: us) t = u :: mergeTerm us t := by
          simp [mergeTerm, hcB, hmB]
        rw [hmerge, evalTerms_cons, ih, evalTerms_cons]
        abel

private theorem collectTerms_eval {m : Nat} (terms : List (Term m)) :
    evalTerms (collectTerms terms) = evalTerms terms := by
  simp only [collectTerms]
  have fold_eval (acc : List (Term m)) (xs : List (Term m)) :
      evalTerms (xs.foldl mergeTerm acc) = evalTerms acc + evalTerms xs := by
    induction xs generalizing acc with
    | nil => simp
    | cons y ys ih =>
      rw [List.foldl_cons, ih, mergeTerm_eval, evalTerms_cons, add_assoc]
  simpa using fold_eval [] terms

theorem insertSorted_eval {m : Nat} (t : Term m) (xs : List (Term m)) :
    evalTerms (insertSorted t xs) = t.eval + evalTerms xs := by
  induction xs with
  | nil => simp [insertSorted]
  | cons u us ih =>
    by_cases hle : Monomial.le t.monomial u.monomial = true
    · simp [insertSorted, hle]
    · have hle' : Monomial.le t.monomial u.monomial = false := by
        cases h : Monomial.le t.monomial u.monomial <;> simp_all
      simp [insertSorted, hle', ih]
      abel

private theorem sortTerms_eval {m : Nat} (terms : List (Term m)) :
    evalTerms (sortTerms terms) = evalTerms terms := by
  simp only [sortTerms]
  have fold_eval (acc : List (Term m)) (xs : List (Term m)) :
      evalTerms (xs.foldl (fun a t => insertSorted t a) acc) =
        evalTerms acc + evalTerms xs := by
    induction xs generalizing acc with
    | nil => simp
    | cons y ys ih =>
      rw [List.foldl_cons, ih, insertSorted_eval, evalTerms_cons]
      abel
  simpa using fold_eval [] terms

theorem RawSparsePoly.eval_normalize {m : Nat} (p : RawSparsePoly m) :
    p.normalize.eval = p.eval := by
  simp [RawSparsePoly.normalize, SparsePoly.eval, RawSparsePoly.eval,
    sortTerms_eval, collectTerms_eval]

theorem SparsePoly.eval_normalize {m : Nat} (p : SparsePoly m) :
    p.normalize.eval = p.eval := by
  simpa [SparsePoly.normalize, SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval] using
    RawSparsePoly.eval_normalize p.toRaw

theorem SparsePoly.eval_add {m : Nat} (a b : SparsePoly m) :
    (a.add b).eval = a.eval + b.eval := by
  calc
    (a.add b).eval = (a.addRaw b).normalize.eval := by
      simp [SparsePoly.add]
    _ = (a.addRaw b).eval := RawSparsePoly.eval_normalize _
    _ = a.toRaw.eval + b.toRaw.eval := RawSparsePoly.eval_add _ _
    _ = a.eval + b.eval := by
      simp [SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval]

theorem SparsePoly.eval_neg {m : Nat} (a : SparsePoly m) :
    a.neg.eval = -a.eval := by
  calc
    a.neg.eval = a.toRaw.neg.normalize.eval := by
      simp [SparsePoly.neg]
    _ = a.toRaw.neg.eval := RawSparsePoly.eval_normalize _
    _ = -a.toRaw.eval := RawSparsePoly.eval_neg _
    _ = -a.eval := by
      simp [SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval]

theorem SparsePoly.eval_sub {m : Nat} (a b : SparsePoly m) :
    (a.sub b).eval = a.eval - b.eval := by
  calc
    (a.sub b).eval = (a.toRaw.sub b.toRaw).normalize.eval := by
      simp [SparsePoly.sub]
    _ = (a.toRaw.sub b.toRaw).eval := RawSparsePoly.eval_normalize _
    _ = a.toRaw.eval - b.toRaw.eval := RawSparsePoly.eval_sub _ _
    _ = a.eval - b.eval := by
      simp [SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval]

theorem SparsePoly.eval_mul {m : Nat} (a b : SparsePoly m) :
    (a.mul b).eval = a.eval * b.eval := by
  calc
    (a.mul b).eval = (a.mulRaw b).normalize.eval := by
      simp [SparsePoly.mul]
    _ = (a.mulRaw b).eval := RawSparsePoly.eval_normalize _
    _ = a.toRaw.eval * b.toRaw.eval := by
      simpa [SparsePoly.mulRaw] using RawSparsePoly.eval_mul a.toRaw b.toRaw
    _ = a.eval * b.eval := by
      simp [SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval]

theorem SparsePoly.eval_C (m : Nat) (c : Int) :
    (SparsePoly.C m c).eval = (MvPolynomial.C c : MvPolynomial (Fin m) ℤ) := by
  unfold SparsePoly.C
  split_ifs with h
  · have hc : c = 0 := by simpa [beq_iff_eq] using h
    simp [hc, SparsePoly.eval_zero, map_zero]
  · simp [SparsePoly.eval, evalTerms, Term.eval, Monomial.toMv, Monomial.toFinsupp_one,
      monomial_zero', mul_one]

private theorem Monomial.toFinsupp_single (m i e : Nat) (hi : i < m) :
    (Monomial.single m i e hi).toFinsupp = Finsupp.single ⟨i, hi⟩ e := by
  apply Finsupp.ext
  intro j
  simp only [Monomial.toFinsupp, Monomial.single, Mathlib.Vector.get_ofFn]
  change (if j.val = i then e else 0) = Finsupp.single (⟨i, hi⟩ : Fin m) e j
  rw [Finsupp.single_apply]
  by_cases h : (⟨i, hi⟩ : Fin m) = j
  · subst h
    simp
  · have : j.val ≠ i := by
      intro hj
      exact h (Fin.ext hj.symm)
    simp [h, this]

theorem SparsePoly.eval_X (m i : Nat) (hi : i < m) :
    (SparsePoly.X m i hi).eval = (MvPolynomial.X ⟨i, hi⟩ : MvPolynomial (Fin m) ℤ) := by
  simp only [SparsePoly.X, SparsePoly.eval, evalTerms, List.map_cons, List.map_nil, List.sum_cons,
    List.sum_nil, Term.eval, Monomial.toMv, Monomial.toFinsupp_single, add_zero, one_mul]
  simp [MvPolynomial.X, C_1]

theorem SparsePoly.eval_npow {m : Nat} (p : SparsePoly m) (n : Nat) :
    (p.npow n).eval = p.eval ^ n := by
  induction n with
  | zero =>
    simp [SparsePoly.npow, SparsePoly.eval_C, pow_zero]
  | succ n ih =>
    simp only [SparsePoly.npow, SparsePoly.eval_mul, ih, pow_succ]

/-- Congruence form used by the proof-producing Meta reifier (ME-RV-033). -/
theorem reify_add_eq {m : Nat} (a b : SparsePoly m)
    (ea eb : MvPolynomial (Fin m) ℤ)
    (ha : a.eval = ea) (hb : b.eval = eb) :
    (a.add b).eval = ea + eb :=
  (SparsePoly.eval_add a b).trans (ha ▸ hb ▸ rfl)

theorem reify_mul_eq {m : Nat} (a b : SparsePoly m)
    (ea eb : MvPolynomial (Fin m) ℤ)
    (ha : a.eval = ea) (hb : b.eval = eb) :
    (a.mul b).eval = ea * eb :=
  (SparsePoly.eval_mul a b).trans (ha ▸ hb ▸ rfl)

theorem reify_sub_eq {m : Nat} (a b : SparsePoly m)
    (ea eb : MvPolynomial (Fin m) ℤ)
    (ha : a.eval = ea) (hb : b.eval = eb) :
    (a.sub b).eval = ea - eb :=
  (SparsePoly.eval_sub a b).trans (ha ▸ hb ▸ rfl)

theorem reify_neg_eq {m : Nat} (a : SparsePoly m)
    (ea : MvPolynomial (Fin m) ℤ) (ha : a.eval = ea) :
    a.neg.eval = -ea :=
  (SparsePoly.eval_neg a).trans (ha ▸ rfl)

theorem reify_npow_eq {m : Nat} (a : SparsePoly m) (n : Nat)
    (ea : MvPolynomial (Fin m) ℤ) (ha : a.eval = ea) :
    (a.npow n).eval = ea ^ n :=
  (SparsePoly.eval_npow a n).trans (ha ▸ rfl)

theorem SparsePoly.eval_of_normalize_eq {m : Nat} (a b : SparsePoly m)
    (h : a.normalize = b.normalize) :
    a.eval = b.eval := by
  calc
    a.eval = a.normalize.eval := (SparsePoly.eval_normalize a).symm
    _ = b.normalize.eval := congrArg SparsePoly.eval h
    _ = b.eval := SparsePoly.eval_normalize b

theorem eval_linearCombinationList {m : Nat}
    (gens mults : List (SparsePoly m)) :
    (linearCombinationList gens mults).eval =
      ((List.zip gens mults).map
        (fun (pair : SparsePoly m × SparsePoly m) => pair.2.eval * pair.1.eval)).sum := by
  have step : ∀ (acc : RawSparsePoly m) (pairs : List (SparsePoly m × SparsePoly m)),
      (pairs.foldl (fun a pair => a.add (pair.2.mulRaw pair.1)) acc).normalize.eval =
        acc.eval +
          ((pairs.map
            (fun (pair : SparsePoly m × SparsePoly m) =>
              pair.2.eval * pair.1.eval)).sum) := by
    intro acc pairs
    induction pairs generalizing acc with
    | nil => simp [RawSparsePoly.eval_normalize]
    | cons p ps ih =>
      rw [List.foldl_cons, ih]
      have hmul :
          (p.2.mulRaw p.1).eval = p.2.eval * p.1.eval := by
        simpa [SparsePoly.mulRaw, SparsePoly.toRaw, SparsePoly.eval, RawSparsePoly.eval] using
          RawSparsePoly.eval_mul p.2.toRaw p.1.toRaw
      simp only [RawSparsePoly.eval_add, hmul, List.map_cons, List.sum_cons]
      abel
  have hstep := step (.zero m) (List.zip gens mults)
  simpa [linearCombinationList, RawSparsePoly.eval_zero, zero_add] using hstep

theorem SparsePoly.eval_linearCombination {m : Nat}
    (gens mults : Array (SparsePoly m)) :
    (linearCombination gens mults).eval =
      ((List.zip gens.toList mults.toList).map
        (fun (pair : SparsePoly m × SparsePoly m) => pair.2.eval * pair.1.eval)).sum := by
  simpa [linearCombination] using eval_linearCombinationList gens.toList mults.toList

/-- Equal-length generators/multipliers: ∑ qᵢ·gᵢ ∈ Ideal.span (range g). -/
theorem mem_span_sum_mul {m : Nat} {n : Nat}
    (g q : Fin n → MvPolynomial (Fin m) ℤ) :
    (∑ i, q i * g i) ∈ Ideal.span (Set.range g) := by
  refine Ideal.sum_mem _ ?_
  intro i _
  exact Ideal.mul_mem_left _ _ (Ideal.subset_span ⟨i, rfl⟩)

/-- Checker identity on normalized IR implies Mathlib ideal membership. -/
theorem mem_span_of_linearCombination {m : Nat}
    (target : SparsePoly m) (gens mults : List (SparsePoly m))
    (hlen : gens.length = mults.length)
    (hid : target.normalize = linearCombinationList gens mults) :
    target.eval ∈
      Ideal.span (Set.range fun i : Fin gens.length => (gens.get i).eval) := by
  have heval : target.eval = (linearCombinationList gens mults).eval := by
    calc
      target.eval = target.normalize.eval := (SparsePoly.eval_normalize _).symm
      _ = (linearCombinationList gens mults).eval := congrArg SparsePoly.eval hid
  rw [heval, eval_linearCombinationList]
  have hz :
      (List.zip gens mults).map
          (fun (pair : SparsePoly m × SparsePoly m) => pair.2.eval * pair.1.eval) =
        (List.ofFn fun i : Fin gens.length =>
          (mults.get (i.cast hlen)).eval * (gens.get i).eval) := by
    apply List.ext_getElem
    · simp [hlen, List.length_zip, List.length_ofFn, min_eq_left]
    · intro i hi hi'
      simp [List.getElem_zip, List.getElem_ofFn, List.get_eq_getElem]
  rw [hz, List.sum_ofFn]
  exact mem_span_sum_mul
    (fun i => (gens.get i).eval)
    (fun i => (mults.get (i.cast hlen)).eval)

end MathEvidence.IR.Polynomial
