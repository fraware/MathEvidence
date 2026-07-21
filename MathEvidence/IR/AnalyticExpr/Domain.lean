/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.AnalyticExpr.Syntax
import Mathlib.Data.Real.Basic
import Mathlib.Data.Set.Basic

/-!
# Domain conditions for analytic expressions

The analytic vertical records domain obligations as typed propositions at the
Mathlib boundary. String labels may describe obligations for reports, but they
are not evidence by themselves.
-/

namespace MathEvidence.IR.AnalyticExpr.Domain

/-- Human-readable label paired with a typed Mathlib-side proposition. -/
structure Condition where
  description : String
  statement : Prop := True

instance : Inhabited Condition where
  default := { description := "true", statement := True }

/-- Point membership condition used by derivative-within-domain certificates. -/
def pointInDomain (s : Set ℝ) (x : ℝ) : Condition where
  description := "point_in_domain"
  statement := x ∈ s

/-- Denominator nonzero condition used before quotient / inverse rules. -/
def denominatorNonzero (g : ℝ → ℝ) (x : ℝ) : Condition where
  description := "denominator_nonzero"
  statement := g x ≠ 0

/-- Logarithm argument positivity. -/
def logArgumentPositive (g : ℝ → ℝ) (x : ℝ) : Condition where
  description := "log_argument_positive"
  statement := 0 < g x

/-- No accepted analytic certificate may claim solution-family completeness. -/
def noCompletenessClaim : Condition where
  description := "no_completeness_claim"
  statement := True

/-- Structural domain obligations collected from expression constructors. -/
def domainConditions : MathEvidence.IR.AnalyticExpr.Expr → List Condition
  | .variable _ | .const _ => []
  | .add a b | .sub a b | .mul a b => domainConditions a ++ domainConditions b
  | .div n d =>
      domainConditions n ++ domainConditions d ++
        [{ description := "denominator_nonzero_structural", statement := True }]
  | .neg a | .sin a | .exp a | .pow a _ => domainConditions a
  | .log a =>
      domainConditions a ++
        [{ description := "log_argument_positive_structural", statement := True }]

end MathEvidence.IR.AnalyticExpr.Domain
