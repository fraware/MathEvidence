/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.Algebra.MvPolynomial.CommRing
import Mathlib.RingTheory.Ideal.Basic
import Mathlib.RingTheory.Ideal.Span
import Mathlib.RingTheory.MvPolynomial.Basic
import Mathlib.Tactic.Ring
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Encoding.Polynomial
import MathEvidence.Tactic.ReifyPolynomial

/-!
# Ideal-membership tactic (Ideal.span auto-bridge)

`mathevidence_ideal_membership` reifies a concrete goal
`f ∈ Ideal.span {g}` or `f ∈ Ideal.span {g₁, g₂}` into sparse IR, proposes
multipliers, gates on `checkMembership`, then closes with
`membership_from_witness_univariate` / `membership_from_witness_pair` /
`membership_from_witness_any` + `ring`.

Supported ambient rings:

* univariate `Polynomial ℤ` / `Polynomial ℚ`
* multivariate `MvPolynomial (Fin n) ℤ` / `ℚ` for `2 ≤ n ≤ 4`
  (Meta close wired for `n = 2`, `n = 3`, and `n = 4`)

Witness search: exact univariate division; multivariate grevlex exact division
(including non-monomial generators when `f` is an exact multiple of `g`);
monomial fast path; small pair search. Not a Gröbner completeness claim —
exact arithmetic only when a sparse quotient exists over ℤ.
-/

namespace MathEvidence.Tactic.IdealMembership

open Lean Meta Elab Tactic
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership
open MathEvidence.Tactic.ReifyPolynomial

def unsupportedMessage : String :=
  "mathevidence ideal membership: unsupported goal. Supported: concrete " ++
  "`f ∈ Ideal.span {g}` or `f ∈ Ideal.span {g₁, g₂}` over ℤ[X]/ℚ[X] or " ++
  "`MvPolynomial (Fin n) ℤ/ℚ` (2≤n≤4; Meta close for n=2,3,4) with integer " ++
  "coefficients where a sparse witness is accepted by checkMembership " ++
  "(univariate / mv exact grevlex division incl. non-monomial gens)."

/-- Build syntax for a univariate integer polynomial from sparse terms. -/
private def sparseToUnivariateStx (overRat : Bool) (p : SparsePoly) : MetaM Lean.Term := do
  let mut acc : Option Lean.Term := none
  let X ← if overRat then `(term| (Polynomial.X : Polynomial ℚ))
           else `(term| (Polynomial.X : Polynomial ℤ))
  for t in p.terms do
    let c := t.coefficient
    let e := t.monomial.exponents.getD 0 0
    let cAbs := if c ≥ 0 then c.toNat else (-c).toNat
    let cPos ← if overRat then `(term| ($(quote cAbs) : ℚ))
               else `(term| ($(quote cAbs) : ℤ))
    let cPoly ←
      if c ≥ 0 then `(term| (Polynomial.C $cPos))
      else `(term| (-(Polynomial.C $cPos)))
    let mon ←
      if e = 0 then pure cPoly
      else if e = 1 then `(term| $cPoly * $X)
      else `(term| $cPoly * $X ^ $(quote e))
    acc ← match acc with
      | none => pure (some mon)
      | some a => `(term| $a + $mon)
  match acc with
  | some t => pure t
  | none =>
    if overRat then `(term| (0 : Polynomial ℚ))
    else `(term| (0 : Polynomial ℤ))

/-- Build `MvPolynomial.X (i : Fin n)` syntax. Prefer concrete `Fin 2` / `Fin 3` / `Fin 4`. -/
private def mvXStx (n : Nat) (overRat : Bool) (i : Nat) : MetaM Lean.Term := do
  if n == 2 then
    if overRat then
      `(term| (MvPolynomial.X ($(quote i) : Fin 2) : MvPolynomial (Fin 2) ℚ))
    else
      `(term| (MvPolynomial.X ($(quote i) : Fin 2) : MvPolynomial (Fin 2) ℤ))
  else if n == 3 then
    if overRat then
      `(term| (MvPolynomial.X ($(quote i) : Fin 3) : MvPolynomial (Fin 3) ℚ))
    else
      `(term| (MvPolynomial.X ($(quote i) : Fin 3) : MvPolynomial (Fin 3) ℤ))
  else if n == 4 then
    if overRat then
      `(term| (MvPolynomial.X ($(quote i) : Fin 4) : MvPolynomial (Fin 4) ℚ))
    else
      `(term| (MvPolynomial.X ($(quote i) : Fin 4) : MvPolynomial (Fin 4) ℤ))
  else if overRat then
    `(term| (MvPolynomial.X ($(quote i) : Fin $(quote n)) : MvPolynomial (Fin $(quote n)) ℚ))
  else
    `(term| (MvPolynomial.X ($(quote i) : Fin $(quote n)) : MvPolynomial (Fin $(quote n)) ℤ))

/-- Build syntax for a multivariate sparse polynomial over `Fin n`. -/
private def sparseToMvStx (n : Nat) (overRat : Bool) (p : SparsePoly) : MetaM Lean.Term := do
  let mut acc : Option Lean.Term := none
  for t in p.terms do
    let c := t.coefficient
    let exps := t.monomial.exponents
    let cAbs := if c ≥ 0 then c.toNat else (-c).toNat
    let cPos ← if overRat then `(term| ($(quote cAbs) : ℚ))
               else `(term| ($(quote cAbs) : ℤ))
    let cPoly ←
      if n == 2 then
        if overRat then
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 2) ℚ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 2) ℚ)))
        else
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 2) ℤ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 2) ℤ)))
      else if n == 3 then
        if overRat then
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 3) ℚ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 3) ℚ)))
        else
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 3) ℤ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 3) ℤ)))
      else if n == 4 then
        if overRat then
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 4) ℚ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 4) ℚ)))
        else
          if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin 4) ℤ))
          else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin 4) ℤ)))
      else if overRat then
        if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin $(quote n)) ℚ))
        else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin $(quote n)) ℚ)))
      else
        if c ≥ 0 then `(term| (MvPolynomial.C $cPos : MvPolynomial (Fin $(quote n)) ℤ))
        else `(term| (-(MvPolynomial.C $cPos : MvPolynomial (Fin $(quote n)) ℤ)))
    let mut mon : Lean.Term := cPoly
    for i in [:n] do
      let e := exps.getD i 0
      if e = 0 then continue
      let Xi ← mvXStx n overRat i
      let factor ←
        if e = 1 then pure Xi
        else `(term| $Xi ^ $(quote e))
      mon ← `(term| $mon * $factor)
    acc ← match acc with
      | none => pure (some mon)
      | some a => `(term| $a + $mon)
  match acc with
  | some t => pure t
  | none =>
    if n == 2 then
      if overRat then `(term| (0 : MvPolynomial (Fin 2) ℚ))
      else `(term| (0 : MvPolynomial (Fin 2) ℤ))
    else if n == 3 then
      if overRat then `(term| (0 : MvPolynomial (Fin 3) ℚ))
      else `(term| (0 : MvPolynomial (Fin 3) ℤ))
    else if n == 4 then
      if overRat then `(term| (0 : MvPolynomial (Fin 4) ℚ))
      else `(term| (0 : MvPolynomial (Fin 4) ℤ))
    else if overRat then `(term| (0 : MvPolynomial (Fin $(quote n)) ℚ))
    else `(term| (0 : MvPolynomial (Fin $(quote n)) ℤ))

private def sparseToStx (overRat : Bool) (p : SparsePoly) : MetaM Lean.Term :=
  if p.varCount ≤ 1 then sparseToUnivariateStx overRat p
  else sparseToMvStx p.varCount overRat p

private def reifyOne (e : Expr) : MetaM (Except Reject PolyResult) :=
  reifyLeanPoly e

/-- General CommRing singleton membership from a product witness (univariate or mv). -/
theorem membership_from_witness_any
    {R : Type*} [CommRing R] (f g q : R) (h : f = q * g) :
    f ∈ Ideal.span {g} := by
  rw [h]
  exact Ideal.mul_mem_left _ _ (Ideal.subset_span (Set.mem_singleton g))

/-- `mathevidence_ideal_membership` — Meta reify + IR gate + ring close. -/
elab "mathevidence_ideal_membership" : tactic => do
  let goal ← getMainGoal
  let goalType ← instantiateMVars (← goal.getType)
  match ← matchMemSpanGenerators goalType with
  | none =>
    throwError "{unsupportedMessage}\nreason: goal is not f ∈ Ideal.span \{…}"
  | some (fExpr, gens) =>
    let fExpr ← whnfR fExpr
    match gens.size with
    | 1 =>
      let gExpr ← whnfR gens[0]!
      match ← reifyOne fExpr, ← reifyOne gExpr with
      | .error err, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, .error err =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | .ok Rf, .ok Rg =>
        unless Rf.overRat == Rg.overRat do
          throwError "{unsupportedMessage}\nreason: ambient rings of f and g differ"
        unless Rf.poly.varCount == Rg.poly.varCount do
          throwError "{unsupportedMessage}\nreason: varCount mismatch"
        match proposeSingletonWitness? Rf.poly Rg.poly with
        | none =>
          throwError "mathevidence ideal membership: no singleton ZZ witness found"
        | some q =>
          unless checkMembership Rf.poly [Rg.poly] [q] do
            throwError "mathevidence ideal membership: checkMembership rejected singleton witness"
          let qStx ← sparseToStx Rf.overRat q
          let n := Rf.poly.varCount
          if n ≤ 1 then
            if Rf.overRat then
              evalTactic (← `(tactic|
                refine membership_from_witness_univariate (R := ℚ) _ _ $qStx (by
                  simp only [Polynomial.C_1, map_one, mul_one, one_mul, mul_neg, neg_mul,
                    sub_eq_add_neg]
                  ring)))
            else
              evalTactic (← `(tactic|
                refine membership_from_witness_univariate (R := ℤ) _ _ $qStx (by
                  simp only [Polynomial.C_1, map_one, mul_one, one_mul, mul_neg, neg_mul,
                    sub_eq_add_neg]
                  ring)))
          else if n == 2 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 2) ℚ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 2 then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 2) ℤ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 3 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 3) ℚ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 3 then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 3) ℤ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 4 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 4) ℚ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 4 then
            evalTactic (← `(tactic|
              refine membership_from_witness_any
                (R := MvPolynomial (Fin 4) ℤ) _ _ $qStx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else
            throwError "{unsupportedMessage}\nreason: MvPolynomial singleton Meta close supports Fin 2/3/4 (got Fin {n}; reify ≤4)"
    | 2 =>
      let g1Expr ← whnfR gens[0]!
      let g2Expr ← whnfR gens[1]!
      match ← reifyOne fExpr, ← reifyOne g1Expr, ← reifyOne g2Expr with
      | .error err, _, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, .error err, _ =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | _, _, .error err =>
        throwError "{unsupportedMessage}\nreason: {Reject.format err}"
      | .ok Rf, .ok Rg1, .ok Rg2 =>
        unless Rf.overRat == Rg1.overRat && Rf.overRat == Rg2.overRat do
          throwError "{unsupportedMessage}\nreason: ambient rings of f and generators differ"
        unless Rf.poly.varCount == Rg1.poly.varCount && Rf.poly.varCount == Rg2.poly.varCount do
          throwError "{unsupportedMessage}\nreason: varCount mismatch"
        match proposePairWitness? Rf.poly Rg1.poly Rg2.poly with
        | none =>
          throwError "mathevidence ideal membership: no two-generator ZZ witness found"
        | some (q1, q2) =>
          unless checkMembership Rf.poly [Rg1.poly, Rg2.poly] [q1, q2] do
            throwError "mathevidence ideal membership: checkMembership rejected pair witness"
          let q1Stx ← sparseToStx Rf.overRat q1
          let q2Stx ← sparseToStx Rf.overRat q2
          let n := Rf.poly.varCount
          if n ≤ 1 then
            if Rf.overRat then
              evalTactic (← `(tactic|
                refine membership_from_witness_pair (R := Polynomial ℚ) _ _ _ $q1Stx $q2Stx (by
                  simp only [Polynomial.C_1, map_one, mul_one, one_mul, mul_neg, neg_mul,
                    sub_eq_add_neg, mul_add, add_mul]
                  ring)))
            else
              evalTactic (← `(tactic|
                refine membership_from_witness_pair (R := Polynomial ℤ) _ _ _ $q1Stx $q2Stx (by
                  simp only [Polynomial.C_1, map_one, mul_one, one_mul, mul_neg, neg_mul,
                    sub_eq_add_neg, mul_add, add_mul]
                  ring)))
          else if n == 2 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 2) ℚ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 2 then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 2) ℤ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 3 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 3) ℚ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 3 then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 3) ℤ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 4 && Rf.overRat then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 4) ℚ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else if n == 4 then
            evalTactic (← `(tactic|
              refine membership_from_witness_pair
                (R := MvPolynomial (Fin 4) ℤ) _ _ _ $q1Stx $q2Stx (by
                simp only [map_zero, map_one, mul_zero, zero_mul, add_zero, zero_add,
                  mul_one, one_mul, mul_comm, mul_left_comm, mul_assoc, mul_add, add_mul,
                  sub_eq_add_neg, mul_neg, neg_mul]
                try ring)))
          else
            throwError "{unsupportedMessage}\nreason: MvPolynomial pair Meta close supports Fin 2/3/4 (got Fin {n}; reify ≤4)"
    | _ =>
      throwError "{unsupportedMessage}\nreason: only singleton or two-generator spans are supported (got {gens.size})"

end MathEvidence.Tactic.IdealMembership
