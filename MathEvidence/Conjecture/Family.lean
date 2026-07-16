/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.Conjecture

open MathEvidence.IR.FinitePredicate
open MathEvidence.Checkers.Counterexample

/-!
# Object-family contract

A domain integration defines formal objects, a bounded generator, duplicate
policy, computable invariants, and a bridge to Lean claims.
-/

/-- Duplicate / isomorphism policy for generated instances. -/
inductive DuplicatePolicy where
  | keepAll
  | rejectExactDuplicates
  deriving DecidableEq, Repr, Inhabited

/-- Finite-predicate object family (initial Product 04 domain). -/
structure FinitePredicateFamily where
  /-- Stable family id. -/
  id : String
  /-- Variable names for generated claims. -/
  varNames : List String
  /-- Explicit finite domains. -/
  domains : List Domain
  /-- Duplicate handling. -/
  duplicates : DuplicatePolicy := .rejectExactDuplicates
  /-- Soft bound on enumerated instances (documentation / Agent search). -/
  enumerateBound : Nat := 64
  deriving Repr, Inhabited

/-- Lift a predicate into a Counterexample claim (refutation strength). -/
def FinitePredicateFamily.toClaim (F : FinitePredicateFamily) (pred : Pred) : Claim where
  varNames := F.varNames
  domains := F.domains
  pred := pred
  claimClass := .refutation

/-- Request binding for a candidate conjecture (as a refutable universal). -/
def FinitePredicateFamily.toRequest (F : FinitePredicateFamily) (pred : Pred) : Request :=
  Request.ofClaim (F.toClaim pred)

end MathEvidence.Conjecture
