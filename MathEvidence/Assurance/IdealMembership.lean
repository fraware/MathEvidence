/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Assurance.Level
import MathEvidence.Checkers.IdealMembership.Check

namespace MathEvidence.Assurance.IdealMembership

open MathEvidence.Checkers.IdealMembership

/-!
# Ideal-membership algorithm contract + verified reference

Reference algorithm: sparse witness identity `f = Σ qᵢ·gᵢ` via
`checkMembership` / `MembershipWitness.check` (normalize + compare).
-/

def contract : AlgorithmContract where
  id := "assurance.ideal_membership.reference"
  version := "0.1.0"
  assuranceLevel := .verifiedReferenceAlgorithm
  capabilityId := "algebra.groebner_membership"
  inputDomain := "Sparse integer polynomials (target, generators, multipliers)"
  outputRelation := "Witness identity f = sum_i q_i * g_i after like-term normalization"
  soundness := "checkMembership / MembershipWitness.check reconstruct the linear combination; membership_from_witness_* close Ideal.span"
  completeness := none
  soundnessDecl := "MathEvidence.Checkers.IdealMembership.membership_from_witness_univariate"
  checkerDecl := "MathEvidence.Checkers.IdealMembership.checkMembership"

def referenceCheck (w : MembershipWitness) : Bool :=
  w.check

theorem referenceCheck_eq_membershipWitness_check (w : MembershipWitness) :
    referenceCheck w = w.check := rfl

example : contract.claimsCompleteness = false := by native_decide
example : contract.assuranceLevel = .verifiedReferenceAlgorithm := by native_decide
example : contract.linksDecls = true := by native_decide

end MathEvidence.Assurance.IdealMembership
