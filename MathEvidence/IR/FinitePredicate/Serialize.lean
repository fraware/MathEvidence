/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.Digest
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.IR.FinitePredicate

open MathEvidence.Core.CanonicalJson

def Ty.toWire : Ty → String
  | .bool => "bool"
  | .nat => "nat"
  | .int => "int"

def Val.toCanonicalJson : Val → String
  | .bool b => object [("tag", ofString "bool"), ("v", ofBool b)]
  | .nat n => object [("tag", ofString "nat"), ("v", ofNat n)]
  | .int i => object [("tag", ofString "int"), ("v", ofInt i)]

def Domain.toCanonicalJson (d : Domain) : String :=
  object [
    ("bound",
      match d.bound with
      | none => "null"
      | some b => ofNat b),
    ("ty", ofString d.ty.toWire)
  ]

partial def Term.toCanonicalJson : Term → String
  | .var i => object [("idx", ofNat i), ("tag", ofString "var")]
  | .lit v => object [("tag", ofString "lit"), ("v", v.toCanonicalJson)]
  | .neg t => object [("e", t.toCanonicalJson), ("tag", ofString "neg")]
  | .add a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "add")]
  | .sub a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "sub")]
  | .mul a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "mul")]

partial def Pred.toCanonicalJson : Pred → String
  | .eq a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "eq")]
  | .ne a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "ne")]
  | .le a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "le")]
  | .lt a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "lt")]
  | .not p => object [("e", p.toCanonicalJson), ("tag", ofString "not")]
  | .and a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "and")]
  | .or a b =>
    object [("left", a.toCanonicalJson), ("right", b.toCanonicalJson), ("tag", ofString "or")]

structure RequestPayload where
  capabilityId : String := "logic.finite_counterexample"
  capabilityVersion : String := "0.1.0"
  varNames : List String
  domains : List Domain
  pred : Pred
  claim : String := "refutation"
  deriving Repr

def RequestPayload.toCanonicalJson (r : RequestPayload) : String :=
  object [
    ("capabilityId", ofString r.capabilityId),
    ("capabilityVersion", ofString r.capabilityVersion),
    ("claim", ofString r.claim),
    ("domains", array (r.domains.map Domain.toCanonicalJson)),
    ("pred", r.pred.toCanonicalJson),
    ("varNames", array (r.varNames.map ofString))
  ]

def RequestPayload.digest (r : RequestPayload) : MathEvidence.Core.EvidenceId :=
  MathEvidence.Core.CanonicalJson.digest r.toCanonicalJson

end MathEvidence.IR.FinitePredicate
