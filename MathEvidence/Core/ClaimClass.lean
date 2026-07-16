/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Core

/-- Strength of mathematical claim associated with a capability request or result.

Domain packages MAY introduce refined classes. They MUST declare ordering and
promotion theorems before silent strengthening is allowed. -/
inductive ClaimClass where
  | candidate
  | witness
  | refutation
  | decomposition
  | soundResult
  | completeSolution
  | optimum
  | enclosure
  | canonicalForm
  deriving DecidableEq, Repr, Inhabited

/-- Wire / schema name for a claim class (stable snake_case identifiers). -/
def ClaimClass.toWire : ClaimClass → String
  | .candidate => "candidate"
  | .witness => "witness"
  | .refutation => "refutation"
  | .decomposition => "decomposition"
  | .soundResult => "soundResult"
  | .completeSolution => "completeSolution"
  | .optimum => "optimum"
  | .enclosure => "enclosure"
  | .canonicalForm => "canonicalForm"

/-- Parse a wire name; returns `none` for unknown tokens. -/
def ClaimClass.ofWire? : String → Option ClaimClass
  | "candidate" => some .candidate
  | "witness" => some .witness
  | "refutation" => some .refutation
  | "decomposition" => some .decomposition
  | "soundResult" => some .soundResult
  | "completeSolution" => some .completeSolution
  | "optimum" => some .optimum
  | "enclosure" => some .enclosure
  | "canonicalForm" => some .canonicalForm
  | _ => none

end MathEvidence.Core
