/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.TraceToPlan.Basic

namespace MathEvidence.TraceToPlan

/-! Smoke tests for Product 05 invariants. -/

def hintNode : PlanNode where
  id := "h1"
  claim := "try substitution"
  stepKind := .searchHint
  status := .proposed
  advancesProofStatus := false

def badHintNode : PlanNode where
  id := "bad"
  claim := "illegal advance"
  stepKind := .searchHint
  status := .proposed
  advancesProofStatus := true

def reconNode : PlanNode where
  id := "r1"
  claim := "rational equality"
  stepKind := .reconstructibleComputation
  status := .proved
  advancesProofStatus := true
  suggestedCapability := some "algebra.rational_equality"

example : hintNode.wellFormed = true := by native_decide
example : badHintNode.wellFormed = false := by native_decide
example : reconNode.wellFormed = true := by native_decide

def samplePlan : ProofPlan where
  targetTheorem := "lhs = rhs"
  nodes := [hintNode, reconNode]
  edges := [{ fromId := "r1", toId := "target" }]

example : samplePlan.nodesWellFormed = true := by native_decide

/-- Multi-step reconstructible plan: only reconstructible nodes advance. -/
def reconNode2 : PlanNode where
  id := "r2"
  claim := "denom cover"
  stepKind := .reconstructibleComputation
  status := .proved
  advancesProofStatus := true
  suggestedCapability := some "algebra.rational_equality"

def multiStepPlan : ProofPlan where
  targetTheorem := "(x^2-1)/(x-1)=x+1"
  nodes := [hintNode, reconNode, reconNode2]
  edges := [
    { fromId := "r1", toId := "target" },
    { fromId := "r2", toId := "target" }
  ]

example : multiStepPlan.nodesWellFormed = true := by native_decide

example :
    (multiStepPlan.nodes.filter (·.advancesProofStatus)).length = 2 := by
  native_decide

end MathEvidence.TraceToPlan
