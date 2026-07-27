/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.Polynomial.Syntax

/-!
# Sparse polynomial normalization

Functional like-term collection + sort. Semantics are proved in `Soundness.lean`.
-/

namespace MathEvidence.IR.Polynomial

/-- Insert/merge one term into an accumulator that has unique monomials. -/
def mergeTerm {m : Nat} (acc : List (Term m)) (t : Term m) : List (Term m) :=
  if t.coefficient == 0 then acc
  else
    match acc with
    | [] => [t]
    | u :: us =>
      if u.monomial == t.monomial then
        let c := u.coefficient + t.coefficient
        if c == 0 then us else { u with coefficient := c } :: us
      else
        u :: mergeTerm us t

/-- Fold `mergeTerm` over all raw terms (unique monomials; not yet sorted). -/
def collectTerms {m : Nat} (terms : List (Term m)) : List (Term m) :=
  terms.foldl mergeTerm []

/-- Insertion into a list sorted by monomial exponents. -/
def insertSorted {m : Nat} (t : Term m) : List (Term m) → List (Term m)
  | [] => [t]
  | u :: us =>
    if Monomial.le t.monomial u.monomial then t :: u :: us
    else u :: insertSorted t us

/-- Insertion-sort by monomial exponent vector. -/
def sortTerms {m : Nat} (terms : List (Term m)) : List (Term m) :=
  terms.foldl (fun acc t => insertSorted t acc) []

/-- Combine like terms, drop zeros, sort by exponents. -/
def RawSparsePoly.normalize {m : Nat} (p : RawSparsePoly m) : SparsePoly m :=
  ⟨sortTerms (collectTerms p.terms)⟩

def SparsePoly.normalize {m : Nat} (p : SparsePoly m) : SparsePoly m :=
  p.toRaw.normalize

def SparsePoly.add {m : Nat} (a b : SparsePoly m) : SparsePoly m :=
  (a.addRaw b).normalize

def SparsePoly.neg {m : Nat} (a : SparsePoly m) : SparsePoly m :=
  a.toRaw.neg.normalize

def SparsePoly.sub {m : Nat} (a b : SparsePoly m) : SparsePoly m :=
  (a.toRaw.sub b.toRaw).normalize

def SparsePoly.mul {m : Nat} (a b : SparsePoly m) : SparsePoly m :=
  (a.mulRaw b).normalize

/-- Linear combination `∑ qᵢ · gᵢ` as a list fold (equal-length gens/mults). -/
def linearCombinationList {m : Nat}
    (gens mults : List (SparsePoly m)) : SparsePoly m :=
  ((List.zip gens mults).foldl
    (fun (acc : RawSparsePoly m) pair =>
      acc.add (pair.2.mulRaw pair.1))
    (RawSparsePoly.zero m)).normalize

/-- Array form: requires equal sizes for a complete combination. -/
def linearCombination {m : Nat}
    (gens : Array (SparsePoly m)) (mults : Array (SparsePoly m)) : SparsePoly m :=
  linearCombinationList gens.toList mults.toList

/-- Constant polynomial `c` in `m` variables. -/
def SparsePoly.C (m : Nat) (c : Int) : SparsePoly m :=
  if c == 0 then .zero m
  else ⟨[{ coefficient := c, monomial := Monomial.one m }]⟩

/-- Indeterminate `X_i` in `m` variables. -/
def SparsePoly.X (m i : Nat) (hi : i < m := by omega) : SparsePoly m :=
  ⟨[{ coefficient := 1, monomial := Monomial.single m i 1 hi }]⟩

/-- Univariate power `c · X^e` (`m = 1`). -/
def SparsePoly.monomialUnivariate (c : Int) (e : Nat) : SparsePoly 1 :=
  if c == 0 then .zero 1
  else ⟨[{ coefficient := c, monomial := ⟨⟨[e], rfl⟩⟩ }]⟩

/-- Multivariate monomial `c · X_i^e`. -/
def SparsePoly.monomialMv (m i e : Nat) (c : Int) (hi : i < m := by omega) :
    SparsePoly m :=
  if c == 0 then .zero m
  else ⟨[{ coefficient := c, monomial := Monomial.single m i e hi }]⟩

/-- Natural-number power via repeated multiplication (reifier / Meta path). -/
def SparsePoly.npow {m : Nat} (p : SparsePoly m) : Nat → SparsePoly m
  | 0 => SparsePoly.C m 1
  | n + 1 => (SparsePoly.npow p n).mul p

end MathEvidence.IR.Polynomial
