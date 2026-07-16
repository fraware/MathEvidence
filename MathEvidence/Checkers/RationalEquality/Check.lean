/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.IR.RationalExpr.Poly
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.RationalEquality

open MathEvidence.Core
open MathEvidence.IR.RationalExpr

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def denomsCovered (e : Expr) (factors : List Expr) : Bool :=
  e.denominators.all fun d => factors.contains d

def digestOk (req : Request) (cert : Certificate) : Bool :=
  digestsEqual cert.requestDigest req.requestDigest

def wellFormedOk (req : Request) (cert : Certificate) : Bool :=
  req.claim.lhs.wellFormed req.claim.varNames.length &&
    req.claim.rhs.wellFormed req.claim.varNames.length &&
    cert.denomFactors.all (·.wellFormed req.claim.varNames.length)

def polyOk (req : Request) : Bool :=
  polyEqual req.claim.lhs req.claim.rhs

def coverOk (req : Request) (cert : Certificate) : Bool :=
  denomsCovered req.claim.lhs cert.denomFactors &&
    denomsCovered req.claim.rhs cert.denomFactors

def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert && wellFormedOk req cert && polyOk req && coverOk req cert

/-- Structured checker; acceptance coincides with `checkBool`. -/
def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else
    .reject .certificateRejected "rational equality check failed"

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  simp [check]

end MathEvidence.Checkers.RationalEquality
