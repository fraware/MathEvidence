/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.CalculusExpr.Serialize
import MathEvidence.IR.CalculusExpr.Syntax
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.Calculus

open MathEvidence.Core
open MathEvidence.IR.CalculusExpr
open MathEvidence.IR.RationalExpr (Expr)

/-- Symbolic calculus claim (Milestone 5).

Candidate validity is always separate from completeness: acceptance never asserts
that antiderivatives / ODE solutions / recurrence closed forms are unique or
exhaustive. Branch and singularity conditions are the explicit `domainConditions`.
-/
structure Claim where
  operation : Operation
  varNames : List String
  /-- Index of the independent variable (`x` or `n`). -/
  independentVar : Nat := 0
  /-- Placeholder index for dependent / previous-term variable (`y` or `u`). -/
  dependentVar : Nat := 1
  /-- Primary expression: `f`, closed form `u(n)`, or ODE solution `y(x)`. -/
  expr : Expr
  /-- Candidate: derivative `g`, antiderivative `F`, or unused for recurrence/ODE. -/
  candidate : Expr := .int 0
  /-- Explicit domain / singularity / branch nonzero obligations. -/
  domainConditions : List Expr := []
  initialConditions : List InitialCondition := []
  /-- First-order ODE right-hand side `f(x, y)`. -/
  odeRhs : Option Expr := none
  /-- Recurrence right-hand side for `u(n+1)` in terms of `n` and `u`. -/
  recurrenceRhs : Option Expr := none
  claimClass : ClaimClass := .candidate
  deriving DecidableEq, Repr, Inhabited

structure Request where
  capability : CapabilityRef := .symbolicCalculus
  claim : Claim
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

def Request.ofClaim (c : Claim) : Request :=
  let payload : RequestPayload := {
    operation := c.operation
    varNames := c.varNames
    independentVar := c.independentVar
    dependentVar := c.dependentVar
    expr := c.expr
    candidate := c.candidate
    domainConditions := c.domainConditions
    initialConditions := c.initialConditions
    odeRhs := c.odeRhs
    recurrenceRhs := c.recurrenceRhs
    claim := c.claimClass.toWire
  }
  { claim := c, requestDigest := payload.digest }

/-- Executable formal-identity obligation (mirrors checker `opOk`).

Completeness / uniqueness are intentionally absent. -/
def Claim.opHolds (c : Claim) : Bool :=
  let x := c.independentVar
  let y := c.dependentVar
  match c.operation with
  | .derivativeCandidate =>
      derivativeOk x c.expr c.candidate
  | .antiderivativeCandidate =>
      antiderivativeOk x c.expr c.candidate
  | .recurrenceIdentity =>
      match c.recurrenceRhs with
      | some rhs =>
          decide (y < c.varNames.length) && recurrenceOk x y c.expr rhs
      | none => false
  | .odeCandidate =>
      match c.odeRhs with
      | some rhs =>
          decide (y < c.varNames.length) &&
            odeResidualOk x y c.expr rhs &&
            icsOk x c.expr c.initialConditions
      | none => false

/-- Proposition established on acceptance: formal candidate identity holds.

Does **not** assert completeness, uniqueness, or identity at poles. -/
def Claim.proposition (c : Claim) : Prop :=
  c.opHolds = true

end MathEvidence.Checkers.Calculus
