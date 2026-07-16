/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.RationalExpr.Eval
import MathEvidence.IR.RationalExpr.Serialize
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core
open MathEvidence.IR.RationalExpr

/-- Mathematical claim: equality of two rational expressions under explicit
nonzero conditions on a listed set of denominator factors (RFC 0001).

The claim is *not* identity of totalized field expressions at poles. -/
structure Claim where
  /-- Canonical variable names (index order). -/
  varNames : List String
  lhs : Expr
  rhs : Expr
  /-- Assumptions already available in the local context (nonzero obligations). -/
  knownAssumptions : List Expr := []
  /-- Requested claim strength (Milestone 1: `soundResult`). -/
  claimClass : ClaimClass := .soundResult
  deriving DecidableEq, Repr, Inhabited

/-- Versioned request binding digest + claim. -/
structure Request where
  capability : CapabilityRef := .rationalEquality
  claim : Claim
  /-- Precomputed or recomputed request digest. -/
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

/-- Build a request payload and its digest from a claim. -/
def Request.ofClaim (c : Claim) : Request :=
  let payload : RequestPayload := {
    varNames := c.varNames
    lhs := c.lhs
    rhs := c.rhs
    knownAssumptions := c.knownAssumptions
    claim := c.claimClass.toWire
  }
  { claim := c, requestDigest := payload.digest }

/-- Proposition established on success: for every environment where all required
conditions are defined and nonzero, `eval lhs = eval rhs`. -/
def Claim.proposition (c : Claim) (conditions : List Expr) : Prop :=
  ∀ env : Env ℚ,
    (∀ e ∈ conditions ++ c.knownAssumptions, Defined env e ∧
      ∃ v, eval env e = some v ∧ v ≠ 0) →
    Defined env c.lhs → Defined env c.rhs →
    eval env c.lhs = eval env c.rhs

end MathEvidence.Checkers.RationalEquality
