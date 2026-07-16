/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.Digest
import MathEvidence.IR.MatrixExpr.Syntax

namespace MathEvidence.IR.MatrixExpr

open MathEvidence.Core.CanonicalJson

/-- Serialize a rational literal. -/
def RatLit.toCanonicalJson (r : RatLit) : String :=
  object [
    ("den", ofNat r.den),
    ("num", MathEvidence.Core.CanonicalJson.ofInt r.num),
    ("tag", ofString "rat")
  ]

/-- Serialize a vector. -/
def Vector.toCanonicalJson (v : Vector) : String :=
  array (v.map RatLit.toCanonicalJson)

/-- Serialize a matrix. -/
def Matrix.toCanonicalJson (A : Matrix) : String :=
  object [
    ("cols", ofNat A.ncols),
    ("entries", array (A.entries.map Vector.toCanonicalJson)),
    ("rows", ofNat A.nrows),
    ("tag", ofString "matrix")
  ]

/-- Request body for digest binding. -/
structure RequestPayload where
  capabilityId : String := "algebra.linear_algebra"
  capabilityVersion : String := "0.1.0"
  operation : String
  matrix : Matrix
  rhs : Vector := []
  claimedDet : Option RatLit := none
  claim : String := "witness"
  deriving Repr

def RequestPayload.toCanonicalJson (r : RequestPayload) : String :=
  object [
    ("capabilityId", ofString r.capabilityId),
    ("capabilityVersion", ofString r.capabilityVersion),
    ("claim", ofString r.claim),
    ("claimedDet",
      match r.claimedDet with
      | none => "null"
      | some d => d.toCanonicalJson),
    ("matrix", r.matrix.toCanonicalJson),
    ("operation", ofString r.operation),
    ("rhs", r.rhs.toCanonicalJson)
  ]

def RequestPayload.digest (r : RequestPayload) : MathEvidence.Core.EvidenceId :=
  MathEvidence.Core.CanonicalJson.digest r.toCanonicalJson

end MathEvidence.IR.MatrixExpr
