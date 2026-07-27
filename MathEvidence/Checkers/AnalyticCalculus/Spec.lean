/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Analysis.Calculus.Deriv.Basic
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.IR.AnalyticExpr.Domain
import MathEvidence.IR.AnalyticExpr.Interpret

/-!
# Analytic calculus specification (ME-RV-050..053)

Claim shapes for derivative, antiderivative, and first-order ODE candidates.
Acceptance never asserts completeness, uniqueness, or maximal intervals.
-/

namespace MathEvidence.Checkers.AnalyticCalculus

open MathEvidence.Core
open MathEvidence.IR.AnalyticExpr

/-- Top-level analytic claim kind. -/
inductive ClaimKind where
  | derivative
  | antiderivative
  | odeCandidate
  deriving DecidableEq, Repr, Inhabited

/-- Initial-condition pair as IR expressions (constants in the public fragment). -/
structure InitialCondition where
  point : Expr
  value : Expr
  deriving DecidableEq, Repr, Inhabited

/-- Analytic claim payload bound into a request. -/
structure Claim where
  kind : ClaimKind
  /-- Source `f`, antiderivative `F`, or ODE solution `y`. -/
  source : Expr
  /-- Claimed derivative `f'`, integrand `f`, or ODE RHS `f(x)`. -/
  target : Expr
  initialConditions : Array InitialCondition := #[]
  claimClass : ClaimClass := .candidate
  deriving DecidableEq, Repr, Inhabited

structure Request where
  capability : CapabilityRef := .analyticCalculus
  claim : Claim
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

/-- Candidate solution satisfies `y' = rhs` on `domain` with listed ICs.

Includes residual satisfaction and initial conditions only. Existence,
uniqueness, maximal interval, and solution-family completeness are out of
scope.
-/
noncomputable def CandidateSolvesFirstOrderODE
    (solution rhs : ℝ → ℝ) (domain : Set ℝ)
    (ics : List (ℝ × ℝ)) : Prop :=
  (∀ x ∈ domain, HasDerivAt solution (rhs x) x) ∧
    (∀ p ∈ ics, solution p.1 = p.2)

/-- Evaluate an IC pair under interpretation (constants ignore the dummy argument). -/
noncomputable def InitialCondition.asPair (ic : InitialCondition) : ℝ × ℝ :=
  (ic.point.interpret 0, ic.value.interpret 0)

end MathEvidence.Checkers.AnalyticCalculus
