/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.RationalExpr.Serialize
import MathEvidence.IR.CalculusExpr.Syntax

namespace MathEvidence.IR.CalculusExpr

open MathEvidence.Core.CanonicalJson
open MathEvidence.IR.RationalExpr (Expr)

def InitialCondition.toCanonicalJson (ic : InitialCondition) : String :=
  object [
    ("point", ic.point.toCanonicalJson),
    ("value", ic.value.toCanonicalJson)
  ]

/-- Lean-side request payload for digest binding (index-based exprs). -/
structure RequestPayload where
  capabilityId : String := "algebra.formal_rational_calculus"
  capabilityVersion : String := "0.1.0"
  operation : Operation
  varNames : List String
  independentVar : Nat
  dependentVar : Nat := 1
  expr : Expr
  candidate : Expr
  domainConditions : List Expr := []
  initialConditions : List InitialCondition := []
  odeRhs : Option Expr := none
  recurrenceRhs : Option Expr := none
  claim : String := "candidate"
  deriving Repr

def RequestPayload.toCanonicalJson (r : RequestPayload) : String :=
  object [
    ("capabilityId", ofString r.capabilityId),
    ("capabilityVersion", ofString r.capabilityVersion),
    ("candidate", r.candidate.toCanonicalJson),
    ("claim", ofString r.claim),
    ("dependentVar", ofNat r.dependentVar),
    ("domainConditions", array (r.domainConditions.map Expr.toCanonicalJson)),
    ("expr", r.expr.toCanonicalJson),
    ("independentVar", ofNat r.independentVar),
    ("initialConditions", array (r.initialConditions.map InitialCondition.toCanonicalJson)),
    ("odeRhs",
      match r.odeRhs with
      | none => "null"
      | some e => e.toCanonicalJson),
    ("operation", ofString r.operation.toWire),
    ("recurrenceRhs",
      match r.recurrenceRhs with
      | none => "null"
      | some e => e.toCanonicalJson),
    ("varNames", array (r.varNames.map ofString))
  ]

def RequestPayload.digest (r : RequestPayload) : MathEvidence.Core.RequestDigest :=
  ⟨(MathEvidence.Core.CanonicalJson.digest r.toCanonicalJson).value⟩

end MathEvidence.IR.CalculusExpr
