/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.ReifyMatrix
import MathEvidence.Tactic.ReifyFinitePredicate
import MathEvidence.Tactic.ReifyPolynomial

/-!
# Reifier registry

Compile-time capability ledger for tactic-side reifiers. Discovery and status
surfaces consult `liveKinds` / `statusOf?` instead of hardcoding rational-only
availability.
-/

namespace MathEvidence.Tactic.ReifierRegistry

inductive ReifierKind where
  | rational
  | matrix
  | counterexample
  | ideal
  deriving DecidableEq, Repr, Inhabited

inductive ReifierStatus where
  | live
  | experimental
  deriving DecidableEq, Repr, Inhabited

structure Entry where
  kind : ReifierKind
  status : ReifierStatus
  moduleName : String
  capabilityId : String
  note : String
  deriving Repr

def entries : List Entry := [
  { kind := .rational
    status := .live
    moduleName := "MathEvidence.Tactic.ReifyRational"
    capabilityId := "algebra.rational_equality"
    note := "Meta reification for Rat equality goals is implemented." },
  { kind := .matrix
    status := .live
    moduleName := "MathEvidence.Tactic.ReifyMatrix"
    capabilityId := "algebra.linear_algebra"
    note := "Meta reification for MatrixExpr goals via mathevidence_linear_algebra." },
  { kind := .counterexample
    status := .live
    moduleName := "MathEvidence.Tactic.ReifyFinitePredicate"
    capabilityId := "logic.finite_counterexample"
    note := "Meta reification for Fin/Bool/bounded Nat/Int predicates." },
  { kind := .ideal
    status := .live
    moduleName := "MathEvidence.Tactic.ReifyPolynomial"
    capabilityId := "algebra.ideal_membership"
    note := "Meta reification for univariate Ideal.span and MvPolynomial Fin 2/3/4." }
]

def statusOf? (kind : ReifierKind) : Option ReifierStatus :=
  (entries.find? (·.kind = kind)).map (·.status)

def entryOf? (kind : ReifierKind) : Option Entry :=
  entries.find? (·.kind = kind)

/-- Kinds with a live Meta reifier (compile-time filtered). -/
def liveKinds : List ReifierKind :=
  entries.filterMap fun e =>
    if e.status = .live then some e.kind else none

/-- True when the registry marks the kind live. -/
def isLive (kind : ReifierKind) : Bool :=
  statusOf? kind = some .live

theorem rational_is_live : isLive .rational = true := by native_decide
theorem matrix_is_live : isLive .matrix = true := by native_decide
theorem counterexample_is_live : isLive .counterexample = true := by native_decide
theorem ideal_is_live : isLive .ideal = true := by native_decide

/-- Discovery must not claim a reifier that the registry marks unavailable. -/
theorem liveKinds_complete :
    liveKinds = [.rational, .matrix, .counterexample, .ideal] := by
  native_decide

end MathEvidence.Tactic.ReifierRegistry
