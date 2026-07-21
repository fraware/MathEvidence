/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.CanonicalJson
import MathEvidence.Core.EvidenceId

/-!
# Typed digests (ME-004)

Distinct types for request binding, file content, bundle identity, checker
receipts, and theorem digests. There are **no** cross-type coercions.
-/

namespace MathEvidence.Core

/-- Wire form shared by all digests: `sha256:` ++ 64 lowercase hex digits. -/
private def parseWire (s : String) : Option String :=
  if isSha256DigestWire s then some s else none

/-- Request-binding digest (canonical request payload). -/
structure RequestDigest where
  value : String
  deriving DecidableEq, Repr, Inhabited

/-- Content digest of exact file bytes. -/
structure ContentDigest where
  value : String
  deriving DecidableEq, Repr, Inhabited

/-- Bundle-level digest over the canonical manifest. -/
structure BundleDigest where
  value : String
  deriving DecidableEq, Repr, Inhabited

/-- Checker receipt digest. -/
structure ReceiptDigest where
  value : String
  deriving DecidableEq, Repr, Inhabited

/-- Theorem / proposition digest. -/
structure TheoremDigest where
  value : String
  deriving DecidableEq, Repr, Inhabited

def RequestDigest.ofWire? (s : String) : Option RequestDigest :=
  (parseWire s).map (⟨·⟩)

def ContentDigest.ofWire? (s : String) : Option ContentDigest :=
  (parseWire s).map (⟨·⟩)

def BundleDigest.ofWire? (s : String) : Option BundleDigest :=
  (parseWire s).map (⟨·⟩)

def ReceiptDigest.ofWire? (s : String) : Option ReceiptDigest :=
  (parseWire s).map (⟨·⟩)

def TheoremDigest.ofWire? (s : String) : Option TheoremDigest :=
  (parseWire s).map (⟨·⟩)

/-- Validated constructor from SHA-256 32-byte digest. -/
def RequestDigest.ofBytes? (digest32 : ByteArray) : Option RequestDigest :=
  if digest32.size != 32 then none
  else RequestDigest.ofWire? ("sha256:" ++ bytesToHex digest32)

def ContentDigest.ofBytes? (digest32 : ByteArray) : Option ContentDigest :=
  if digest32.size != 32 then none
  else ContentDigest.ofWire? ("sha256:" ++ bytesToHex digest32)

def BundleDigest.ofBytes? (digest32 : ByteArray) : Option BundleDigest :=
  if digest32.size != 32 then none
  else BundleDigest.ofWire? ("sha256:" ++ bytesToHex digest32)

/-- Opaque artifact identity only — not for request binding or file content. -/
def EvidenceId.toRequestDigest (e : EvidenceId) : Option RequestDigest :=
  RequestDigest.ofWire? e.value

def EvidenceId.toContentDigest (e : EvidenceId) : Option ContentDigest :=
  ContentDigest.ofWire? e.value

/-- Explicit conversion helpers (no `Coe` instances). -/
def RequestDigest.toEvidenceId (d : RequestDigest) : EvidenceId := ⟨d.value⟩
def ContentDigest.toEvidenceId (d : ContentDigest) : EvidenceId := ⟨d.value⟩

end MathEvidence.Core
