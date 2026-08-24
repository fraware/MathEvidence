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

Pins the environment used for elaboration and kernel acceptance. Current exact
certification uses the v0.4 profile, which can bind project revision, trusted
Lean source content, and the dependency lockfile in addition to toolchain,
Mathlib revision, and import names.

The structure can also represent historical v0.3 locks. Optional v0.4 fields
are omitted from canonical JSON when absent, preserving historical digests.
-/

namespace MathEvidence.Core

open Lean
open MathEvidence.Core.JsonCanonical

/-- Current schema profile for newly constructed environment locks. -/
def environmentLockSchemaVersion : String := "0.4.0"

/-- Declared Lean environment used for elaboration and kernel acceptance. -/
structure EnvironmentLock where
  schemaVersion : String := environmentLockSchemaVersion
  leanVersion : String
  lakeVersion : String := "lake"
  mathlibRevision : String
  /-- Ordered import module names that must be present. -/
  imports : List String := []
  /-- Optional opaque toolchain digest. -/
  toolchainDigest : Option ContentDigest := none
  /-- Exact project revision when available; v0.4 exact locks populate this. -/
  projectRevision : Option String := none
  /-- Digest of the trusted project Lean source tree; generated candidate modules excluded. -/
  projectSourceDigest : Option ContentDigest := none
  /-- Digest of the dependency lockfile used to resolve transitive packages. -/
  dependencyLockDigest : Option ContentDigest := none
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
  let withRevision :=
    match lock.projectRevision with
    | some revision => withTool ++ [("projectRevision", Json.str revision)]
    | none => withTool
  let withSource :=
    match lock.projectSourceDigest with
    | some d => withRevision ++ [("projectSourceDigest", Json.str d.value)]
    | none => withRevision
  let withDeps :=
    match lock.dependencyLockDigest with
    | some d => withSource ++ [("dependencyLockDigest", Json.str d.value)]
    | none => withSource
  Json.mkObj withDeps

/-- Digest of the environment lock binding payload. -/
def EnvironmentLock.digest (lock : EnvironmentLock) : Except String ContentDigest := do
  match JsonCanonical.digest lock.toBindingJson with
  | .ok d =>
    match ContentDigest.ofWire? d.value with
    | some cd => pure cd
    | none => throw "environment lock digest wire form invalid"
  | .error e => throw (toString e)

/-- Historical v0.3 MathEvidence rational-equality environment lock. -/
def EnvironmentLock.rationalEqualityDefault : EnvironmentLock :=
  { schemaVersion := "0.3.0"
    leanVersion := "leanprover/lean4:v4.14.0"
    mathlibRevision := "v4.14.0"
    imports := [
      "MathEvidence.Checkers.RationalEquality.Check",
      "MathEvidence.Checkers.RationalEquality.Soundness",
      "MathEvidence.Checkers.RationalEquality.Wire"
    ] }

end MathEvidence.Core
