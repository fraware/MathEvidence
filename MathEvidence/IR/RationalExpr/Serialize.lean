/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.Digest
import MathEvidence.IR.RationalExpr.Syntax

-- `CanonicalJson.digest` is provided by `Digest.lean`.

namespace MathEvidence.IR.RationalExpr

/-!
Serialization follows the Lean-side canonical JSON profile
(`docs/architecture/canonical-json.md`): UTF-8, no whitespace, lexicographic keys.
-/

open MathEvidence.Core.CanonicalJson

/-- Serialize a single expression tree. -/
partial def Expr.toCanonicalJson : Expr → String
  | .var i => object [("idx", ofNat i), ("tag", ofString "var")]
  | .int n => object [("n", ofInt n), ("tag", ofString "int")]
  | .rat n d => object [("d", ofNat d), ("n", ofInt n), ("tag", ofString "rat")]
  | .neg e => object [("e", e.toCanonicalJson), ("tag", ofString "neg")]
  | .add a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "add")]
  | .sub a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "sub")]
  | .mul a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "mul")]
  | .pow b k =>
    object [("base", b.toCanonicalJson), ("k", ofNat k), ("tag", ofString "pow")]
  | .div n d =>
    object [("den", d.toCanonicalJson), ("num", n.toCanonicalJson), ("tag", ofString "div")]

/-- Canonical variable declaration list (names in index order). -/
def varsCanonicalJson (names : List String) : String :=
  array (names.map ofString)

/-- Request body fields for digest binding (capability fixed by caller). -/
structure RequestPayload where
  capabilityId : String := "algebra.rational_equality"
  capabilityVersion : String := "0.1.0"
  varNames : List String
  lhs : Expr
  rhs : Expr
  knownAssumptions : List Expr := []
  claim : String := "soundResult"
  deriving Repr

/-- Canonical JSON for a rational-equality request (sorted keys). -/
def RequestPayload.toCanonicalJson (r : RequestPayload) : String :=
  object [
    ("capabilityId", ofString r.capabilityId),
    ("capabilityVersion", ofString r.capabilityVersion),
    ("claim", ofString r.claim),
    ("knownAssumptions", array (r.knownAssumptions.map Expr.toCanonicalJson)),
    ("lhs", r.lhs.toCanonicalJson),
    ("rhs", r.rhs.toCanonicalJson),
    ("varNames", varsCanonicalJson r.varNames)
  ]

/-- Request digest: SHA-256 of canonical JSON. -/
def RequestPayload.digest (r : RequestPayload) : MathEvidence.Core.EvidenceId :=
  MathEvidence.Core.CanonicalJson.digest r.toCanonicalJson

end MathEvidence.IR.RationalExpr
