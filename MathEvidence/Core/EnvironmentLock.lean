/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.JsonCanonical

/-!
# Environment lock (Wave 2 / ME-RV-020)

Pins the Lean toolchain, Mathlib revision, and import set used when elaborating
a theorem type. Digests participate in theorem identity and Certification Records.
-/

namespace MathEvidence.Core

open Lean
open MathEvidence.Core.JsonCanonical

/-- Schema / serializer profile for environment locks. -/
def environmentLockSchemaVersion : String := "0.3.0"

/-- Declared Lean environment used for elaboration and kernel acceptance. -/
structure EnvironmentLock where
  schemaVersion : String := environmentLockSchemaVersion
  leanVersion : String
  lakeVersion : String := "lake"
  mathlibRevision : String
  /-- Ordered import module names that must be present. -/
  imports : List String := []
  /-- Optional opaque toolchain digest (e.g. lake-manifest hash). -/
  toolchainDigest : Option ContentDigest := none
  deriving DecidableEq, Repr, Inhabited

/-- Canonical JSON binding payload (excludes self-digest). -/
def EnvironmentLock.toBindingJson (lock : EnvironmentLock) : Json :=
  let importsArr := (lock.imports.map Json.str).toArray
  let base : List (String × Json) := [
    ("schemaVersion", Json.str lock.schemaVersion),
    ("leanVersion", Json.str lock.leanVersion),
    ("lakeVersion", Json.str lock.lakeVersion),
    ("mathlibRevision", Json.str lock.mathlibRevision),
    ("imports", Json.arr importsArr)
  ]
  let withTool :=
    match lock.toolchainDigest with
    | some d => base ++ [("toolchainDigest", Json.str d.value)]
    | none => base
  Json.mkObj withTool

/-- Digest of the environment lock binding payload. -/
def EnvironmentLock.digest (lock : EnvironmentLock) : Except String ContentDigest := do
  -- Qualify JsonCanonical.digest: an unqualified `digest` resolves to this def.
  match JsonCanonical.digest lock.toBindingJson with
  | .ok d =>
    match ContentDigest.ofWire? d.value with
    | some cd => pure cd
    | none => throw "environment lock digest wire form invalid"
  | .error e => throw (toString e)

/-- Default MathEvidence rational-equality environment lock. -/
def EnvironmentLock.rationalEqualityDefault : EnvironmentLock :=
  { leanVersion := "leanprover/lean4:v4.14.0"
    mathlibRevision := "v4.14.0"
    imports := [
      "MathEvidence.Checkers.RationalEquality.Check",
      "MathEvidence.Checkers.RationalEquality.Soundness",
      "MathEvidence.Checkers.RationalEquality.Wire"
    ] }

end MathEvidence.Core
