/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EnvironmentLock
import MathEvidence.Core.JsonCanonical

/-!
# Theorem identity (Wave 2 / ME-RV-020)

Digests the **elaborated** theorem type (not pretty-printed source alone).

Serializer profile: **mathevidence-theorem-identity-0.3**

The digest input includes:

* fully elaborated expression serialization via kernel `Expr` / `Level` walk
  (`MathEvidence.Core.ExprSerialize`; not `ppExpr`);
* universe level parameters;
* local binder types and binder information;
* constant names referenced by the type;
* imported environment lock digest.

A future serializer change requires incrementing `theoremIdentitySerializerVersion`
and the theorem-identity schema version.

Proof-term digests use the same structural `ExprSerialize` walk when a
declaration value is available (`proofTermDigestOfConst?`). Lean-internal
`Expr.hash` across compiler revisions is still not claimed and must not be
used for Certification Records.
-/

namespace MathEvidence.Core

open Lean
open MathEvidence.Core.JsonCanonical

/-- Serializer profile version embedded in every theorem-identity digest. -/
def theoremIdentitySerializerVersion : String := "mathevidence-theorem-identity-0.3"

/-- Schema version for theorem-identity role payloads. -/
def theoremIdentitySchemaVersion : String := "0.3.0"

/-- Binder kind encoded into the structural serializer. -/
inductive BinderKindWire where
  | default
  | implicit
  | strictImplicit
  | instImplicit
  deriving DecidableEq, Repr, Inhabited

def BinderKindWire.toWire : BinderKindWire → String
  | .default => "default"
  | .implicit => "implicit"
  | .strictImplicit => "strictImplicit"
  | .instImplicit => "instImplicit"

/-- One binder in the elaborated telescope. -/
structure TheoremBinder where
  name : String
  kind : BinderKindWire := .default
  /-- Structural serialization of the binder type (serializer-owned string). -/
  typeSerialization : String
  deriving DecidableEq, Repr, Inhabited

/-- Structural theorem-type identity (pre-digest). -/
structure TheoremTypeIdentity where
  schemaVersion : String := theoremIdentitySchemaVersion
  serializerVersion : String := theoremIdentitySerializerVersion
  /-- Fully elaborated expression serialization (not pretty-print alone). -/
  elaboratedSerialization : String
  universeParams : List String := []
  binders : List TheoremBinder := []
  /-- Reducibility-normalized constant names referenced by the type. -/
  constantNames : List String := []
  environmentLockDigest : ContentDigest
  deriving DecidableEq, Repr, Inhabited

/-- Full theorem identity role payload (type + proof declaration digests). -/
structure TheoremIdentity where
  schemaVersion : String := theoremIdentitySchemaVersion
  serializerVersion : String := theoremIdentitySerializerVersion
  declarationName : String
  theoremTypeDigest : TheoremDigest
  proofDeclarationDigest : ContentDigest
  environmentLockDigest : ContentDigest
  /-- Optional structural snapshot used to recompute `theoremTypeDigest`. -/
  typeIdentity : Option TheoremTypeIdentity := none
  deriving DecidableEq, Repr, Inhabited

def TheoremBinder.toJson (b : TheoremBinder) : Json :=
  Json.mkObj [
    ("name", Json.str b.name),
    ("kind", Json.str b.kind.toWire),
    ("typeSerialization", Json.str b.typeSerialization)
  ]

def TheoremTypeIdentity.toBindingJson (t : TheoremTypeIdentity) : Json :=
  Json.mkObj [
    ("schemaVersion", Json.str t.schemaVersion),
    ("serializerVersion", Json.str t.serializerVersion),
    ("elaboratedSerialization", Json.str t.elaboratedSerialization),
    ("universeParams", Json.arr (t.universeParams.map Json.str).toArray),
    ("binders", Json.arr (t.binders.map TheoremBinder.toJson).toArray),
    ("constantNames", Json.arr (t.constantNames.map Json.str).toArray),
    ("environmentLockDigest", Json.str t.environmentLockDigest.value)
  ]

/-- Digest over elaborated serialization + binders + environment lock. -/
def TheoremTypeIdentity.digest (t : TheoremTypeIdentity) : Except String TheoremDigest := do
  match JsonCanonical.digest t.toBindingJson with
  | .ok d =>
    match TheoremDigest.ofWire? d.value with
    | some td => pure td
    | none => throw "theorem type digest wire form invalid"
  | .error e => throw (toString e)

def TheoremIdentity.toBindingJson (t : TheoremIdentity) : Json :=
  Json.mkObj [
    ("schemaVersion", Json.str t.schemaVersion),
    ("serializerVersion", Json.str t.serializerVersion),
    ("declarationName", Json.str t.declarationName),
    ("theoremTypeDigest", Json.str t.theoremTypeDigest.value),
    ("proofDeclarationDigest", Json.str t.proofDeclarationDigest.value),
    ("environmentLockDigest", Json.str t.environmentLockDigest.value)
  ]

def TheoremIdentity.wellFormed (t : TheoremIdentity) : Bool :=
  t.schemaVersion == theoremIdentitySchemaVersion &&
    t.serializerVersion == theoremIdentitySerializerVersion &&
    !t.declarationName.isEmpty &&
    isSha256DigestWire t.theoremTypeDigest.value &&
    isSha256DigestWire t.proofDeclarationDigest.value &&
    isSha256DigestWire t.environmentLockDigest.value

end MathEvidence.Core
