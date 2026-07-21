/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Lean.Data.Json
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.Digest
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.Digest.Types

/-!
# Lean-side JCS-style canonicalization of `Lean.Json`

Profile version: **mathevidence-jcs-0.2**

Recomputes the same digest profile as the Python canonical module under
`adapters/common` (see `docs/architecture/canonical-json.md`).

Numbers in Lean `Json` that are floats are rejected for digest binding (v0
forbids floats). Integer-valued `Json.num` values are emitted as canonical
decimal integers. Duplicate keys are rejected at the text-parse boundary when
using the shared Python/Lean vectors; Lean `Json` objects are already keyed
uniquely by `RBNode`.
-/

namespace MathEvidence.Core.JsonCanonical

open Lean
open MathEvidence.Core
open MathEvidence.Core.CanonicalJson

inductive Error where
  | floatForbidden (detail : String)
  | unsupported (detail : String)
  deriving Repr, Inhabited

def Error.toString : Error → String
  | .floatForbidden d => s!"float forbidden in digest: {d}"
  | .unsupported d => s!"unsupported JSON for digest: {d}"

instance : ToString Error where
  toString := Error.toString

/-- UTF-16 code units for RFC 8785 key ordering. -/
def utf16Units (s : String) : List Nat :=
  Id.run do
    let mut out : List Nat := []
    for c in s.toList do
      let cp := c.toNat
      if cp ≤ 0xFFFF then
        out := out ++ [cp]
      else
        let cp' := cp - 0x10000
        out := out ++ [0xD800 + (cp' >>> 10), 0xDC00 + (cp' &&& 0x3FF)]
    pure out

def keyLess (a b : String) : Bool :=
  decide (utf16Units a < utf16Units b)

/-- Emit canonical integer decimal.

Lean `JsonNumber` is `mantissa * 10^(-exponent)`. Nonzero exponents are
fractional and forbidden in v0 theorem-binding digests. -/
def canonicalNumber (n : JsonNumber) : Except Error String := do
  if n.exponent != 0 then
    throw (.floatForbidden s!"non-integral JsonNumber exponent={n.exponent}")
  pure (toString n.mantissa)

/-- Collect object keys (RBNode order is string-compare; we re-sort by UTF-16). -/
def objectKeys (m : RBNode String fun _ => Json) : List String :=
  m.fold (init := []) fun acc k _ => acc ++ [k]

partial def dumps : Json → Except Error String
  | .null => pure "null"
  | .bool true => pure "true"
  | .bool false => pure "false"
  | .str s => pure (escapeString s)
  | .num n => canonicalNumber n
  | .arr a => do
    let parts ← a.toList.mapM dumps
    pure ("[" ++ String.intercalate "," parts ++ "]")
  | .obj m => do
    let keys := (objectKeys m).toArray.qsort keyLess |>.toList
    let parts ← keys.mapM fun k => do
      let v ← match m.find compare k with
        | some j => pure j
        | none => throw (.unsupported s!"missing key {k}")
      let vs ← dumps v
      pure (escapeString k ++ ":" ++ vs)
    pure ("{" ++ String.intercalate "," parts ++ "}")

/-- Canonical UTF-8 JSON text for digest binding. -/
def canonicalString (j : Json) : Except Error String := dumps j

/-- SHA-256 digest of canonical JSON as a typed request digest. -/
def digestRequest (j : Json) : Except Error RequestDigest := do
  let s ← canonicalString j
  let eid := CanonicalJson.digest s
  match RequestDigest.ofWire? eid.value with
  | some d => pure d
  | none => throw (.unsupported "digest wire form invalid")

/-- SHA-256 digest of canonical JSON (`sha256:` + hex). Prefer `digestRequest` for binding. -/
def digest (j : Json) : Except Error EvidenceId := do
  let s ← canonicalString j
  pure (CanonicalJson.digest s)

/-- Digest a JSON object after removing `requestDigest` (Python binding payload). -/
def digestRequestBinding (j : Json) : Except Error RequestDigest := do
  match j with
  | .obj m =>
    let m' := RBNode.erase compare "requestDigest" m
    digestRequest (.obj m')
  | _ => throw (.unsupported "request binding requires a JSON object")

/-- Parse text and digest the request-binding payload. -/
def digestRequestBindingString (s : String) : Except String RequestDigest := do
  let j ← match Json.parse s with
    | .ok j => pure j
    | .error m => throw m
  match digestRequestBinding j with
  | .ok d => pure d
  | .error e => throw e.toString

end MathEvidence.Core.JsonCanonical
