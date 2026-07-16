/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Conjecture.Engine
import MathEvidence.Checkers.Counterexample.Tests

namespace MathEvidence.Conjecture

/-!
# Precision accounting (Product 04)

Campaigns record proposed vs falsified vs surviving rates. Bounded verification
is never counted as an unbounded theorem.
-/

/-- Aggregate precision / outcome accounting for one formal family campaign. -/
structure PrecisionAccounting where
  familyId : String
  proposed : Nat := 0
  falsified : Nat := 0
  boundedVerified : Nat := 0
  formallyProved : Nat := 0
  openProblems : Nat := 0
  deriving DecidableEq, Repr, Inhabited

/-- Count episode outcomes. Precision = falsified / proposed when proposed > 0. -/
def Campaign.precisionAccounting (C : Campaign) : PrecisionAccounting :=
  let rec go (xs : List Episode) (A : PrecisionAccounting) : PrecisionAccounting :=
    match xs with
    | [] => A
    | e :: rest =>
      let A1 := { A with proposed := A.proposed + 1 }
      let A2 :=
        match e.state with
        | .falsified => { A1 with falsified := A1.falsified + 1 }
        | .boundedVerified => { A1 with boundedVerified := A1.boundedVerified + 1 }
        | .formallyProved => { A1 with formallyProved := A1.formallyProved + 1 }
        | .open_ => { A1 with openProblems := A1.openProblems + 1 }
        | _ => A1
      go rest A2
  go C.episodes { familyId := C.family.id }

/-- Mark a surviving candidate as an explicit open problem (not a theorem). -/
def markOpenProblem (e : Episode) (detail : String) : Episode :=
  match e.state with
  | .falsified | .formallyProved => e
  | _ =>
    { e with
      state := .open_
      notes := detail }

/-- Mark a reusable formally proved survivor (requires external Lean proof). -/
def markFormallyProved (e : Episode) (theoremRef : String) : Episode :=
  match e.state with
  | .falsified => e
  | _ =>
    { e with
      state := .formallyProved
      notes := s!"Reusable theorem: {theoremRef}" }

end MathEvidence.Conjecture
