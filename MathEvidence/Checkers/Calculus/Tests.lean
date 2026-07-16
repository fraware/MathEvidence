/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Calculus.Check
import MathEvidence.Checkers.Calculus.Replay
import MathEvidence.Checkers.Calculus.Soundness
import MathEvidence.IR.CalculusExpr.Ops
import MathEvidence.IR.RationalExpr.Syntax

namespace MathEvidence.Checkers.Calculus.Tests

open MathEvidence.IR.CalculusExpr
open MathEvidence.IR.RationalExpr
open MathEvidence.Checkers.Calculus

/-!
Hand-written offline fixtures for Milestone 5 calculus operations.
-/

/-- `d/dx (x^2) = 2x`. -/
def claim_deriv_x2 : Claim where
  operation := .derivativeCandidate
  varNames := ["x"]
  independentVar := 0
  expr := .pow (.var 0) 2
  candidate := .mul (.int 2) (.var 0)
  domainConditions := []
  claimClass := .candidate

def req_deriv_x2 : Request := Request.ofClaim claim_deriv_x2

def cert_deriv_x2 : Certificate where
  requestDigest := req_deriv_x2.requestDigest
  operation := .derivativeCandidate
  domainConditions := []

/-- Antiderivative: `F = x^2`, `f = 2x` so `F' = f`. -/
def claim_antideriv : Claim where
  operation := .antiderivativeCandidate
  varNames := ["x"]
  independentVar := 0
  expr := .mul (.int 2) (.var 0)
  candidate := .pow (.var 0) 2
  domainConditions := []
  claimClass := .candidate

def req_antideriv : Request := Request.ofClaim claim_antideriv

def cert_antideriv : Certificate where
  requestDigest := req_antideriv.requestDigest
  operation := .antiderivativeCandidate
  domainConditions := []

/-- Closed form `u(n) = n`; recurrence `u(n+1) = u + 1`. -/
def claim_recurrence : Claim where
  operation := .recurrenceIdentity
  varNames := ["n", "u"]
  independentVar := 0
  dependentVar := 1
  expr := .var 0
  candidate := .int 0
  recurrenceRhs := some (.add (.var 1) (.int 1))
  domainConditions := []
  claimClass := .candidate

def req_recurrence : Request := Request.ofClaim claim_recurrence

def cert_recurrence : Certificate where
  requestDigest := req_recurrence.requestDigest
  operation := .recurrenceIdentity
  domainConditions := []

/-- ODE `y' = 1` with solution `y = x`, IC `y(0) = 0`. -/
def claim_ode : Claim where
  operation := .odeCandidate
  varNames := ["x", "y"]
  independentVar := 0
  dependentVar := 1
  expr := .var 0
  candidate := .int 0
  odeRhs := some (.int 1)
  initialConditions := [{ point := .int 0, value := .int 0 }]
  domainConditions := []
  claimClass := .candidate

def req_ode : Request := Request.ofClaim claim_ode

def cert_ode : Certificate where
  requestDigest := req_ode.requestDigest
  operation := .odeCandidate
  domainConditions := []

/-- Wrong derivative must be rejected. -/
def claim_bad_deriv : Claim where
  operation := .derivativeCandidate
  varNames := ["x"]
  independentVar := 0
  expr := .pow (.var 0) 2
  candidate := .int 0
  domainConditions := []

def req_bad_deriv : Request := Request.ofClaim claim_bad_deriv

def cert_bad_deriv : Certificate where
  requestDigest := req_bad_deriv.requestDigest
  operation := .derivativeCandidate
  domainConditions := []

/-- Digest mismatch rejected. -/
def cert_bad_digest : Certificate where
  requestDigest := ⟨"sha256:0000000000000000000000000000000000000000000000000000000000000000"⟩
  operation := .derivativeCandidate
  domainConditions := []

/-- Rational with explicit pole conditions: `d/dx (1/x)`.

Candidate matches the formal quotient-rule expansion (poly-equal to `-1/x^2`). -/
def claim_deriv_inv : Claim where
  operation := .derivativeCandidate
  varNames := ["x"]
  independentVar := 0
  expr := .div (.int 1) (.var 0)
  candidate :=
    .div
      (.sub (.mul (.int 0) (.var 0)) (.mul (.int 1) (.int 1)))
      (.pow (.var 0) 2)
  domainConditions := [.var 0, .pow (.var 0) 2]
  claimClass := .candidate

def req_deriv_inv : Request := Request.ofClaim claim_deriv_inv

def cert_deriv_inv : Certificate where
  requestDigest := req_deriv_inv.requestDigest
  operation := .derivativeCandidate
  domainConditions := [.var 0, .pow (.var 0) 2]

/-- Missing singularity condition rejected. -/
def claim_deriv_inv_missing : Claim where
  operation := .derivativeCandidate
  varNames := ["x"]
  independentVar := 0
  expr := .div (.int 1) (.var 0)
  candidate := .neg (.div (.int 1) (.pow (.var 0) 2))
  domainConditions := []
  claimClass := .candidate

def req_deriv_inv_missing : Request := Request.ofClaim claim_deriv_inv_missing

def cert_deriv_inv_missing : Certificate where
  requestDigest := req_deriv_inv_missing.requestDigest
  operation := .derivativeCandidate
  domainConditions := []

theorem replay_deriv_x2 :
    checkBool req_deriv_x2 cert_deriv_x2 = true := by native_decide

theorem replay_antideriv :
    checkBool req_antideriv cert_antideriv = true := by native_decide

theorem replay_recurrence :
    checkBool req_recurrence cert_recurrence = true := by native_decide

theorem replay_ode :
    checkBool req_ode cert_ode = true := by native_decide

theorem replay_deriv_inv :
    checkBool req_deriv_inv cert_deriv_inv = true := by native_decide

theorem reject_bad_deriv :
    checkBool req_bad_deriv cert_bad_deriv = false := by native_decide

theorem reject_bad_digest :
    checkBool req_deriv_x2 cert_bad_digest = false := by native_decide

theorem reject_missing_domain :
    checkBool req_deriv_inv_missing cert_deriv_inv_missing = false := by native_decide

theorem replay_report_deriv :
    (replay { request := req_deriv_x2, certificate := cert_deriv_x2 }).accepted = true := by
  native_decide

theorem sound_deriv_x2 :
    Claim.proposition claim_deriv_x2 :=
  checkBool_sound req_deriv_x2 cert_deriv_x2 replay_deriv_x2

theorem sound_ode :
    Claim.proposition claim_ode :=
  checkBool_sound req_ode cert_ode replay_ode

end MathEvidence.Checkers.Calculus.Tests
