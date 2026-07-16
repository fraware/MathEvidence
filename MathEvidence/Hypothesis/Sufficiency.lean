/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Hypothesis.Lattice

namespace MathEvidence.Hypothesis

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality

/-!
# Sufficiency proof loop

Proposed condition sets become proof obligations under the existing
`RationalEquality` checker. Sufficiency is exactly checker acceptance
(`checkBool`), which yields `Claim.proposition` via soundness.
-/

/-- Build an untrusted certificate binding `conditions` as denominator factors. -/
def certificateOf (req : Request) (conditions : List Expr) : Certificate where
  requestDigest := req.requestDigest
  denomFactors := conditions

/-- Executable sufficiency predicate: poly identity + denom coverage. -/
def isSufficient (req : Request) (conditions : List Expr) : Bool :=
  checkBool req (certificateOf req conditions)

/-- Structured result of a sufficiency attempt. -/
inductive SufficiencyResult where
  | proved
  | rejected (detail : String)
  deriving DecidableEq, Repr, Inhabited

def proveSufficient (req : Request) (conditions : List Expr) : SufficiencyResult :=
  if isSufficient req conditions then
    .proved
  else
    .rejected "rational equality checker rejected condition set"

/-- Soundness bridge: checker acceptance ⇒ claim proposition under `conditions`. -/
theorem sufficient_implies_proposition (req : Request) (conditions : List Expr)
    (h : isSufficient req conditions = true) :
    Claim.proposition req.claim conditions :=
  checkBool_sound req (certificateOf req conditions) h

/-- Record a proved sufficient set onto a lattice (by condition ids). -/
def ConditionLattice.recordSufficient
    (L : ConditionLattice) (ids : List String) (proved : Bool) : ConditionLattice :=
  if proved then
    { L with
      sufficientSets := L.sufficientSets ++ [ids]
      proposed := L.proposed.map fun n =>
        if ids.contains n.id then
          { n with status := .sufficientMember }
        else n }
  else L

end MathEvidence.Hypothesis
