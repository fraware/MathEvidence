/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Vector.Defs

/-!
# Sparse Polynomial Syntax (fixed-arity)

ME-RV-030: monomials are parameterized by variable count `m`. Exponent vectors
are Mathlib `Vector Nat m` (list subtype of length `m`); length truncation is
impossible by construction. Canonical sparse polynomials are produced by
`Normalize`.
-/

namespace MathEvidence.IR.Polynomial

open Mathlib

/-- A monomial in exactly `m` variables. -/
structure Monomial (m : Nat) where
  exponents : Vector Nat m
  deriving DecidableEq

instance {α : Type*} {n : Nat} [Repr α] : Repr (Vector α n) where
  reprPrec v _ := repr v.toList

instance {m : Nat} : Repr (Monomial m) where
  reprPrec mon _ :=
    Std.Format.text "Monomial.mk " ++ repr mon.exponents

instance {m : Nat} : Inhabited (Monomial m) where
  default := ⟨Vector.replicate m 0⟩

/-- A sparse term `coefficient * x_0^e_0 * ... * x_{m-1}^e_{m-1}`. -/
structure Term (m : Nat) where
  coefficient : Int
  monomial : Monomial m
  deriving DecidableEq, Repr

instance {m : Nat} : Inhabited (Term m) where
  default := ⟨0, default⟩

/-- Raw (possibly unnormalized) sparse polynomial over `ℤ` in `m` variables. -/
structure RawSparsePoly (m : Nat) where
  terms : List (Term m)
  deriving DecidableEq, Repr, Inhabited

/-- Canonical sparse polynomial: like terms combined, zeros dropped, sorted. -/
structure SparsePoly (m : Nat) where
  terms : List (Term m)
  deriving DecidableEq, Repr, Inhabited

/-- Forget canonicality (still fixed-arity). -/
def SparsePoly.toRaw {m : Nat} (p : SparsePoly m) : RawSparsePoly m :=
  ⟨p.terms⟩

/-- Zero polynomial in `m` variables. -/
def SparsePoly.zero (m : Nat) : SparsePoly m :=
  ⟨[]⟩

def RawSparsePoly.zero (m : Nat) : RawSparsePoly m :=
  ⟨[]⟩

/-- Build a monomial from a length-`m` list; `none` when length differs. -/
def Monomial.ofList? (m : Nat) (xs : List Nat) : Option (Monomial m) :=
  if h : xs.length = m then
    some ⟨⟨xs, h⟩⟩
  else
    none

/-- Unsafe constructor for literals that are definitionally length-`m`. -/
def Monomial.ofList! (m : Nat) (xs : List Nat) (h : xs.length = m := by decide) :
    Monomial m :=
  ⟨⟨xs, h⟩⟩

/-- Single-variable power `X_i^e` in `m` variables. -/
def Monomial.single (m i e : Nat) (_hi : i < m := by omega) : Monomial m :=
  ⟨Vector.ofFn fun j => if j.val = i then e else 0⟩

/-- Constant term monomial (all exponents zero). -/
def Monomial.one (m : Nat) : Monomial m :=
  ⟨Vector.replicate m 0⟩

/-- Componentwise exponent addition (same arity by type). -/
def Monomial.mul {m : Nat} (a b : Monomial m) : Monomial m :=
  ⟨Vector.map₂ (· + ·) a.exponents b.exponents⟩

/-- Lexicographic order on exponent vectors (for stable sorting). -/
def Monomial.le {m : Nat} (a b : Monomial m) : Bool :=
  decide (a.exponents.toList ≤ b.exponents.toList)

/-- Total degree. -/
def Monomial.totalDegree {m : Nat} (a : Monomial m) : Nat :=
  a.exponents.toList.foldl (· + ·) 0

/-- Erased wire form: runtime `varCount` with arity-checked terms. -/
structure SparsePolyᵤ where
  varCount : Nat
  terms : List (Int × List Nat)
  deriving DecidableEq, Repr, Inhabited

/-- Every term's exponent list length equals `varCount`. -/
def SparsePolyᵤ.wellFormed (p : SparsePolyᵤ) : Bool :=
  p.terms.all fun t => decide (t.2.length = p.varCount)

/-- Decode erased poly into fixed-arity IR; rejects length ≠ `varCount`. -/
def SparsePolyᵤ.toTyped? (p : SparsePolyᵤ) : Option (Σ m, SparsePoly m) :=
  if !p.wellFormed then none
  else
    let m := p.varCount
    let terms : List (Term m) :=
      p.terms.filterMap fun (c, exps) =>
        match Monomial.ofList? m exps with
        | some mon => some ⟨c, mon⟩
        | none => none
    if terms.length != p.terms.length then none
    else some ⟨m, ⟨terms⟩⟩

/-- Encode typed poly to erased wire form. -/
def SparsePoly.toErased {m : Nat} (p : SparsePoly m) : SparsePolyᵤ :=
  { varCount := m
    terms := p.terms.map fun t => (t.coefficient, t.monomial.exponents.toList) }

/-- Build erased poly from coefficient/exponent pairs; rejects bad arity. -/
def SparsePolyᵤ.ofTerms? (m : Nat) (terms : List (Int × List Nat)) : Option SparsePolyᵤ :=
  let p : SparsePolyᵤ := { varCount := m, terms := terms }
  if p.wellFormed then some p else none

/-- Typed decode when `varCount = m`. -/
def SparsePolyᵤ.toSparse? (m : Nat) (p : SparsePolyᵤ) : Option (SparsePoly m) :=
  if p.varCount != m || !p.wellFormed then none
  else
    let terms : List (Term m) :=
      p.terms.filterMap fun (c, exps) =>
        (Monomial.ofList? m exps).map fun mon => ⟨c, mon⟩
    if terms.length != p.terms.length then none else some ⟨terms⟩

/-- Concatenate raw terms (no like-term collection). -/
def RawSparsePoly.add {m : Nat} (a b : RawSparsePoly m) : RawSparsePoly m :=
  ⟨a.terms ++ b.terms⟩

/-- Negate all coefficients. -/
def RawSparsePoly.neg {m : Nat} (a : RawSparsePoly m) : RawSparsePoly m :=
  ⟨a.terms.map fun t => { t with coefficient := -t.coefficient }⟩

/-- Subtract via negation. -/
def RawSparsePoly.sub {m : Nat} (a b : RawSparsePoly m) : RawSparsePoly m :=
  a.add b.neg

/-- Multiply two raw sparse polynomials (cartesian product; fixed arity). -/
def RawSparsePoly.mul {m : Nat} (a b : RawSparsePoly m) : RawSparsePoly m :=
  ⟨a.terms.flatMap fun ta =>
    b.terms.map fun tb =>
      ({
        coefficient := ta.coefficient * tb.coefficient
        monomial := Monomial.mul ta.monomial tb.monomial
      } : Term m)⟩

/-- Lift typed polys to raw then add. -/
def SparsePoly.addRaw {m : Nat} (a b : SparsePoly m) : RawSparsePoly m :=
  a.toRaw.add b.toRaw

def SparsePoly.mulRaw {m : Nat} (a b : SparsePoly m) : RawSparsePoly m :=
  a.toRaw.mul b.toRaw

/-- Certificate side of `f = ∑ qᵢ · gᵢ`: one multiplier per generator. -/
structure IdealMembershipCertificate (m : Nat) where
  multipliers : Array (SparsePoly m)
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.IR.Polynomial
