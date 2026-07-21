/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.FinitePredicate.Eval
import MathEvidence.IR.FinitePredicate.Serialize
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.Core
open MathEvidence.IR.FinitePredicate

/-- Claim: a finite predicate to be refuted by a typed witness.

The established theorem is only that the predicate is **false at the witness**.
Exhaustive absence of counterexamples is outside this capability. -/
structure Claim where
  varNames : List String
  domains : List Domain
  pred : Pred
  claimClass : ClaimClass := .refutation
  deriving DecidableEq, Repr, Inhabited

structure Request where
  capability : CapabilityRef := .finiteCounterexample
  claim : Claim
  requestDigest : RequestDigest
  deriving DecidableEq, Repr, Inhabited

def Request.ofClaim (c : Claim) : Request :=
  let payload : RequestPayload := {
    varNames := c.varNames
    domains := c.domains
    pred := c.pred
    claim := c.claimClass.toWire
  }
  { claim := c, requestDigest := payload.digest }

/-- Proposition: the predicate evaluates to `false` at the witness assignment. -/
def Claim.proposition (c : Claim) (σ : Assignment) : Prop :=
  isCounterexample σ c.pred = true

end MathEvidence.Checkers.Counterexample
