/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Assurance

/-!
# Algorithm Assurance levels (Product 06)

Ordered from most practical to strongest. Higher levels are never implied by lower
ones. Proprietary CAS internals are not claimed verified.
-/

inductive AssuranceLevel where
  | outputVerification
  | checkerSoundness
  | verifiedReferenceAlgorithm
  | restrictedCompleteness
  | openImplementationCorrespondence
  | proprietaryDifferential
  deriving DecidableEq, Repr, Inhabited

def AssuranceLevel.toWire : AssuranceLevel → String
  | .outputVerification => "output_verification"
  | .checkerSoundness => "checker_soundness"
  | .verifiedReferenceAlgorithm => "verified_reference_algorithm"
  | .restrictedCompleteness => "restricted_completeness"
  | .openImplementationCorrespondence => "open_implementation_correspondence"
  | .proprietaryDifferential => "proprietary_differential"

def AssuranceLevel.ofWire? : String → Option AssuranceLevel
  | "output_verification" => some .outputVerification
  | "checker_soundness" => some .checkerSoundness
  | "verified_reference_algorithm" => some .verifiedReferenceAlgorithm
  | "restricted_completeness" => some .restrictedCompleteness
  | "open_implementation_correspondence" => some .openImplementationCorrespondence
  | "proprietary_differential" => some .proprietaryDifferential
  | _ => none

/-- Algorithm contract metadata (Lean-side; JSON mirror in schemas/). -/
structure AlgorithmContract where
  id : String
  version : String
  assuranceLevel : AssuranceLevel
  capabilityId : String
  inputDomain : String
  outputRelation : String
  soundness : String
  completeness : Option String := none
  /-- Lean declaration name that owns the soundness theorem (string form). -/
  soundnessDecl : String := ""
  /-- Lean declaration name for the executable checker entry. -/
  checkerDecl : String := ""
  deriving Repr, Inhabited

/-- Completeness is never silently claimed. -/
def AlgorithmContract.claimsCompleteness (c : AlgorithmContract) : Bool :=
  c.completeness.isSome

/-- True when the contract links concrete Lean decls (not free-text only). -/
def AlgorithmContract.linksDecls (c : AlgorithmContract) : Bool :=
  !c.soundnessDecl.isEmpty && !c.checkerDecl.isEmpty

end MathEvidence.Assurance
