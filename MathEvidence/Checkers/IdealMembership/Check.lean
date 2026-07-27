/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Core.ErrorCode
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.Checkers.IdealMembership.Certificate
import MathEvidence.Checkers.IdealMembership.Spec

/-!
# Ideal-membership Boolean checker (ME-RV-032)

Trusted gate: digest + well-formedness + resource policy + linear-combination
identity after normalization. Search algorithms live in `Search.lean`.
-/

namespace MathEvidence.Checkers.IdealMembership

open MathEvidence.Core
open MathEvidence.IR.Polynomial

inductive CheckResult where
  | accept
  | reject (code : ErrorCode) (detail : String := "")
  deriving DecidableEq, Repr, Inhabited

def digestOk {m : Nat} (req : Request m) (cert : Certificate m) : Bool :=
  cert.requestDigest == req.requestDigest

def maxExpMonomial {m : Nat} (mon : Monomial m) : Nat :=
  mon.exponents.toList.foldl Nat.max 0

def maxExpPoly {m : Nat} (p : SparsePoly m) : Nat :=
  p.terms.foldl (fun acc t => Nat.max acc (maxExpMonomial t.monomial)) 0

def maxCoeffDigitsPoly {m : Nat} (p : SparsePoly m) : Nat :=
  p.terms.foldl (fun acc t => Nat.max acc (toString t.coefficient.natAbs).length) 0

def resourceOk {m : Nat} (req : Request m) (cert : Certificate m) : Bool :=
  let pol := req.resourcePolicy
  m ≤ pol.maxVariableCount &&
    req.claim.generators.size ≤ pol.maxGeneratorCount &&
    cert.multipliers.size ≤ pol.maxGeneratorCount &&
    req.claim.target.terms.length ≤ pol.maxTermCount &&
    req.claim.generators.all (fun g => g.terms.length ≤ pol.maxTermCount) &&
    cert.multipliers.all (fun q => q.terms.length ≤ pol.maxTermCount) &&
    maxExpPoly req.claim.target ≤ pol.maxExponent &&
    req.claim.generators.all (fun g => maxExpPoly g ≤ pol.maxExponent) &&
    cert.multipliers.all (fun q => maxExpPoly q ≤ pol.maxExponent) &&
    maxCoeffDigitsPoly req.claim.target ≤ pol.maxCoefficientDigits &&
    req.claim.generators.all (fun g => maxCoeffDigitsPoly g ≤ pol.maxCoefficientDigits) &&
    cert.multipliers.all (fun q => maxCoeffDigitsPoly q ≤ pol.maxCoefficientDigits)

def wellFormedOk {m : Nat} (req : Request m) (cert : Certificate m) : Bool :=
  req.claim.generators.size == cert.multipliers.size &&
    req.claim.generators.size ≥ 1

def identityOk {m : Nat} (req : Request m) (cert : Certificate m) : Bool :=
  linearCombination req.claim.generators cert.multipliers ==
    req.claim.target.normalize

/-- Boolean certificate check (authority gate). -/
def checkBool {m : Nat} (req : Request m) (cert : Certificate m) : Bool :=
  digestOk req cert &&
    wellFormedOk req cert &&
    resourceOk req cert &&
    identityOk req cert

def check {m : Nat} (req : Request m) (cert : Certificate m) : CheckResult :=
  if checkBool req cert then .accept
  else if !digestOk req cert then
    .reject .requestDigestMismatch "ideal membership digest mismatch"
  else if !wellFormedOk req cert then
    .reject .certificateRejected "ideal membership arity / well-formedness failed"
  else if !resourceOk req cert then
    .reject .resourceLimitExceeded "ideal membership resource policy rejected"
  else
    .reject .certificateRejected "ideal membership linear combination identity failed"

/-- Legacy Boolean gate over a witness package (no digest). -/
def checkMembership {m : Nat}
    (f : SparsePoly m) (gens mults : Array (SparsePoly m)) : Bool :=
  gens.size == mults.size &&
    linearCombination gens mults == f.normalize

def MembershipWitness.check {m : Nat} (w : MembershipWitness m) : Bool :=
  checkMembership w.target w.generators w.multipliers

/-- Example: `xy ∈ ⟨x, y⟩` via multipliers `(y, 0)`. -/
def example_xy : MembershipWitness 2 where
  target := ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 1] }]⟩
  generators := #[
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 0] }]⟩,
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [0, 1] }]⟩]
  multipliers := #[
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [0, 1] }]⟩,
    SparsePoly.zero 2]

theorem example_xy_accepts : example_xy.check = true := by native_decide

/-- Example: `x² - 1 ∈ ⟨x - 1⟩` with multiplier `x + 1`. -/
def example_x2_minus_1 : MembershipWitness 1 where
  target := ⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [2] },
    { coefficient := -1, monomial := Monomial.ofList! 1 [0] }]⟩
  generators := #[⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [1] },
    { coefficient := -1, monomial := Monomial.ofList! 1 [0] }]⟩]
  multipliers := #[⟨[
    { coefficient := 1, monomial := Monomial.ofList! 1 [1] },
    { coefficient := 1, monomial := Monomial.ofList! 1 [0] }]⟩]

theorem example_x2_minus_1_accepts : example_x2_minus_1.check = true := by native_decide

end MathEvidence.Checkers.IdealMembership
