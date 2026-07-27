/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.JsonCanonical
import MathEvidence.Core.TheoremIdentity

/-!
# Replay target (Wave 2 / ME-RV-020)

Identifies the exact original Lean theorem type that kernel replay must elaborate.
Canonical theorem type is derived from elaborated Lean syntax — pretty-printed
source text alone is insufficient.
-/

namespace MathEvidence.Core

open Lean
open MathEvidence.Core.JsonCanonical

def replayTargetSchemaVersion : String := "0.3.0"

/-- Source span inside `sourceFile` (1-based line/column when known). -/
structure SourceSpan where
  startLine : Nat := 0
  startCol : Nat := 0
  endLine : Nat := 0
  endCol : Nat := 0
  deriving DecidableEq, Repr, Inhabited

def SourceSpan.toJson (s : SourceSpan) : Json :=
  Json.mkObj [
    ("startLine", Json.num s.startLine),
    ("startCol", Json.num s.startCol),
    ("endLine", Json.num s.endLine),
    ("endCol", Json.num s.endCol)
  ]

/-- Exact theorem target for kernel replay. -/
structure ReplayTarget where
  schemaVersion : String := replayTargetSchemaVersion
  moduleName : String
  declarationName : String
  /-- Canonical elaborated theorem type (serializer-owned string). -/
  theoremTypeCanonical : String
  theoremTypeDigest : TheoremDigest
  sourceRevision : String
  sourceFile : String
  sourceSpan : SourceSpan := {}
  environmentLockDigest : ContentDigest
  capability : CapabilityRef
  requestDigest : RequestDigest
  /-- Optional candidate bundle digest this target is bound to. -/
  candidateBundleDigest : Option BundleDigest := none
  deriving DecidableEq, Repr, Inhabited

def ReplayTarget.toBindingJson (t : ReplayTarget) : Json :=
  let base : List (String × Json) := [
    ("schemaVersion", Json.str t.schemaVersion),
    ("moduleName", Json.str t.moduleName),
    ("declarationName", Json.str t.declarationName),
    ("theoremTypeCanonical", Json.str t.theoremTypeCanonical),
    ("theoremTypeDigest", Json.str t.theoremTypeDigest.value),
    ("sourceRevision", Json.str t.sourceRevision),
    ("sourceFile", Json.str t.sourceFile),
    ("sourceSpan", SourceSpan.toJson t.sourceSpan),
    ("environmentLockDigest", Json.str t.environmentLockDigest.value),
    ("capability", Json.mkObj [
      ("id", Json.str t.capability.id.id),
      ("version", Json.str t.capability.version.version)
    ]),
    ("requestDigest", Json.str t.requestDigest.value)
  ]
  let withBundle :=
    match t.candidateBundleDigest with
    | some b => base ++ [("candidateBundleDigest", Json.str b.value)]
    | none => base
  Json.mkObj withBundle

def ReplayTarget.digest (t : ReplayTarget) : Except String ContentDigest := do
  match JsonCanonical.digest t.toBindingJson with
  | .ok d =>
    match ContentDigest.ofWire? d.value with
    | some cd => pure cd
    | none => throw "replay target digest wire form invalid"
  | .error e => throw (toString e)

def ReplayTarget.wellFormed (t : ReplayTarget) : Bool :=
  t.schemaVersion == replayTargetSchemaVersion &&
    !t.moduleName.isEmpty &&
    !t.declarationName.isEmpty &&
    !t.theoremTypeCanonical.isEmpty &&
    isSha256DigestWire t.theoremTypeDigest.value &&
    isSha256DigestWire t.environmentLockDigest.value &&
    isSha256DigestWire t.requestDigest.value &&
    !t.sourceFile.isEmpty

end MathEvidence.Core
