/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Syntax

/-!
# Sparse polynomial *computation* (no Mathlib)

Used by `checkBool` and `mathevidence-replay` so the Lake exe does not link
Mathlib. Homomorphism / evaluation lemmas live in `Poly.lean`.
-/

namespace MathEvidence.IR.RationalExpr

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

end MathEvidence.IR.RationalExpr
