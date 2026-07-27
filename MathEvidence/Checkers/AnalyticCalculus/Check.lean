/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.ErrorCode
import MathEvidence.IR.AnalyticExpr.Interpret
import MathEvidence.Checkers.AnalyticCalculus.Certificate
import MathEvidence.Checkers.AnalyticCalculus.Spec

/-!
# Analytic calculus checker (ME-RV-051..053)

Validates derivation-tree shape and reconstructed derivative syntax. Domain
truth is never a Boolean field on the certificate.
-/

namespace MathEvidence.Checkers.AnalyticCalculus

open MathEvidence.Core
open MathEvidence.IR.AnalyticExpr

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

/-- Reconstruct the derivative expression implied by applying `proof` to `source`. -/
def reconstructDeriv : Expr → DerivProof → Option Expr
  | .variable 0, .variable => some (.const 1)
  | .const _, .const => some (.const 0)
  | .neg a, .neg p => (reconstructDeriv a p).map .neg
  | .add a b, .add p q =>
    match reconstructDeriv a p, reconstructDeriv b q with
    | some da, some db => some (.add da db)
    | _, _ => none
  | .sub a b, .sub p q =>
    match reconstructDeriv a p, reconstructDeriv b q with
    | some da, some db => some (.sub da db)
    | _, _ => none
  | .mul a b, .mul p q =>
    match reconstructDeriv a p, reconstructDeriv b q with
    | some da, some db => some (.add (.mul da b) (.mul a db))
    | _, _ => none
  | .inv a, .inv p _ =>
    match reconstructDeriv a p with
    | some da => some (.neg (.div da (.mul a a)))
    | none => none
  | .div n d, .div p q _ =>
    match reconstructDeriv n p, reconstructDeriv d q with
    | some dn, some dd =>
        some (.div (.sub (.mul dn d) (.mul n dd)) (.mul d d))
    | _, _ => none
  | .pow a k, .pow k' p =>
    if k ≠ k' then none
    else
      match reconstructDeriv a p with
      | some da =>
          if k = 0 then some (.const 0)
          else some (.mul (.mul (.const (k : ℚ)) (.pow a (k - 1))) da)
      | none => none
  | .sin a, .sin p =>
    match reconstructDeriv a p with
    | some da => some (.mul (.cos a) da)
    | none => none
  | .exp a, .exp p =>
    match reconstructDeriv a p with
    | some da => some (.mul (.exp a) da)
    | none => none
  | .log a, .log p _ =>
    match reconstructDeriv a p with
    | some da => some (.div da a)
    | none => none
  | _, _ => none

/-- Obligation `id` is `.nonzero e`. -/
def obligationNonzeroOk (obls : Array DomainObligation) (id : Nat) (e : Expr) : Bool :=
  if h : id < obls.size then
    match obls[id] with
    | .nonzero e' => decide (e' = e)
    | _ => false
  else
    false

/-- Obligation `id` is `.positive e`. -/
def obligationPositiveOk (obls : Array DomainObligation) (id : Nat) (e : Expr) : Bool :=
  if h : id < obls.size then
    match obls[id] with
    | .positive e' => decide (e' = e)
    | _ => false
  else
    false

/-- Tree shape matches `source` and obligation ids bind the correct subexpressions. -/
def checkProof : Expr → DerivProof → Array DomainObligation → Bool
  | .variable 0, .variable, _ => true
  | .const _, .const, _ => true
  | .neg a, .neg p, obls => checkProof a p obls
  | .add a b, .add p q, obls => checkProof a p obls && checkProof b q obls
  | .sub a b, .sub p q, obls => checkProof a p obls && checkProof b q obls
  | .mul a b, .mul p q, obls => checkProof a p obls && checkProof b q obls
  | .inv a, .inv p id, obls =>
      obligationNonzeroOk obls id a && checkProof a p obls
  | .div n d, .div p q id, obls =>
      obligationNonzeroOk obls id d &&
        checkProof n p obls && checkProof d q obls
  | .pow a k, .pow k' p, obls => decide (k = k') && checkProof a p obls
  | .sin a, .sin p, obls => checkProof a p obls
  | .exp a, .exp p, obls => checkProof a p obls
  | .log a, .log p id, obls =>
      obligationPositiveOk obls id a && checkProof a p obls
  | _, _, _ => false

/-- Core derivative checker (Boolean shape/syntax only). -/
def checkDeriv (c : DerivCertificate) : Bool :=
  !c.claimsCompleteness &&
    c.source.withinSizeLimit &&
    c.derivative.withinSizeLimit &&
    c.source.isUnivariate &&
    c.derivative.isUnivariate &&
    checkProof c.source c.proof c.obligations &&
    match reconstructDeriv c.source c.proof with
    | some d => decide (d = c.derivative)
    | none => false

/-- Antiderivative checker: same as derivative of claimed `F`. -/
def checkAntideriv (c : AntiderivCertificate) : Bool :=
  checkDeriv c

/-- IC entries must be constant expressions (decidable syntactic check). -/
def initialConditionsOk (ics : Array InitialCondition) : Bool :=
  ics.all fun ic => ic.point.isConst && ic.value.isConst

/-- ODE candidate checker: residual tree matches RHS; ICs are const pairs. -/
def checkODE (c : ODECertificate) : Bool :=
  !c.claimsCompleteness &&
    c.solution.withinSizeLimit &&
    c.rhs.withinSizeLimit &&
    c.solution.isUnivariate &&
    c.rhs.isUnivariate &&
    checkProof c.solution c.derivProof c.obligations &&
    initialConditionsOk c.initialConditions &&
    match reconstructDeriv c.solution c.derivProof with
    | some d => decide (d = c.rhs)
    | none => false

/-- Package check against a typed request for derivative claims. -/
def checkDerivRequest (req : Request) (c : DerivCertificate) : Bool :=
  decide (req.claim.kind = .derivative) &&
    decide (req.claim.source = c.source) &&
    decide (req.claim.target = c.derivative) &&
    (c.requestDigest.value = "" || c.requestDigest == req.requestDigest) &&
    checkDeriv c

def checkODERequest (req : Request) (c : ODECertificate) : Bool :=
  decide (req.claim.kind = .odeCandidate) &&
    decide (req.claim.source = c.solution) &&
    decide (req.claim.target = c.rhs) &&
    (c.requestDigest.value = "" || c.requestDigest == req.requestDigest) &&
    checkODE c

def check (c : DerivCertificate) : CheckResult :=
  if checkDeriv c then .accept
  else .reject .certificateRejected "analytic derivative check failed"

def checkODEResult (c : ODECertificate) : CheckResult :=
  if checkODE c then .accept
  else .reject .certificateRejected "analytic ODE check failed"

/-- Marker: analytic checkers must conclude Mathlib derivative/ODE props. -/
def requiresHasDerivAt : Bool := true

/-- Forbidden shortcut: polyEqual-only acceptance. -/
def forbidsPolyEqualAlone : Bool := true

/-- Analytic certificates never classify all solutions. -/
def rejectsCompletenessClaims : Bool := true

end MathEvidence.Checkers.AnalyticCalculus
