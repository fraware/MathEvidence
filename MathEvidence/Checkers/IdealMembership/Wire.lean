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
-/

namespace MathEvidence.Checkers.IdealMembership.Wire

open Lean
open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership

def termToJson {m : Nat} (t : Term m) : Json :=
  Json.mkObj
    [("coefficient", Json.str (toString t.coefficient)),
     ("exponents",
      Json.arr ((t.monomial.exponents.toList.map fun (e : Nat) => Json.num e).toArray))]

def polyToJson {m : Nat} (p : SparsePoly m) : Json :=
  Json.mkObj
    [("varCount", Json.num m),
     ("terms", Json.arr (p.terms.toArray.map termToJson))]

def defaultResourcePolicyJson : Json :=
  Json.mkObj
    [("maxWallTimeMs", Json.num (120000 : Nat)),
     ("maxOutputBytes", Json.num (16777216 : Nat))]

def claimToWireJson {m : Nat} (claim : Claim m) : Json :=
  Json.mkObj
    [("schemaVersion", Json.str "0.1.0"),
     ("capability", Json.str "algebra.ideal_membership_witness"),
     ("capabilityVersion", Json.str "0.1.0"),
     ("target", polyToJson claim.target),
     ("generators", Json.arr (claim.generators.map polyToJson)),
     ("requestedClaim", Json.str "witness"),
     ("resourcePolicy", defaultResourcePolicyJson)]

/-- Wire digest for a claim (parity with Python `bind_request_digest`). -/
def digestOfClaim {m : Nat} (claim : Claim m) : Except String RequestDigest :=
  match JsonCanonical.digestRequestBinding (claimToWireJson claim) with
  | .ok d => pure d
  | .error e => throw e.toString

end MathEvidence.Checkers.IdealMembership.Wire

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.Checkers.IdealMembership.Wire

/-- Build a request whose digest is the Lean wire binding. Never fabricates digests. -/
def Request.ofClaim {m : Nat} (claim : Claim m) : Except String (Request m) := do
  let d ← digestOfClaim claim
  pure { claim := claim, requestDigest := d }

/-- Panic variant for offline fixtures / generated modules. -/
def Request.ofClaim! {m : Nat} (claim : Claim m) : Request m :=
  match Request.ofClaim claim with
  | .ok r => r
  | .error e => panic! s!"Request.ofClaim! failed: {e}"

end MathEvidence.Checkers.IdealMembership
