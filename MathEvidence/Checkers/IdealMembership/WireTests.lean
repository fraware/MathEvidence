/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.IdealMembership.Wire
import MathEvidence.IR.Polynomial.Syntax

/-!
# Ideal-membership wire parity tests

Known request-digest vectors are computed independently by the Python canonical
JSON implementation.  These compile-time checks make Lean/Python wire drift a
build failure.
-/

namespace MathEvidence.Checkers.IdealMembership.WireTests

open MathEvidence.Core
open MathEvidence.IR.Polynomial
open MathEvidence.Checkers.IdealMembership
open MathEvidence.Checkers.IdealMembership.Wire

private def parityClaim : Claim 2 where
  target := ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 1] }]⟩
  generators := #[
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [1, 0] }]⟩,
    ⟨[{ coefficient := 1, monomial := Monomial.ofList! 2 [0, 1] }]⟩]
  claimClass := .witness

private def parityCapability : CapabilityRef where
  id := "algebra.ideal_membership_witness"
  version := "0.1.0"

/-- Bool wrapper so `native_decide` can use `Bool.decEq`. -/
private def digestMatches (notes : Option (List String)) (expected : String) : Bool :=
  match digestOfRequestFields parityCapability parityClaim notes with
  | .ok d => d.value == expected
  | .error _ => false

theorem parity_digest_no_notes :
    digestMatches none
      "sha256:a25e551485df42cb0302c98d7eae8c590759a8d40f49257d335431f458578c3e" =
      true := by
  native_decide

theorem parity_digest_with_notes :
    digestMatches (some ["semantic note", "second note"])
      "sha256:f189ced92b8824681b10bd30368c4e86aecf947e3607fe2161b3eeea96a3954e" =
      true := by
  native_decide

end MathEvidence.Checkers.IdealMembership.WireTests
