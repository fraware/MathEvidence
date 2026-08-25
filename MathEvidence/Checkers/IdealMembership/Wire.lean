/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.JsonCanonical
import MathEvidence.Checkers.IdealMembership.Spec
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.IR.Polynomial.Normalize

/-!
# Ideal-membership wire digests (Lean ↔ Python)

This module is the Lean-side authority for the request-binding projection used
by `schemas/ideal-membership-request.schema.json`.  The projection intentionally
contains exactly the request fields that participate in `requestDigest` for the
exact replay vertical.  In particular:

* integer polynomial coefficients are JSON numbers, not strings;
* no internal `ResourcePolicy` field is serialized because the wire schema does
  not contain one;
* capability version and requested claim are explicit;
* optional request notes are bound when present.

The generated replay path constructs a `Request` with the digest computed here,
so an orchestration-side translation error cannot merely copy a request digest
onto different Lean semantics and still satisfy the checker.
-/

namespace MathEvidence.Checkers.IdealMembership.Wire

open Lean
open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

private def intJson (value : Int) : Json :=
  Json.num { mantissa := value, exponent := 0 }

def termToJson {m : Nat} (t : Term m) : Json :=
  Json.mkObj
    [("coefficient", intJson t.coefficient),
     ("exponents",
      Json.arr ((t.monomial.exponents.toList.map fun (e : Nat) => Json.num e).toArray))]

def polyToJson {m : Nat} (p : SparsePoly m) : Json :=
  Json.mkObj
    [("varCount", Json.num m),
     ("terms", Json.arr (p.terms.toArray.map termToJson))]

def claimClassToWire : ClaimClass → String
  | .witness => "witness"
  | .candidate => "candidate"
  | .soundResult => "soundResult"

private def notesJson (notes : List String) : Json :=
  Json.arr ((notes.map Json.str).toArray)

/-- Canonical request-binding object for the ideal-membership v0.1 wire schema.

`requestDigest` itself is intentionally absent.  `requestedClaim` is always
present on the theorem-producing exact replay path; callers that need to model a
wire request where the optional field was absent must not use this constructor.
-/
def requestBindingJson {m : Nat}
    (capability : CapabilityRef)
    (claim : Claim m)
    (notes : Option (List String) := none) : Json :=
  let base : List (String × Json) :=
    [("schemaVersion", Json.str "0.1.0"),
     ("capability", Json.str capability.id),
     ("capabilityVersion", Json.str capability.version),
     ("target", polyToJson claim.target),
     ("generators", Json.arr (claim.generators.map polyToJson)),
     ("requestedClaim", Json.str (claimClassToWire claim.claimClass))]
  let fields :=
    match notes with
    | some values => base ++ [("notes", notesJson values)]
    | none => base
  Json.mkObj fields

/-- Request digest derived from the Lean semantic values under the exact wire
binding projection. -/
def digestOfRequestFields {m : Nat}
    (capability : CapabilityRef)
    (claim : Claim m)
    (notes : Option (List String) := none) : Except String RequestDigest :=
  match JsonCanonical.digestRequestBinding (requestBindingJson capability claim notes) with
  | .ok d => pure d
  | .error e => throw e.toString

/-- Historical convenience projection for the default capability/version and no
notes.  Its semantics now match the current wire schema. -/
def digestOfClaim {m : Nat} (claim : Claim m) : Except String RequestDigest :=
  digestOfRequestFields {} claim none

end MathEvidence.Checkers.IdealMembership.Wire

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.Checkers.IdealMembership.Wire

/-- Build a checker request from exact wire-semantic fields.  The digest is
computed in Lean; callers do not supply it. -/
def Request.ofWireFields {m : Nat}
    (capability : CapabilityRef)
    (claim : Claim m)
    (notes : Option (List String) := none) : Except String (Request m) := do
  let d ← digestOfRequestFields capability claim notes
  pure {
    capability := capability
    claim := claim
    resourcePolicy := defaultResourcePolicy
    requestDigest := d
  }

/-- Panic variant for generated/offline closed terms. -/
def Request.ofWireFields! {m : Nat}
    (capability : CapabilityRef)
    (claim : Claim m)
    (notes : Option (List String) := none) : Request m :=
  match Request.ofWireFields capability claim notes with
  | .ok r => r
  | .error e => panic! s!"Request.ofWireFields! failed: {e}"

/-- Build a default-version request whose digest is the Lean wire binding. -/
def Request.ofClaim {m : Nat} (claim : Claim m) : Except String (Request m) :=
  Request.ofWireFields {} claim none

/-- Panic variant for offline fixtures. -/
def Request.ofClaim! {m : Nat} (claim : Claim m) : Request m :=
  match Request.ofClaim claim with
  | .ok r => r
  | .error e => panic! s!"Request.ofClaim! failed: {e}"

end MathEvidence.Checkers.IdealMembership
