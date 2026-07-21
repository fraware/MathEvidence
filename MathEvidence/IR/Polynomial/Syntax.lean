/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.IR.Polynomial

/-!
# Sparse Polynomial Syntax

Minimal, sorry-free syntax for RFC 0002 ideal-membership federation scaffolding.

This module intentionally provides structural data only. It does not implement
normalization, Gröbner bases, ideal membership checking, or semantic evaluation.
-/

/-- A monomial is represented by one exponent per variable. -/
structure Monomial where
  exponents : List Nat
  deriving DecidableEq, Repr, Inhabited

/-- A sparse term `coefficient * x_0^e_0 * ... * x_n^e_n`. -/
structure Term where
  coefficient : Int
  monomial : Monomial
  deriving DecidableEq, Repr, Inhabited

/-- Sparse polynomial syntax over integer coefficients. -/
structure SparsePoly where
  varCount : Nat
  terms : List Term
  deriving DecidableEq, Repr, Inhabited

/-- Terms must mention exactly the variables declared by the polynomial. -/
def Term.wellFormed (varCount : Nat) (term : Term) : Bool :=
  decide (term.monomial.exponents.length = varCount)

/-- Structural well-formedness for the sparse representation. -/
def SparsePoly.wellFormed (poly : SparsePoly) : Bool :=
  poly.terms.all (Term.wellFormed poly.varCount)

/-- Certificate side of `f = sum_i q_i * g_i`: one multiplier for each generator. -/
structure IdealMembershipCertificate where
  multipliers : List SparsePoly
  deriving DecidableEq, Repr, Inhabited

/-- Zero polynomial with a fixed variable count. -/
def SparsePoly.zero (varCount : Nat := 0) : SparsePoly :=
  { varCount := varCount, terms := [] }

/-- Concatenate terms (no like-term collection; structural only). -/
def SparsePoly.add (a b : SparsePoly) : SparsePoly :=
  if a.varCount != b.varCount then a
  else { varCount := a.varCount, terms := a.terms ++ b.terms }

/-- Multiply two sparse polynomials (cartesian product of terms). -/
def SparsePoly.mul (a b : SparsePoly) : SparsePoly :=
  if a.varCount != b.varCount then SparsePoly.zero a.varCount
  else
    let terms :=
      a.terms.flatMap fun ta =>
        b.terms.map fun tb =>
          ({
            coefficient := ta.coefficient * tb.coefficient
            monomial := {
              exponents :=
                List.zip ta.monomial.exponents tb.monomial.exponents |>.map fun (x, y) =>
                  x + y
            }
          } : Term)
    { varCount := a.varCount, terms := terms }

end MathEvidence.IR.Polynomial
