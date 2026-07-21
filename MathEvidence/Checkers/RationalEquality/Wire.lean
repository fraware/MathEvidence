/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.JsonCanonical
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.IR.RationalExpr.Syntax

/-!
# Wire-format request digests (Lean ↔ Python parity)

`Request.ofClaim` and live discovery MUST hash the same adapter wire object that
Python `bind_request_digest` hashes (schemaVersion, variables[{name,type}],
name-based exprs, resourcePolicy, …) — not the older capabilityId/varNames IR
fragment.
-/

namespace MathEvidence.Checkers.RationalEquality.Wire

open Lean
open MathEvidence.Core
open MathEvidence.Checkers.RationalEquality

/-- Serialize IR expr to adapter wire JSON (name-based). -/
partial def exprToWireJson (names : List String) :
    MathEvidence.IR.RationalExpr.Expr → Json
  | .var i =>
    let name := names.getD i s!"v{i}"
    Json.mkObj [("tag", Json.str "var"), ("name", Json.str name)]
  | .int n => Json.mkObj [("tag", Json.str "int"), ("value", Json.str (toString n))]
  | .rat n d =>
    Json.mkObj
      [("tag", Json.str "rat"), ("num", Json.str (toString n)),
       ("den", Json.str (toString d))]
  | .neg e => Json.mkObj [("tag", Json.str "neg"), ("arg", exprToWireJson names e)]
  | .add a b =>
    Json.mkObj
      [("tag", Json.str "add"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .sub a b =>
    Json.mkObj
      [("tag", Json.str "sub"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .mul a b =>
    Json.mkObj
      [("tag", Json.str "mul"), ("left", exprToWireJson names a),
       ("right", exprToWireJson names b)]
  | .pow b k =>
    Json.mkObj
      [("tag", Json.str "pow"), ("base", exprToWireJson names b), ("exp", Json.num k)]
  | .div n d =>
    Json.mkObj
      [("tag", Json.str "div"), ("num", exprToWireJson names n),
       ("den", exprToWireJson names d)]

def varDeclJson (name : String) : Json :=
  Json.mkObj [("name", Json.str name), ("type", Json.str "Rat")]

/-- Default resource policy matching committed evidence fixtures. -/
def defaultResourcePolicy : Json :=
  Json.mkObj
    [("maxWallTimeMs", Json.num (10000 : Nat)),
     ("maxOutputBytes", Json.num (1048576 : Nat))]

/-- Build adapter request JSON (pre-digest) from a claim. -/
def claimToRequestJson (c : Claim) : Json :=
  let assumptions :=
    (c.knownAssumptions.map fun e =>
      Json.mkObj
        [("kind", Json.str "nonzero"),
         ("expr", exprToWireJson c.varNames e)]).toArray
  Json.mkObj [
    ("schemaVersion", Json.str "0.1.0"),
    ("capability", Json.str "algebra.rational_equality"),
    ("capabilityVersion", Json.str "0.1.0"),
    ("variables", Json.arr (c.varNames.map varDeclJson).toArray),
    ("lhs", exprToWireJson c.varNames c.lhs),
    ("rhs", exprToWireJson c.varNames c.rhs),
    ("knownAssumptions", Json.arr assumptions),
    ("requestedClaim", Json.str c.claimClass.toWire),
    ("resourcePolicy", defaultResourcePolicy)
  ]

/-- Wire digest for a claim (parity with Python `bind_request_digest`). -/
def digestOfClaim (c : Claim) : Except String RequestDigest := do
  match JsonCanonical.digestRequestBinding (claimToRequestJson c) with
  | .ok d => pure d
  | .error e => throw e.toString

/-- Bind `requestDigest` onto the wire JSON object. -/
def bindClaimDigest (c : Claim) : Except String (Json × RequestDigest) := do
  let j := claimToRequestJson c
  let d ← digestOfClaim c
  let j' :=
    match j with
    | .obj m => Json.obj (m.insert compare "requestDigest" (Json.str d.value))
    | other => other
  pure (j', d)

end MathEvidence.Checkers.RationalEquality.Wire

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Checkers.RationalEquality.Wire

/-- Build a request whose digest is the Lean wire binding (Python parity). -/
def Request.ofClaim (c : Claim) : Request :=
  match digestOfClaim c with
  | .ok d => { claim := c, requestDigest := d }
  | .error _ =>
    -- Unreachable for well-formed claims; keep a deterministic fallback wire form.
    { claim := c,
      requestDigest := ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩ }

end MathEvidence.Checkers.RationalEquality
