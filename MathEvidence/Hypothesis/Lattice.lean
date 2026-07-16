/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Hypothesis

open MathEvidence.IR.RationalExpr

/-!
# Condition lattice artifact (Product 03)

The primary Hypothesis Synthesis output is a **lattice**, not one opaque repaired
statement. Nodes record provenance and justification status. Minimality is never
asserted by construction — only via an explicit `NecessityProof` when present.
-/

/-- Provenance of a condition candidate. -/
inductive ConditionSource where
  | originalAssumption
  | backendProposed
  | libraryHeuristic
  | human
  deriving DecidableEq, Repr, Inhabited

/-- Status of one condition relative to a candidate theorem interface. -/
inductive ConditionStatus where
  /-- Proposed but not yet proved sufficient as part of a set. -/
  | proposed
  /-- Appears in a Lean-proved sufficient set. -/
  | sufficientMember
  /-- Proved removable while preserving sufficiency. -/
  | redundant
  /-- Necessity not established (default; absence of CEX is not necessity). -/
  | necessityOpen
  /-- A weaker variant without this condition has a certified counterexample. -/
  | weakerFalsified
  deriving DecidableEq, Repr, Inhabited

/-- One lattice node: a side condition with status and optional notes. -/
structure ConditionNode where
  id : String
  expr : Expr
  source : ConditionSource := .backendProposed
  status : ConditionStatus := .proposed
  /-- Human-readable notes; never a soundness claim. -/
  notes : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Justification kinds attached to lattice edges / deletions. -/
inductive JustificationKind where
  | sufficiencyProof
  | redundancyProof
  | certifiedCounterexample
  | unresolved
  deriving DecidableEq, Repr, Inhabited

/-- Explicit necessity marker — only when a proof or complete CEX argument exists. -/
structure NecessityProof where
  conditionId : String
  kind : JustificationKind
  detail : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Ranking criteria explanation (never a model-only score for correctness). -/
structure RankingExplanation where
  criteria : List String
  recommendedInterfaceId : String
  notes : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Condition lattice artifact — Product 03 primary output. -/
structure ConditionLattice where
  /-- Stable artifact id (for Foundry episode linkage). -/
  artifactId : String
  /-- Original assumptions from the candidate Lean proposition. -/
  originalAssumptions : List ConditionNode
  /-- Backend-proposed conditions (untrusted until sufficiency). -/
  proposed : List ConditionNode
  /-- Condition sets proved sufficient in Lean (by checker acceptance). -/
  sufficientSets : List (List String)
  /-- Conditions proved redundant (removable). -/
  redundant : List String
  /-- Weakened variants tested (condition-id subsets). -/
  weakenedVariants : List (List String)
  /-- Certified counterexample refs for weaker variants (opaque ids). -/
  certifiedCounterexamples : List String
  /-- Unresolved necessity questions. -/
  unresolvedNecessity : List String
  /-- Optional necessity proofs (empty ⇒ no minimality claim). -/
  necessityProofs : List NecessityProof := []
  /-- Recommended theorem interface (human review still required). -/
  recommendedInterface : List String := []
  ranking : Option RankingExplanation := none
  /-- Hard invariant: `claimsMinimal = true` only when necessityProofs cover
  every recommended condition. Callers MUST use `withMinimalityClaim`. -/
  claimsMinimal : Bool := false
  deriving Repr, Inhabited

/-- Empty lattice scaffold. -/
def ConditionLattice.empty (artifactId : String) : ConditionLattice where
  artifactId := artifactId
  originalAssumptions := []
  proposed := []
  sufficientSets := []
  redundant := []
  weakenedVariants := []
  certifiedCounterexamples := []
  unresolvedNecessity := []

/-- Refuse minimality unless every recommended condition has a necessity proof. -/
def ConditionLattice.withMinimalityClaim (L : ConditionLattice) : ConditionLattice :=
  let covered := L.necessityProofs.map (·.conditionId)
  let ok :=
    L.recommendedInterface.all (fun id => covered.contains id) &&
      !L.recommendedInterface.isEmpty &&
      L.necessityProofs.all (fun p =>
        p.kind = .certifiedCounterexample ∨ p.kind = .redundancyProof)
  { L with claimsMinimal := ok }

/-- Invariant helper used by tests and Agent export. -/
def ConditionLattice.minimalitySound (L : ConditionLattice) : Bool :=
  !L.claimsMinimal ||
    (L.recommendedInterface.all fun id =>
      L.necessityProofs.any fun p => p.conditionId = id)

end MathEvidence.Hypothesis
