/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Conjecture.Family
import MathEvidence.Conjecture.States

namespace MathEvidence.Conjecture

open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample

/-!
# Conjecture / falsification engine

Candidates vs certified refutations only. A returned counterexample changes
status to `falsified` only after Lean `checkBool` acceptance.
-/

/-- One conjecture episode over a finite-predicate family. -/
structure Episode where
  familyId : String
  candidatePred : Pred
  state : ConjectureState := .candidateStatement
  /-- Opaque id of a certified counterexample bundle / witness, if any. -/
  certifiedRefutationId : Option String := none
  /-- Search bounds recorded for audits (see Foundry episodes). -/
  searchBound : Nat := 0
  notes : String := ""
  deriving DecidableEq, Repr, Inhabited

/-- Campaign metadata (generators, bounds) — never a proof. -/
structure Campaign where
  family : FinitePredicateFamily
  episodes : List Episode := []
  deriving Repr, Inhabited

/-- Promote an observed pattern to a candidate statement (no proof claim). -/
def observePattern (familyId : String) (pred : Pred) : Episode where
  familyId := familyId
  candidatePred := pred
  state := .observedPattern
  notes := "Pattern only; not a theorem."

def toCandidate (e : Episode) : Episode :=
  { e with state := .candidateStatement }

/-- Apply a Lean-verified counterexample: only then mark `falsified`. -/
def certifyRefutation
    (e : Episode)
    (req : Request)
    (cert : Certificate)
    (refutationId : String) : Episode :=
  if checkBool req cert then
    { e with
      state := .falsified
      certifiedRefutationId := some refutationId
      notes := "Falsified by Lean-certified finite counterexample." }
  else
    { e with
      notes := "Witness rejected by Counterexample checker; state unchanged." }

/-- Soundness: checker acceptance ⇒ counterexample proposition. -/
theorem certifyRefutation_sound
    (_e : Episode) (req : Request) (cert : Certificate) (_id : String)
    (h : checkBool req cert = true) :
    Claim.proposition req.claim cert.witness :=
  checkBool_sound req cert h

/-- Bounded verification marker — explicitly not an unbounded theorem. -/
def markBoundedVerified (e : Episode) (bound : Nat) : Episode :=
  match e.state with
  | .falsified | .formallyProved => e
  | _ =>
    { e with
      state := .boundedVerified
      searchBound := bound
      notes :=
        "Bounded verification only; not a theorem over the unbounded family." }

/-- Append an episode; engine never consults Foundry / training data. -/
def Campaign.addEpisode (C : Campaign) (e : Episode) : Campaign :=
  { C with episodes := C.episodes ++ [e] }

/-- Survivors are candidates not yet falsified (may still be open / bounded). -/
def Campaign.survivors (C : Campaign) : List Episode :=
  C.episodes.filter fun e =>
    e.state ≠ .falsified

end MathEvidence.Conjecture
