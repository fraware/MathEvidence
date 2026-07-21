/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.AssuranceMode
import MathEvidence.Core.CapabilityId
import MathEvidence.Core.ClaimClass
import MathEvidence.Core.Digest.Types
import MathEvidence.Core.EvidenceId
import MathEvidence.Core.Provenance
import MathEvidence.Core.ResultStatus

namespace MathEvidence.Core

/-- One file entry inside an evidence bundle manifest. -/
structure BundleFileEntry where
  path : String
  digest : ContentDigest
  mediaType : String
  deriving DecidableEq, Repr, Inhabited

/-- Immutable evidence-bundle metadata (control plane; no domain math). -/
structure BundleMetadata where
  bundleVersion : String := "0.2.0"
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

/-- Allowed media types for bundle files (v0.2). -/
def allowedMediaType (m : String) : Bool :=
  m == "application/json" ||
    m == "application/cjson" ||
    m == "text/plain" ||
    m == "text/x-lean" ||
    m == "text/markdown"

/-- Parse path into segments; reject `.`, `..`, empty, absolute, and overlong paths. -/
def BundleFileEntry.pathOk (e : BundleFileEntry) : Bool :=
  let segs := e.path.splitOn "/"
  !e.path.isEmpty &&
    e.path.length ≤ 512 &&
    !(e.path.startsWith "/") &&
    !(e.path.startsWith "\\") &&
    !e.path.contains '\\' &&
    segs.all (fun s => !s.isEmpty && s != "." && s != "..") &&
    e.path.all pathCharOk &&
    allowedMediaType e.mediaType

/-- Unique roles: no duplicate paths. -/
def BundleMetadata.uniquePaths (m : BundleMetadata) : Bool :=
  let paths := m.files.map (·.path)
  paths.eraseDups.length == m.files.length

/-- Structural well-formedness for bundle metadata (schema-shaped checks). -/
def BundleMetadata.wellFormed (m : BundleMetadata) : Bool :=
  (m.bundleVersion == "0.1.0" || m.bundleVersion == "0.2.0") &&
    !m.files.isEmpty &&
    m.files.all (·.pathOk) &&
    m.uniquePaths &&
    isSha256DigestWire m.requestDigest.value &&
    m.files.all fun f => isSha256DigestWire f.digest.value

end MathEvidence.Core
