/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
namespace MathEvidence.Conjecture

/-!
# Conjecture states (Product 04)

Bounded verification is never presented as a theorem over an unbounded family.
-/

inductive ConjectureState where
  | observedPattern
  | candidateStatement
  | falsified
  | boundedVerified
  | formallyProved
  | open_
  deriving DecidableEq, Repr, Inhabited

def ConjectureState.toWire : ConjectureState → String
  | .observedPattern => "observed_pattern"
  | .candidateStatement => "candidate_statement"
  | .falsified => "falsified"
  | .boundedVerified => "bounded_verified"
  | .formallyProved => "formally_proved"
  | .open_ => "open"

def ConjectureState.ofWire? : String → Option ConjectureState
  | "observed_pattern" => some .observedPattern
  | "candidate_statement" => some .candidateStatement
  | "falsified" => some .falsified
  | "bounded_verified" => some .boundedVerified
  | "formally_proved" => some .formallyProved
  | "open" => some .open_
  | _ => none

/-- True when the state must not be marketed as an unbounded theorem. -/
def ConjectureState.isTheoremGrade : ConjectureState → Bool
  | .formallyProved => true
  | _ => false

end MathEvidence.Conjecture
