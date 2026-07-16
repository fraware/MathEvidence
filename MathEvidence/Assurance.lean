/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Assurance.RationalEquality
import MathEvidence.Assurance.LinearAlgebra
import MathEvidence.Assurance.Counterexample
import MathEvidence.Assurance.Calculus

/-!
# MathEvidence.Assurance (Product 06 MVP)

Formal contracts + verified reference algorithms for checkers MathEvidence owns:
RationalEquality, LinearAlgebra, Counterexample, Calculus.

Does **not** audit external CAS internals or federated checkers.
-/

namespace MathEvidence.Assurance

def packageName : String := "MathEvidence.Assurance"

/-- Owned MVP contracts. -/
def ownedContracts : List AlgorithmContract :=
  [RationalEquality.contract, LinearAlgebra.contract, Counterexample.contract,
    Calculus.contract]

theorem owned_are_verified_reference :
    ownedContracts.all (fun c => c.assuranceLevel == .verifiedReferenceAlgorithm) = true := by
  native_decide

theorem owned_do_not_claim_completeness :
    ownedContracts.all (fun c => !c.claimsCompleteness) = true := by
  native_decide

end MathEvidence.Assurance
