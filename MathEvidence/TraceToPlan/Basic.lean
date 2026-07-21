/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.TraceToPlan

/-!
# Trace-to-Plan (Product 05)

Untrusted traces become a proof-plan DAG. Only reconstructible step kinds may
advance formal proof status; hints never do.
-/

/-- Product 05 step taxonomy. -/
inductive StepKind where
  | directProofStep
  | reconstructibleComputation
  | lemmaCandidate
  | searchHint
  | diagnosticMetadata
  deriving DecidableEq, Repr, Inhabited

def StepKind.toWire : StepKind → String
  | .directProofStep => "direct_proof_step"
  | .reconstructibleComputation => "reconstructible_computation"
  | .lemmaCandidate => "lemma_candidate"
  | .searchHint => "search_hint"
  | .diagnosticMetadata => "diagnostic_metadata"

def StepKind.ofWire? : String → Option StepKind
  | "direct_proof_step" => some .directProofStep
  | "reconstructible_computation" => some .reconstructibleComputation
  | "lemma_candidate" => some .lemmaCandidate
  | "search_hint" => some .searchHint
  | "diagnostic_metadata" => some .diagnosticMetadata
  | _ => none

/-- Whether this kind is allowed to advance proof status (when verified). -/
def StepKind.mayAdvanceProofStatus : StepKind → Bool
  | .directProofStep | .reconstructibleComputation => true
  | .lemmaCandidate | .searchHint | .diagnosticMetadata => false

/-- Plan node status. -/
inductive NodeStatus where
  | proved
  | checkable
  | proposed
  | rejected
  | blocked
  deriving DecidableEq, Repr, Inhabited

def NodeStatus.toWire : NodeStatus → String
  | .proved => "proved"
  | .checkable => "checkable"
  | .proposed => "proposed"
  | .rejected => "rejected"
  | .blocked => "blocked"

/-- A single plan node (Lean-side stub aligned with `schemas/proof-plan.schema.json`). -/
structure PlanNode where
  id : String
  claim : String
  stepKind : StepKind
  status : NodeStatus
  advancesProofStatus : Bool := false
  suggestedCapability : Option String := none
  deriving Repr, Inhabited

/-- Invariant: non-reconstructible kinds must not advance proof status. -/
def PlanNode.hintSafe (n : PlanNode) : Bool :=
  !n.advancesProofStatus || n.stepKind.mayAdvanceProofStatus

/-- Invariant: advancing requires proved or checkable status. -/
def PlanNode.advanceStatusOk (n : PlanNode) : Bool :=
  !n.advancesProofStatus || n.status == .proved || n.status == .checkable

/-- Combined node well-formedness for Product 05 acceptance criteria 1–3. -/
def PlanNode.wellFormed (n : PlanNode) : Bool :=
  n.hintSafe && n.advanceStatusOk

/-- Edge in the proof-plan DAG. -/
structure PlanEdge where
  fromId : String
  toId : String
  deriving Repr, Inhabited

/-- Proof-plan DAG stub. -/
structure ProofPlan where
  targetTheorem : String
  nodes : List PlanNode
  edges : List PlanEdge
  deriving Repr, Inhabited

def ProofPlan.nodesWellFormed (p : ProofPlan) : Bool :=
  p.nodes.all PlanNode.wellFormed

/-- Successors of `id` in the edge list. -/
def ProofPlan.successors (p : ProofPlan) (id : String) : List String :=
  p.edges.filterMap fun e => if e.fromId == id then some e.toId else none

/-- DFS cycle detection from `start`, with path stack `stack`. -/
partial def ProofPlan.reachesCycleFrom
    (p : ProofPlan) (start : String) (stack : List String) : Bool :=
  if stack.contains start then true
  else
    let stack' := start :: stack
    (p.successors start).any fun nxt => p.reachesCycleFrom nxt stack'

/-- Executable DAG acyclicity: no node reaches itself via directed edges. -/
def ProofPlan.isAcyclic (p : ProofPlan) : Bool :=
  !(p.nodes.any fun n => p.reachesCycleFrom n.id [])

/-- Combined structural gate: node WF + acyclicity. -/
def ProofPlan.structurallyOk (p : ProofPlan) : Bool :=
  p.nodesWellFormed && p.isAcyclic

/-- Hints never alter theorem status when the node is well-formed. -/
theorem searchHint_never_advances (n : PlanNode)
    (hk : n.stepKind = .searchHint) (hw : n.hintSafe = true) :
    n.advancesProofStatus = false := by
  cases hadv : n.advancesProofStatus
  · rfl
  · unfold PlanNode.hintSafe at hw
    simp [hk, hadv, StepKind.mayAdvanceProofStatus] at hw

/-- Diagnostic metadata never advances when well-formed. -/
theorem diagnostic_never_advances (n : PlanNode)
    (hk : n.stepKind = .diagnosticMetadata) (hw : n.hintSafe = true) :
    n.advancesProofStatus = false := by
  cases hadv : n.advancesProofStatus
  · rfl
  · unfold PlanNode.hintSafe at hw
    simp [hk, hadv, StepKind.mayAdvanceProofStatus] at hw

/-- Concrete acyclic plan accepts. -/
theorem example_acyclic_plan :
    let p : ProofPlan := {
      targetTheorem := "demo"
      nodes := [
        { id := "a", claim := "A", stepKind := .directProofStep, status := .proved,
          advancesProofStatus := true },
        { id := "b", claim := "B", stepKind := .lemmaCandidate, status := .proposed }
      ]
      edges := [{ fromId := "a", toId := "b" }]
    }
    p.isAcyclic = true ∧ p.structurallyOk = true := by
  native_decide

/-- Concrete cyclic plan rejects acyclicity. -/
theorem example_cyclic_plan_rejected :
    let p : ProofPlan := {
      targetTheorem := "cycle"
      nodes := [
        { id := "a", claim := "A", stepKind := .directProofStep, status := .checkable,
          advancesProofStatus := true },
        { id := "b", claim := "B", stepKind := .directProofStep, status := .checkable,
          advancesProofStatus := true }
      ]
      edges := [{ fromId := "a", toId := "b" }, { fromId := "b", toId := "a" }]
    }
    p.isAcyclic = false := by
  native_decide

end MathEvidence.TraceToPlan
