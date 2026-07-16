/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.Hypothesis.Deletion
import MathEvidence.Hypothesis.Lattice

namespace MathEvidence.Hypothesis

open MathEvidence.Checkers.Counterexample

/-!
# Certified counterexamples for weaker variants

Weaker theorem variants are falsified only through the existing
`logic.finite_counterexample` checker. Backend search is untrusted; Lean
acceptance is required before lattice status may move to `weakerFalsified`.
-/

/-- Result of verifying a finite counterexample against a weaker variant claim. -/
inductive WeakerRefutation where
  | certified
  | rejected (detail : String)
  deriving DecidableEq, Repr, Inhabited

/-- Verify a counterexample certificate for an explicitly stated weaker claim. -/
def verifyCounterexample (req : Request) (cert : Certificate) : WeakerRefutation :=
  if checkBool req cert then
    .certified
  else
    .rejected "finite counterexample checker rejected witness"

/-- Soundness: checker acceptance ⇒ claim proposition at the witness. -/
theorem verifyCounterexample_sound (req : Request) (cert : Certificate)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.witness :=
  checkBool_sound req cert h

/-- Record a certified CEX id on the lattice and mark related conditions. -/
def ConditionLattice.recordCertifiedCounterexample
    (L : ConditionLattice)
    (cexId : String)
    (relatedConditionIds : List String)
    (weakerVariant : List String) : ConditionLattice :=
  { L with
    certifiedCounterexamples := L.certifiedCounterexamples ++ [cexId]
    weakenedVariants := L.weakenedVariants ++ [weakerVariant]
    proposed := L.proposed.map fun n =>
      if relatedConditionIds.contains n.id then
        { n with status := .weakerFalsified }
      else n
    unresolvedNecessity :=
      L.unresolvedNecessity.filter (fun id => !relatedConditionIds.contains id)
    necessityProofs :=
      L.necessityProofs ++
        relatedConditionIds.map fun id =>
          ({ conditionId := id
             kind := .certifiedCounterexample
             detail := cexId } : NecessityProof) }

end MathEvidence.Hypothesis
