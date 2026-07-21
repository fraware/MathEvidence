/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.Calculus.Certificate
import MathEvidence.Checkers.Calculus.Spec
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.CalculusExpr.Syntax

namespace MathEvidence.Checkers.Calculus

open MathEvidence.Core
open MathEvidence.IR.CalculusExpr
open MathEvidence.IR.RationalExpr (Expr)

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def digestOk (req : Request) (cert : Certificate) : Bool :=
  cert.requestDigest == req.requestDigest &&
    decide (cert.operation = req.claim.operation)

/-- Every expression well-formed relative to `varNames`. -/
def wellFormedOk (req : Request) : Bool :=
  let n := req.claim.varNames.length
  req.claim.expr.wellFormed n &&
    req.claim.candidate.wellFormed n &&
    req.claim.domainConditions.all (·.wellFormed n) &&
    req.claim.initialConditions.all (fun ic =>
      ic.point.wellFormed n && ic.value.wellFormed n) &&
    (match req.claim.odeRhs with
     | none => true
     | some e => e.wellFormed n) &&
    (match req.claim.recurrenceRhs with
     | none => true
     | some e => e.wellFormed n) &&
    decide (req.claim.independentVar < n) &&
    exprsWithinLimit
      ([req.claim.expr, req.claim.candidate] ++
        req.claim.domainConditions ++
        req.claim.initialConditions.map (·.point) ++
        req.claim.initialConditions.map (·.value) ++
        req.claim.odeRhs.toList ++
        req.claim.recurrenceRhs.toList)

/-- Singularity / branch conditions must cover every division denominator involved. -/
def domainCoverOk (req : Request) (cert : Certificate) : Bool :=
  let conds := req.claim.domainConditions
  decide (conds = cert.domainConditions) &&
    densCovered req.claim.expr conds &&
    densCovered req.claim.candidate conds &&
    (match req.claim.odeRhs with
     | none => true
     | some e => densCovered e conds) &&
    (match req.claim.recurrenceRhs with
     | none => true
     | some e => densCovered e conds) &&
    req.claim.initialConditions.all (fun ic =>
      densCovered ic.point conds && densCovered ic.value conds)

def opOk (req : Request) : Bool :=
  req.claim.opHolds

theorem opOk_eq_opHolds (req : Request) : opOk req = req.claim.opHolds := rfl

def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert && wellFormedOk req && domainCoverOk req cert && opOk req

def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else
    .reject .certificateRejected "symbolic calculus check failed"

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  simp [check]

end MathEvidence.Checkers.Calculus
