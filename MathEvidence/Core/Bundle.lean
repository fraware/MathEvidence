/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.EvidenceId
import MathEvidence.Core.Provenance
import MathEvidence.Core.ResultStatus

namespace MathEvidence.Core

/-- One file entry inside an evidence bundle manifest. -/
structure BundleFileEntry where
  path : String
  digest : EvidenceId
  mediaType : String
  deriving DecidableEq, Repr, Inhabited

/-- Immutable evidence-bundle metadata (control plane; no domain math). -/
structure BundleMetadata where
  bundleVersion : String := "0.1.0"
  capability : CapabilityRef
  requestDigest : RequestDigest
  claimClass : ClaimClass
  resultStatus : ResultStatus
  assuranceMode : AssuranceMode
  files : List BundleFileEntry
  provenance : Provenance
  deriving DecidableEq, Repr, Inhabited

private def pathCharOk (c : Char) : Bool :=
  c.isAlphanum || c == '.' || c == '_' || c == '-' || c == '/'

/-- Reject empty paths, absolute paths, and `..` segments. -/
def BundleFileEntry.pathOk (e : BundleFileEntry) : Bool :=
  !e.path.isEmpty &&
    !(e.path.startsWith "/") &&
    !(e.path.startsWith "\\") &&
    (e.path.splitOn "..").length == 1 &&
    e.path.all pathCharOk

/-- Structural well-formedness for bundle metadata (schema-shaped checks). -/
def BundleMetadata.wellFormed (m : BundleMetadata) : Bool :=
  m.bundleVersion == "0.1.0" &&
    !m.files.isEmpty &&
    m.files.all (·.pathOk) &&
    isSha256DigestWire m.requestDigest.value &&
    m.files.all fun f => isSha256DigestWire f.digest.value

end MathEvidence.Core
