/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.Digest.Types
import MathEvidence.IR.AnalyticExpr.Syntax
import MathEvidence.IR.AnalyticExpr.Domain
import MathEvidence.Checkers.AnalyticCalculus.Spec

/-!
# Analytic calculus certificates (ME-RV-051, ME-RV-053)

Inductive derivation trees mirror admissible Mathlib derivative rules.
Obligation identifiers index into the certificate obligation array; the checker
never trusts caller Booleans for domain truth.
-/

namespace MathEvidence.Checkers.AnalyticCalculus

open MathEvidence.Core
open MathEvidence.IR.AnalyticExpr

/-- Inductive derivation certificate tree (ME-RV-051). -/
inductive DerivProof where
  | variable
  | const
  | neg (p : DerivProof)
  | add (p q : DerivProof)
  | sub (p q : DerivProof)
  | mul (p q : DerivProof)
  | inv (p : DerivProof) (obligationId : Nat)
  | div (p q : DerivProof) (obligationId : Nat)
  | pow (k : Nat) (p : DerivProof)
  | sin (p : DerivProof)
  | exp (p : DerivProof)
  | log (p : DerivProof) (obligationId : Nat)
  deriving DecidableEq, Repr, Inhabited

/-- Derivative certificate: source, claimed derivative, proof tree, obligations. -/
structure DerivCertificate where
  requestDigest : RequestDigest := ⟨""⟩
  source : Expr
  derivative : Expr
  proof : DerivProof
  obligations : Array DomainObligation := #[]
  claimsCompleteness : Bool := false
  deriving Inhabited

/-- Antiderivative certificate is a derivative certificate for `F` with
`derivative = integrand`. Acceptance establishes `HasDerivAt F f(x) x` under
obligations; never completeness or uniqueness. -/
abbrev AntiderivCertificate := DerivCertificate

/-- First-order ODE candidate certificate (ME-RV-053).

Residual and IC are carried as IR + derivation tree / equality propositions —
not as trusted Booleans.
-/
structure ODECertificate where
  requestDigest : RequestDigest := ⟨""⟩
  solution : Expr
  rhs : Expr
  derivProof : DerivProof
  obligations : Array DomainObligation := #[]
  initialConditions : Array InitialCondition := #[]
  /-- Explicit domain encoded as membership obligations on the identity variable. -/
  domain : Domain := Set.univ
  claimsCompleteness : Bool := false
  deriving Inhabited

/-- Collect obligation ids referenced by a derivation tree. -/
def DerivProof.obligationIds : DerivProof → List Nat
  | .variable | .const => []
  | .neg p | .pow _ p | .sin p | .exp p => p.obligationIds
  | .add p q | .sub p q | .mul p q => p.obligationIds ++ q.obligationIds
  | .inv p id | .log p id => id :: p.obligationIds
  | .div p q id => id :: (p.obligationIds ++ q.obligationIds)

end MathEvidence.Checkers.AnalyticCalculus
