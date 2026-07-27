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

/-!
# Evidence Bundle metadata (v0.3 Candidate Bundle)

Wave 1 splits untrusted **Candidate Bundles** from trusted **Certification Records**.
A Candidate Bundle holds request/candidate/certificate/provenance only; its status
is always `computed`. Bundle identity is the digest of the manifest binding payload,
never the request digest alone.
-/

namespace MathEvidence.Core

/-- Artifact kind for evidence directories. -/
inductive BundleKind where
  | candidate
  | certification
  deriving DecidableEq, Repr, Inhabited

def BundleKind.toWire : BundleKind → String
  | .candidate => "candidate"
  | .certification => "certification"

def BundleKind.ofWire? : String → Option BundleKind
  | "candidate" => some .candidate
  | "certification" => some .certification
  | _ => none

/-- Named role inside a Candidate Bundle or Certification Record. -/
inductive BundleRole where
  | request
  | candidate
  | certificate
  | provenance
  | replayTarget
  | checkerEvaluation
  | theoremIdentity
  | axiomReport
  | certificationReceipt
  | signature
  | readme
  | other
  deriving DecidableEq, Repr, Inhabited

def BundleRole.toWire : BundleRole → String
  | .request => "request"
  | .candidate => "candidate"
  | .certificate => "certificate"
  | .provenance => "provenance"
  | .replayTarget => "replay-target"
  | .checkerEvaluation => "checker-evaluation"
  | .theoremIdentity => "theorem-identity"
  | .axiomReport => "axiom-report"
  | .certificationReceipt => "certification-receipt"
  | .signature => "signature"
  | .readme => "readme"
  | .other => "other"

def BundleRole.ofWire? : String → Option BundleRole
  | "request" => some .request
  | "candidate" => some .candidate
  | "certificate" => some .certificate
  | "provenance" => some .provenance
  | "replay-target" => some .replayTarget
  | "checker-evaluation" => some .checkerEvaluation
  | "theorem-identity" => some .theoremIdentity
  | "axiom-report" => some .axiomReport
  | "certification-receipt" => some .certificationReceipt
  | "signature" => some .signature
  | "readme" => some .readme
  | "other" => some .other
  | _ => none

/-- Infer role from a relative path stem (no directory). -/
def BundleRole.ofPath? (path : String) : Option BundleRole :=
  let stem :=
    if path.endsWith ".cjson" then path.dropRight 6
    else if path.endsWith ".json" then path.dropRight 5
    else if path.endsWith ".lean" then path.dropRight 5
    else if path.endsWith ".md" then path.dropRight 3
    else path
  match stem with
  | "request" => some .request
  | "candidate" => some .candidate
  | "certificate" => some .certificate
  | "provenance" => some .provenance
  | "replay-target" => some .replayTarget
  | "checker-evaluation" => some .checkerEvaluation
  | "theorem-identity" => some .theoremIdentity
  | "axiom-report" => some .axiomReport
  | "certification-receipt" => some .certificationReceipt
  | "signature" => some .signature
  | "README" | "readme" => some .readme
  | "theorem" => some .theoremIdentity
  | "checker-receipt" => some .checkerEvaluation
  | _ => none

/-- One file entry inside an evidence bundle manifest. -/
structure BundleFileEntry where
  path : String
  digest : ContentDigest
  mediaType : String
  role : BundleRole := .other
  deriving DecidableEq, Repr, Inhabited

/-- Immutable evidence-bundle metadata (control plane; no domain math).

Legacy v0.1/v0.2 layouts remain readable; new writers emit Candidate Bundle v0.3. -/
structure BundleMetadata where
  bundleVersion : String := "0.3.0"
  artifactKind : BundleKind := .candidate
  capability : CapabilityRef
  requestDigest : RequestDigest
  claimClass : ClaimClass
  resultStatus : ResultStatus
  assuranceMode : AssuranceMode
  files : List BundleFileEntry
  provenance : Provenance
  bundleDigest : Option BundleDigest := none
  deriving DecidableEq, Repr, Inhabited

private def pathCharOk (c : Char) : Bool :=
  c.isAlphanum || c == '.' || c == '_' || c == '-' || c == '/'

/-- Allowed media types for bundle files. -/
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

/-- Unique paths: no duplicate paths. -/
def BundleMetadata.uniquePaths (m : BundleMetadata) : Bool :=
  let paths := m.files.map (·.path)
  paths.eraseDups.length == m.files.length

/-- Unique roles among non-`other` / non-`readme` entries (duplicate roles reject). -/
def BundleMetadata.uniqueRoles (m : BundleMetadata) : Bool :=
  let roles := m.files.filterMap fun e =>
    match e.role with
    | .other | .readme => none
    | r => some r
  roles.eraseDups.length == roles.length

/-- Mandatory Candidate Bundle roles. -/
def BundleMetadata.hasCandidateRoles (m : BundleMetadata) : Bool :=
  let roles := m.files.map (·.role)
  roles.contains .request &&
    roles.contains .candidate &&
    roles.contains .certificate &&
    roles.contains .provenance

/-- Candidate Bundles must never advertise a verified theorem status. -/
def BundleMetadata.candidateStatusOk (m : BundleMetadata) : Bool :=
  match m.artifactKind with
  | .candidate => m.resultStatus == .computed
  | .certification => true

/-- Structural well-formedness for bundle metadata (schema-shaped checks). -/
def BundleMetadata.wellFormed (m : BundleMetadata) : Bool :=
  (m.bundleVersion == "0.1.0" || m.bundleVersion == "0.2.0" ||
      m.bundleVersion == "0.3.0") &&
    !m.files.isEmpty &&
    m.files.all (·.pathOk) &&
    m.uniquePaths &&
    m.uniqueRoles &&
    isSha256DigestWire m.requestDigest.value &&
    m.files.all fun f => isSha256DigestWire f.digest.value &&
    (m.bundleVersion != "0.3.0" ||
      (m.artifactKind == .candidate && m.hasCandidateRoles && m.candidateStatusOk))

/-- Binding payload fields that participate in `bundleDigest` (excludes digest itself). -/
structure ManifestBindingPayload where
  schemaVersion : String
  capability : CapabilityRef
  requestDigest : RequestDigest
  claimRequested : ClaimClass
  roles : List BundleFileEntry
  backendProvenanceDigest : Option ContentDigest := none
  resourcePolicyDigest : Option ContentDigest := none
  deriving DecidableEq, Repr, Inhabited

end MathEvidence.Core
