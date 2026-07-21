/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Stable capability identifier (e.g. `algebra.rational_equality`). -/
structure CapabilityId where
  id : String
  deriving DecidableEq, Repr, Inhabited

/-- Semantic version string for a capability schema / checker contract. -/
structure CapabilityVersion where
  version : String
  deriving DecidableEq, Repr, Inhabited

/-- Capability reference used in requests and bundle manifests. -/
structure CapabilityRef where
  id : CapabilityId
  version : CapabilityVersion
  deriving DecidableEq, Repr, Inhabited

/-- First Milestone-1 capability identifier. -/
def CapabilityId.rationalEquality : CapabilityId :=
  ⟨"algebra.rational_equality"⟩

/-- Initial capability contract version for rational equality. -/
def CapabilityVersion.v0_1_0 : CapabilityVersion := ⟨"0.1.0"⟩

def CapabilityRef.rationalEquality : CapabilityRef :=
  ⟨.rationalEquality, .v0_1_0⟩

/-- Milestone-2 exact linear algebra (inverse / system / kernel / det). -/
def CapabilityId.linearAlgebra : CapabilityId :=
  ⟨"algebra.linear_algebra"⟩

def CapabilityRef.linearAlgebra : CapabilityRef :=
  ⟨.linearAlgebra, .v0_1_0⟩

/-- Milestone-2 finite counterexample (typed witness refutation). -/
def CapabilityId.finiteCounterexample : CapabilityId :=
  ⟨"logic.finite_counterexample"⟩

def CapabilityRef.finiteCounterexample : CapabilityRef :=
  ⟨.finiteCounterexample, .v0_1_0⟩

/-- Formal rational calculus over rational-expression syntax. -/
def CapabilityId.formalRationalCalculus : CapabilityId :=
  ⟨"algebra.formal_rational_calculus"⟩

/-- Deprecated alias — prefer `formalRationalCalculus`. -/
abbrev CapabilityId.symbolicCalculus := CapabilityId.formalRationalCalculus

def CapabilityRef.formalRationalCalculus : CapabilityRef :=
  ⟨.formalRationalCalculus, .v0_1_0⟩

/-- Deprecated alias — prefer `formalRationalCalculus`. -/
abbrev CapabilityRef.symbolicCalculus := CapabilityRef.formalRationalCalculus

/-- Analytic calculus capability for Mathlib `HasDerivAt` / ODE fragments. -/
def CapabilityId.analyticCalculus : CapabilityId :=
  ⟨"analysis.analytic_calculus"⟩

def CapabilityRef.analyticCalculus : CapabilityRef :=
  ⟨.analyticCalculus, .v0_1_0⟩

end MathEvidence.Core
