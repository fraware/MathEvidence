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
import MathEvidence.Assurance.IdealMembership

/-!
# MathEvidence.Assurance (Product 06 MVP)

Formal contracts + verified reference algorithms for checkers MathEvidence owns:
RationalEquality, LinearAlgebra, Counterexample, Calculus, IdealMembership.

Does **not** audit external CAS internals or federated checkers.
-/

namespace MathEvidence.Assurance

def packageName : String := "MathEvidence.Assurance"

/-- Owned MVP contracts. -/
def ownedContracts : List AlgorithmContract :=
  [RationalEquality.contract, LinearAlgebra.contract, Counterexample.contract,
    Calculus.contract, IdealMembership.contract]

theorem owned_are_verified_reference :
    ownedContracts.all (fun c => c.assuranceLevel == .verifiedReferenceAlgorithm) = true := by
  native_decide

theorem owned_do_not_claim_completeness :
    ownedContracts.all (fun c => !c.claimsCompleteness) = true := by
  native_decide

/-- Every owned contract cites concrete Lean checker + soundness decls. -/
theorem owned_link_decls :
    ownedContracts.all (fun c => c.linksDecls) = true := by
  native_decide

/-- Ideal membership contract points at live decls after Meta/IR renames. -/
theorem ideal_contract_decls :
    IdealMembership.contract.soundnessDecl =
        "MathEvidence.Checkers.IdealMembership.membership_from_witness_univariate" ∧
      IdealMembership.contract.checkerDecl =
        "MathEvidence.Checkers.IdealMembership.checkMembership" := by
  native_decide

/-- Rational equality contract points at live checkBool / checkBool_sound. -/
theorem rational_contract_decls :
    RationalEquality.contract.soundnessDecl =
        "MathEvidence.Checkers.RationalEquality.checkBool_sound" ∧
      RationalEquality.contract.checkerDecl =
        "MathEvidence.Checkers.RationalEquality.checkBool" := by
  native_decide

/-- Linear algebra contract is fully linked (decls + referenceCheck_sound). -/
theorem linear_algebra_contract_decls :
    LinearAlgebra.contract.soundnessDecl =
        "MathEvidence.Checkers.LinearAlgebra.checkBool_sound" ∧
      LinearAlgebra.contract.checkerDecl =
        "MathEvidence.Checkers.LinearAlgebra.checkBool" ∧
      LinearAlgebra.contract.linksDecls = true := by
  native_decide

end MathEvidence.Assurance
