/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.AnalyticExpr.Syntax
import Mathlib.Data.Real.Basic
import Mathlib.Data.Set.Basic

/-!
# Domain obligations for analytic expressions (ME-RV-050)

Certificates may *list* obligations. Callers supply proofs that the obligations
hold at the evaluation point. The checker never accepts caller-trusted Booleans
as evidence that a domain condition is true.
-/

namespace MathEvidence.IR.AnalyticExpr

/-- Explicit domain for membership obligations (initially `Set ℝ`). -/
abbrev Domain := Set ℝ

/-- Inductive domain obligation attached to a derivation / ODE certificate. -/
inductive DomainObligation where
  | nonzero (expr : Expr)
  | positive (expr : Expr)
  | member (domain : Domain) (expr : Expr)
  deriving Inhabited

/-- Structural obligations implied by expression constructors (for reports).

These are *hints* for adapters; acceptance still requires certificate-listed
obligations plus caller proofs of `SatisfiesObligations`.
-/
def Expr.structuralObligations : Expr → List DomainObligation
  | .variable _ | .const _ => []
  | .add a b | .sub a b | .mul a b =>
      a.structuralObligations ++ b.structuralObligations
  | .div n d =>
      n.structuralObligations ++ d.structuralObligations ++ [.nonzero d]
  | .inv a =>
      a.structuralObligations ++ [.nonzero a]
  | .neg a | .sin a | .cos a | .exp a | .pow a _ =>
      a.structuralObligations
  | .log a =>
      a.structuralObligations ++ [.positive a]

end MathEvidence.IR.AnalyticExpr
