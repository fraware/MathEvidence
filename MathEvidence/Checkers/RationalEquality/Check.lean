/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.Wire
import MathEvidence.IR.RationalExpr.PolyCompute
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core
open MathEvidence.IR.RationalExpr

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

/-- Lean-enforced resource policy bound into the request wire (ME-RV-022). -/
structure ResourcePolicy where
  maxVariableCount : Nat := 64
  maxExprNodes : Nat := 4096
  maxExponent : Nat := 64
  maxIntegerDigits : Nat := 4096
  maxDenominatorFactors : Nat := 1024
  maxNormalizedTermCount : Nat := 8192
  deriving DecidableEq, Repr, Inhabited

def defaultResourcePolicyLean : ResourcePolicy := {}

partial def exprNodeCount : Expr → Nat
  | .var _ | .int _ | .rat _ _ => 1
  | .neg e => 1 + exprNodeCount e
  | .add a b | .sub a b | .mul a b | .div a b => 1 + exprNodeCount a + exprNodeCount b
  | .pow b _ => 1 + exprNodeCount b

partial def maxExponentIn : Expr → Nat
  | .var _ | .int _ | .rat _ _ => 0
  | .neg e => maxExponentIn e
  | .add a b | .sub a b | .mul a b | .div a b =>
    Nat.max (maxExponentIn a) (maxExponentIn b)
  | .pow b k => Nat.max k (maxExponentIn b)

partial def maxIntegerDigitsIn : Expr → Nat
  | .var _ => 0
  | .int n => (toString n.natAbs).length
  | .rat n d => Nat.max (toString n.natAbs).length (toString d).length
  | .neg e => maxIntegerDigitsIn e
  | .add a b | .sub a b | .mul a b | .div a b =>
    Nat.max (maxIntegerDigitsIn a) (maxIntegerDigitsIn b)
  | .pow b _ => maxIntegerDigitsIn b

def resourcePolicyOk (req : Request) (policy : ResourcePolicy := defaultResourcePolicyLean) :
    Bool :=
  req.claim.varNames.length ≤ policy.maxVariableCount &&
    exprNodeCount req.claim.lhs ≤ policy.maxExprNodes &&
    exprNodeCount req.claim.rhs ≤ policy.maxExprNodes &&
    maxExponentIn req.claim.lhs ≤ policy.maxExponent &&
    maxExponentIn req.claim.rhs ≤ policy.maxExponent &&
    maxIntegerDigitsIn req.claim.lhs ≤ policy.maxIntegerDigits &&
    maxIntegerDigitsIn req.claim.rhs ≤ policy.maxIntegerDigits

def denomsCovered (e : Expr) (factors : List Expr) : Bool :=
  e.denominators.all fun d => factors.contains d

def digestOk (req : Request) (cert : Certificate) : Bool :=
  cert.requestDigest == req.requestDigest

def wellFormedOk (req : Request) (cert : Certificate) : Bool :=
  req.claim.lhs.wellFormed req.claim.varNames.length &&
    req.claim.rhs.wellFormed req.claim.varNames.length &&
    cert.denomFactors.all (·.wellFormed req.claim.varNames.length)

def polyOk (req : Request) : Bool :=
  polyEqual req.claim.lhs req.claim.rhs

def coverOk (req : Request) (cert : Certificate) : Bool :=
  denomsCovered req.claim.lhs cert.denomFactors &&
    denomsCovered req.claim.rhs cert.denomFactors

def factorsOk (_req : Request) (cert : Certificate)
    (policy : ResourcePolicy := defaultResourcePolicyLean) : Bool :=
  cert.denomFactors.length ≤ policy.maxDenominatorFactors

/-- Structural factor contract: certificate factors must reproduce original
division-denominator subexpressions exactly (initial stable fragment). -/
def structuralFactorContract : String :=
  "certificate.denomFactors must structurally equal original division denominators"

def checkBool (req : Request) (cert : Certificate) : Bool :=
  resourcePolicyOk req &&
    digestOk req cert &&
    wellFormedOk req cert &&
    factorsOk req cert &&
    polyOk req &&
    coverOk req cert

/-- Structured checker; acceptance coincides with `checkBool`. -/
def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else if !resourcePolicyOk req then
    .reject .resourceLimitExceeded "rational equality resource policy rejected"
  else
    .reject .certificateRejected "rational equality check failed"

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  constructor
  · intro h
    simp only [check] at h
    split at h
    · assumption
    · split at h <;> cases h
  · intro h
    simp only [check]
    rw [if_pos h]

end MathEvidence.Checkers.RationalEquality
