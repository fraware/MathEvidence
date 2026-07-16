/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Hypothesis.CounterexampleBridge
import MathEvidence.Hypothesis.Deletion
import MathEvidence.Hypothesis.Lattice
import MathEvidence.Hypothesis.Sufficiency

namespace MathEvidence.Hypothesis

open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.RationalEquality

/-!
# Build condition lattice

Orchestrates propose → prove_sufficient → delete_hypothesis over a bounded
policy. Never asserts minimality without necessity proofs.
-/

/-- Pair an id with an expression for lattice construction. -/
structure NamedCondition where
  id : String
  expr : Expr
  source : ConditionSource := .backendProposed
  deriving DecidableEq, Repr, Inhabited

/-- Bounded deletion policy: try deleting each member of a sufficient set once. -/
structure BuildPolicy where
  /-- Maximum number of single-deletion attempts. -/
  maxDeletions : Nat := 16
  deriving Repr, Inhabited

/-- Convert named conditions to lattice nodes. -/
def toNodes (xs : List NamedCondition) : List ConditionNode :=
  xs.map fun n =>
    { id := n.id
      expr := n.expr
      source := n.source
      status := .proposed }

/-- Recursive single-pass deletion search under a budget. -/
def deletionPass
    (req : Request)
    (L : ConditionLattice)
    (candidates : List NamedCondition)
    (remainingIds : List String)
    (remainingExprs : List Expr)
    (budget : Nat) :
    ConditionLattice × List String × List Expr :=
  match budget, candidates with
  | 0, _ => (L, remainingIds, remainingExprs)
  | _, [] => (L, remainingIds, remainingExprs)
  | Nat.succ b, nc :: rest =>
    match deleteHypothesis req remainingExprs nc.expr with
    | .redundant rem =>
      let L' := L.recordRedundant nc.id
      deletionPass req L' rest
        (remainingIds.filter (· ≠ nc.id)) rem b
    | .notRedundant _ =>
      let L' := L.recordUnresolvedNecessity nc.id
      deletionPass req L' rest remainingIds remainingExprs b
    | .missing =>
      deletionPass req L rest remainingIds remainingExprs b

/-- Build a lattice from original + proposed conditions under a rational claim. -/
def buildConditionLattice
    (artifactId : String)
    (req : Request)
    (original : List NamedCondition)
    (proposed : List NamedCondition)
    (policy : BuildPolicy := {}) :
    ConditionLattice :=
  let all := original ++ proposed
  let L0 : ConditionLattice :=
    { ConditionLattice.empty artifactId with
      originalAssumptions := toNodes original
      proposed := toNodes proposed }
  let allIds := all.map (·.id)
  let allExprs := all.map (·.expr)
  let suf := isSufficient req allExprs
  let L1 := L0.recordSufficient allIds suf
  if !suf then
    { L1 with
      unresolvedNecessity := proposed.map (·.id)
      recommendedInterface := []
      claimsMinimal := false
      ranking := some {
        criteria :=
          ["logical generality",
           "assumption count",
           "library conventions",
           "human readability"]
        recommendedInterfaceId := "none"
        notes := "No sufficient set proved; human review required." } }
  else
    let (L2, remIds, _) :=
      deletionPass req L1 all allIds allExprs policy.maxDeletions
    { L2 with
      recommendedInterface := remIds
      claimsMinimal := false
      ranking := some {
        criteria :=
          ["logical generality",
           "assumption count",
           "library conventions",
           "human readability"]
        recommendedInterfaceId := "recommended_v0"
        notes :=
          "Minimality is not claimed. Expert review required before upstreaming." } }

end MathEvidence.Hypothesis
