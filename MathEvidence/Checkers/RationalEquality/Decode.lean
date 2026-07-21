/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.IR.RationalExpr.Wire

namespace MathEvidence.Checkers.RationalEquality.Decode

open Lean
open MathEvidence.Core
open MathEvidence.IR.RationalExpr
open MathEvidence.IR.RationalExpr.Wire

/-!
Decode adapter wire JSON (request + certificate) into checker structures.
Digest fields are taken from the wire (adapters bind digests); Lean verifies
binding equality and mathematical evidence, not Python canonicalization.
-/

def decodeVarNames (j : Json) : Except DecodeError (List String) := do
  let vars ← match j.getObjVal? "variables" with
    | .ok v => pure v
    | .error m => .error (.json m)
  let arr ← match vars.getArr? with
    | .ok a => pure a
    | .error m => .error (.json m)
  arr.toList.mapM fun v => do
    match v.getObjValAs? String "name" with
    | .ok s => pure s
    | .error m => .error (.json m)

def decodeClaim (j : Json) : Except DecodeError Claim := do
  let names ← decodeVarNames j
  let lhs ← decodeExpr names (← match j.getObjVal? "lhs" with
    | .ok x => pure x | .error m => .error (.json m))
  let rhs ← decodeExpr names (← match j.getObjVal? "rhs" with
    | .ok x => pure x | .error m => .error (.json m))
  let claimClass :=
    match j.getObjValAs? String "requestedClaim" with
    | .ok s => (ClaimClass.ofWire? s).getD .soundResult
    | .error _ => .soundResult
  pure { varNames := names, lhs := lhs, rhs := rhs, claimClass := claimClass }

def decodeRequest (j : Json) : Except DecodeError Request := do
  let claim ← decodeClaim j
  let digestStr ← match j.getObjValAs? String "requestDigest" with
    | .ok s => pure s
    | .error m => .error (.json m)
  let digest ← match RequestDigest.ofWire? digestStr with
    | some d => pure d
    | none => .error (.json s!"invalid requestDigest {digestStr}")
  pure { claim := claim, requestDigest := digest }

def decodeCertificate (j : Json) (varNames : List String) : Except DecodeError Certificate := do
  let digestStr ← match j.getObjValAs? String "requestDigest" with
    | .ok s => pure s
    | .error m => .error (.json m)
  let digest ← match RequestDigest.ofWire? digestStr with
    | some d => pure d
    | none => .error (.json s!"invalid certificate requestDigest {digestStr}")
  let factorsJ ← match j.getObjVal? "denominatorFactors" with
    | .ok f => pure f
    | .error m => .error (.json m)
  let arr ← match factorsJ.getArr? with
    | .ok a => pure a
    | .error m => .error (.json m)
  let factors ← arr.toList.mapM fun entry => do
    let exprJ ← match entry.getObjVal? "expr" with
      | .ok e => pure e
      | .error _ => pure entry
    decodeExpr varNames exprJ
  pure { requestDigest := digest, denomFactors := factors }

def decodeRequestString (s : String) : Except DecodeError Request := do
  let j ← match Json.parse s with
    | .ok j => pure j
    | .error m => .error (.json m)
  decodeRequest j

def decodeCertificateString (s : String) (varNames : List String) :
    Except DecodeError Certificate := do
  let j ← match Json.parse s with
    | .ok j => pure j
    | .error m => .error (.json m)
  decodeCertificate j varNames

end MathEvidence.Checkers.RationalEquality.Decode
