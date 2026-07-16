/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest
import MathEvidence.Core.ErrorCode
import MathEvidence.Checkers.LinearAlgebra.Certificate
import MathEvidence.Checkers.LinearAlgebra.Spec
import MathEvidence.IR.MatrixExpr.Ops

namespace MathEvidence.Checkers.LinearAlgebra

open MathEvidence.Core
open MathEvidence.IR.MatrixExpr

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def digestOk (req : Request) (cert : Certificate) : Bool :=
  digestsEqual cert.requestDigest req.requestDigest

def wellFormedOk (req : Request) (cert : Certificate) : Bool :=
  req.claim.matrix.wellFormed &&
    req.claim.matrix.withinSizeLimit &&
    (match req.claim.claimedDet with
     | none => true
     | some d => decide (d.den ≠ 0)) &&
    (match cert.inverse with
     | none => true
     | some B => B.wellFormed && B.withinSizeLimit) &&
    (match cert.vector with
     | none => true
     | some v => v.all fun e => decide (e.den ≠ 0)) &&
    req.claim.rhs.all fun e => decide (e.den ≠ 0)

def opOk (req : Request) (cert : Certificate) : Bool :=
  payloadOk req.claim.operation req.claim.matrix req.claim.rhs req.claim.claimedDet
    cert.inverse cert.vector

def checkBool (req : Request) (cert : Certificate) : Bool :=
  digestOk req cert && wellFormedOk req cert && opOk req cert

def check (req : Request) (_cand : Candidate := {}) (cert : Certificate) : CheckResult :=
  if checkBool req cert then
    .accept
  else
    .reject .certificateRejected "linear algebra check failed"

@[simp] theorem check_accept_iff (req : Request) (cand : Candidate) (cert : Certificate) :
    check req cand cert = .accept ↔ checkBool req cert = true := by
  simp [check]

end MathEvidence.Checkers.LinearAlgebra
