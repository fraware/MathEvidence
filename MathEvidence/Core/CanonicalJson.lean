/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.EvidenceId

/-!
# Lean-side canonical JSON fragments

Profile: `docs/architecture/canonical-json.md` (RFC 8785 principles).
Full arbitrary-JSON canonicalization lives in adapters; Lean builds deterministic
UTF-8 for theorem-binding request digests.
-/

namespace MathEvidence.Core

/-- Hex alphabet (lowercase). -/
def hexDigits : String := "0123456789abcdef"

/-- Encode a byte as two lowercase hex digits. -/
def byteToHex (b : UInt8) : String :=
  let hi := (b >>> 4).toNat
  let lo := (b &&& 15).toNat
  String.mk [hexDigits.get! ⟨hi⟩, hexDigits.get! ⟨lo⟩]

/-- Encode a byte array as lowercase hex. -/
def bytesToHex (bs : ByteArray) : String :=
  Id.run do
    let mut s := ""
    for b in bs do
      s := s ++ byteToHex b
    pure s

namespace CanonicalJson

/-- Escape a string per a conservative RFC 8785 subset (control chars + quotes). -/
def escapeString (s : String) : String :=
  Id.run do
    let mut out := "\""
    for c in s.toList do
      out := out ++
        match c with
        | '"' => "\\\""
        | '\\' => "\\\\"
        | '\n' => "\\n"
        | '\r' => "\\r"
        | '\t' => "\\t"
        | _ =>
          if c.toNat < 0x20 then
            let h := bytesToHex (ByteArray.mk #[UInt8.ofNat c.toNat])
            "\\u00" ++ h
          else String.mk [c]
    pure (out ++ "\"")

def ofString (s : String) : String := escapeString s

def ofInt (n : Int) : String := toString n

def ofNat (n : Nat) : String := toString n

def ofBool : Bool → String
  | true => "true"
  | false => "false"

/-- Object from pre-sorted `(key, valueJson)` pairs (caller MUST sort keys). -/
def object (fields : List (String × String)) : String :=
  let body := String.intercalate "," (fields.map fun (k, v) => escapeString k ++ ":" ++ v)
  "{" ++ body ++ "}"

def array (elems : List String) : String :=
  "[" ++ String.intercalate "," elems ++ "]"

end CanonicalJson

end MathEvidence.Core
