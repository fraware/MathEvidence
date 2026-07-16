/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.IR.FinitePredicate.Eval

namespace MathEvidence.Checkers.Counterexample

open MathEvidence.Core
open MathEvidence.IR.FinitePredicate

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def digestOk (req : Request) (cert : Certificate) : Bool :=
  digestsEqual cert.requestDigest req.requestDigest

def wellFormedOk (req : Request) (cert : Certificate) : Bool :=
  decide (req.claim.varNames.length = req.claim.domains.length) &&
    req.claim.domains.all Domain.wellFormed &&
    req.claim.pred.wellFormed req.claim.domains &&
    req.claim.pred.withinSizeLimit &&
    Assignment.wellFormed req.claim.domains cert.witness

def evalOk (req : Request) (cert : Certificate) : Bool :=
  isCounterexample cert.witness req.claim.pred

def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert && wellFormedOk req cert && evalOk req cert

def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else
    .reject .certificateRejected "finite counterexample check failed"

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  simp [check]

end MathEvidence.Checkers.Counterexample
