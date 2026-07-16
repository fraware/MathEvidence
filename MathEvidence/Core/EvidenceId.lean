/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Content-addressed evidence identifier: lowercase hex SHA-256 with `sha256:` prefix. -/
structure EvidenceId where
  /-- Full digest string of the form `sha256:` ++ 64 hex digits. -/
  value : String
  deriving DecidableEq, Repr, Inhabited

/-- Request-binding digest (same wire form as `EvidenceId`). -/
abbrev RequestDigest := EvidenceId

/-- True when `s` matches `sha256:[0-9a-f]{64}`. -/
def isSha256DigestWire (s : String) : Bool :=
  s.length == 71 &&
    s.startsWith "sha256:" &&
    (s.drop 7).all fun c =>
      ('0' ≤ c ∧ c ≤ '9') ∨ ('a' ≤ c ∧ c ≤ 'f')

/-- Construct an evidence id if the wire form is valid. -/
def EvidenceId.ofWire? (s : String) : Option EvidenceId :=
  if isSha256DigestWire s then some ⟨s⟩ else none

/-- Hex body without the `sha256:` prefix (64 chars when well-formed). -/
def EvidenceId.hex (e : EvidenceId) : String := e.value.drop 7

end MathEvidence.Core
