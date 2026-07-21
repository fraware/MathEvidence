/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.IR.FinitePredicate.Syntax

namespace MathEvidence.IR.FinitePredicate

/-!
# Reification

Explicit constructors for finite predicates. Meta-level reification is owned by
`MathEvidence.Tactic`.
-/

inductive Reject where
  | unsupportedExpression (detail : String)
  | unsupportedType (detail : String)
  | illFormed (detail : String)
  | expressionTooLarge (size limit : Nat)
  | unboundedDomain (detail : String)
  deriving DecidableEq, Repr, Inhabited

structure Reified where
  varNames : List String
  domains : List Domain
  pred : Pred
  deriving DecidableEq, Repr, Inhabited

def acceptReified (r : Reified) (sizeLimit : Nat := defaultSizeLimit) :
    Except Reject Reified :=
  if r.varNames.length ≠ r.domains.length then
    .error (.illFormed "varNames/domains length mismatch")
  else if !domainsWellFormed r.domains then
    .error (.unboundedDomain "nat/int domains require explicit constant or prior-binder bounds")
  else if !r.pred.wellFormed r.domains then
    .error (.illFormed "predicate variable index out of range")
  else if r.pred.maxVarIdx > r.domains.length then
    .error (.illFormed "maxVarIdx exceeds domains")
  else if !r.pred.withinSizeLimit sizeLimit then
    .error (.expressionTooLarge r.pred.size sizeLimit)
  else
    .ok r

def reifyEq (names : List String) (doms : List Domain) (a b : Term) :
    Except Reject Reified :=
  acceptReified ⟨names, doms, .eq a b⟩

def reifyNe (names : List String) (doms : List Domain) (a b : Term) :
    Except Reject Reified :=
  acceptReified ⟨names, doms, .ne a b⟩

end MathEvidence.IR.FinitePredicate
