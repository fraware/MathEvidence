/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.

Thin registry metadata pointers for Product 07 discovery.
-/
namespace MathEvidence.Registry

/-- Placeholder marker that the Registry package is linked. -/
def packageName : String := "MathEvidence.Registry"

structure CapabilityPointer where
  id : String
  version : String
  registryPath : String
  leanIRPackage : String
  leanCheckerPackage : String
  deriving Repr, BEq

/-- Machine-readable capability IDs mirrored from `registry/capabilities/`. -/
def rationalEquality : CapabilityPointer where
  id := "algebra.rational_equality"
  version := "0.1.0"
  registryPath := "registry/capabilities/algebra.rational_equality.json"
  leanIRPackage := "MathEvidence.IR.RationalExpr"
  leanCheckerPackage := "MathEvidence.Checkers.RationalEquality"

def linearAlgebra : CapabilityPointer where
  id := "algebra.linear_algebra"
  version := "0.1.0"
  registryPath := "registry/capabilities/algebra.linear_algebra.json"
  leanIRPackage := "MathEvidence.IR.MatrixExpr"
  leanCheckerPackage := "MathEvidence.Checkers.LinearAlgebra"

def finiteCounterexample : CapabilityPointer where
  id := "logic.finite_counterexample"
  version := "0.1.0"
  registryPath := "registry/capabilities/logic.finite_counterexample.json"
  leanIRPackage := "MathEvidence.IR.FinitePredicate"
  leanCheckerPackage := "MathEvidence.Checkers.Counterexample"

def symbolicCalculus : CapabilityPointer where
  id := "analysis.symbolic_calculus"
  version := "0.1.0"
  registryPath := "registry/capabilities/analysis.symbolic_calculus.json"
  leanIRPackage := "MathEvidence.IR.CalculusExpr"
  leanCheckerPackage := "MathEvidence.Checkers.Calculus"

/-- Federated: external checker authority; MathEvidence metadata only. -/
def groebnerMembership : CapabilityPointer where
  id := "algebra.groebner_membership"
  version := "0.1.0"
  registryPath := "registry/capabilities/algebra.groebner_membership.json"
  leanIRPackage := "external"
  leanCheckerPackage := "external:GroebnerCert"

def satUnsat : CapabilityPointer where
  id := "logic.sat_unsat"
  version := "0.1.0"
  registryPath := "registry/capabilities/logic.sat_unsat.json"
  leanIRPackage := "external"
  leanCheckerPackage := "external:SATChecker"

def pseudoBoolean : CapabilityPointer where
  id := "logic.pseudo_boolean"
  version := "0.1.0"
  registryPath := "registry/capabilities/logic.pseudo_boolean.json"
  leanIRPackage := "external"
  leanCheckerPackage := "external:PseudoBooleanChecker"

def smt : CapabilityPointer where
  id := "logic.smt"
  version := "0.1.0"
  registryPath := "registry/capabilities/logic.smt.json"
  leanIRPackage := "external"
  leanCheckerPackage := "external:LeanSMT"

def ownedCapabilityPointers : List CapabilityPointer :=
  [rationalEquality, linearAlgebra, finiteCounterexample, symbolicCalculus]

def federatedCapabilityPointers : List CapabilityPointer :=
  [groebnerMembership, satUnsat, pseudoBoolean, smt]

def allCapabilityPointers : List CapabilityPointer :=
  ownedCapabilityPointers ++ federatedCapabilityPointers

end MathEvidence.Registry
