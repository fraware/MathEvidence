/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.MvPolynomial.Basic
import Mathlib.Data.Finsupp.Defs
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.IR.Polynomial.Normalize

/-!
# Sparse polynomial interpretation into MvPolynomial (Fin m) over Int

ME-RV-031: semantic evaluation of fixed-arity IR.
-/

namespace MathEvidence.IR.Polynomial

open MvPolynomial

/-- Convert a fixed-arity monomial to a finitely supported exponent function. -/
noncomputable def Monomial.toFinsupp {m : Nat} (mon : Monomial m) : Fin m →₀ Nat :=
  Finsupp.equivFunOnFinite.symm fun i => mon.exponents.get i

/-- Monomial as an MvPolynomial monomial (coefficient 1). -/
noncomputable def Monomial.toMv {m : Nat} (mon : Monomial m) : MvPolynomial (Fin m) ℤ :=
  monomial mon.toFinsupp (1 : ℤ)

/-- Evaluate a single term. -/
noncomputable def Term.eval {m : Nat} (t : Term m) : MvPolynomial (Fin m) ℤ :=
  C t.coefficient * t.monomial.toMv

/-- List-sum evaluation (definitional form used in proofs). -/
noncomputable def evalTerms {m : Nat} (terms : List (Term m)) : MvPolynomial (Fin m) ℤ :=
  (terms.map Term.eval).sum

/-- Interpret a raw sparse polynomial. -/
noncomputable def RawSparsePoly.eval {m : Nat} (p : RawSparsePoly m) : MvPolynomial (Fin m) ℤ :=
  evalTerms p.terms

/-- Interpret a (canonical) sparse polynomial. -/
noncomputable def SparsePoly.eval {m : Nat} (p : SparsePoly m) : MvPolynomial (Fin m) ℤ :=
  evalTerms p.terms

end MathEvidence.IR.Polynomial
