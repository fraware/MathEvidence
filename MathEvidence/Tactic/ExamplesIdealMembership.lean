/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Algebra.Polynomial.Basic
import Mathlib.Algebra.MvPolynomial.CommRing
import Mathlib.RingTheory.Ideal.Span
import Mathlib.RingTheory.MvPolynomial.Basic
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Tactic.IdealMembership

/-!
# Ordinary Ideal.span theorems via Meta reify + witness gate + ring

Supported Meta shapes (this session):

* Univariate `Polynomial ℤ` / `ℚ`: singleton and two-generator `Ideal.span`
* Multivariate `MvPolynomial (Fin 2)` / `(Fin 3)` / `(Fin 4) ℤ` / `ℚ`:
  - monomial-generator spans
  - non-monomial principal generators via grevlex exact division when `f` is an
    exact multiple of `g` over ℤ (e.g. `X₀²−X₁ ∈ ⟨X₀²−X₁⟩`,
    `X₀³−X₀X₁ ∈ ⟨X₀²−X₁⟩`)
  - two-generator spans when pair search + exact division finds a witness
    (including when one generator is non-monomial, e.g.
    `X₀³−X₀X₁ ∈ ⟨X₀²−X₁, X₁⟩`)

Not claimed: Gröbner completeness, non-membership, `n > 4`.
-/

namespace MathEvidence.Tactic.Examples.IdealMembership

open Polynomial
open MathEvidence.Checkers.IdealMembership

set_option maxHeartbeats 800000

/-- Ordinary Mathlib theorem: `X² − 1 ∈ ⟨X − 1⟩` closed by Meta auto-bridge. -/
theorem x2_minus_1_in_span_X_minus_1 :
    ((X : ℤ[X]) ^ 2 - 1) ∈ Ideal.span {(X : ℤ[X]) - 1} := by
  mathevidence_ideal_membership

/-- Ordinary Mathlib theorem: `X² ∈ ⟨X⟩` closed by Meta auto-bridge. -/
theorem x2_in_span_X :
    ((X : ℤ[X]) ^ 2) ∈ Ideal.span {(X : ℤ[X])} := by
  mathevidence_ideal_membership

/-- Ordinary Mathlib theorem over ℚ: `X³ − X ∈ ⟨X² − 1⟩`. -/
theorem x3_minus_x_in_span_x2_minus_1 :
    ((X : ℚ[X]) ^ 3 - X) ∈ Ideal.span {((X : ℚ[X]) ^ 2 - 1)} := by
  mathevidence_ideal_membership

/-- Ordinary two-generator Meta bridge: `2X ∈ ⟨X+1, X−1⟩` with witness `(1,1)`. -/
theorem two_x_in_span_pair_meta :
    (2 * (X : ℤ[X])) ∈ Ideal.span {(X : ℤ[X]) + 1, (X : ℤ[X]) - 1} := by
  mathevidence_ideal_membership

/-- Ordinary two-generator Meta bridge: `1 ∈ ⟨X, 1+X⟩` (Bézout). -/
theorem one_in_span_x_one_plus_x_meta :
    (1 : ℤ[X]) ∈ Ideal.span {(X : ℤ[X]), (1 : ℤ[X]) + X} := by
  mathevidence_ideal_membership

/-- MvPolynomial Meta: `X₀·X₁ ∈ ⟨X₀, X₁⟩` over `MvPolynomial (Fin 2) ℚ`. -/
theorem mv_xy_in_span_x_y_meta :
    ((MvPolynomial.X (0 : Fin 2) * MvPolynomial.X (1 : Fin 2) : MvPolynomial (Fin 2) ℚ) ∈
      Ideal.span
        {MvPolynomial.X (0 : Fin 2), MvPolynomial.X (1 : Fin 2)}) := by
  mathevidence_ideal_membership

/-- MvPolynomial Meta (non-monomial target): `X₀² + X₀·X₁ ∈ ⟨X₀, X₁⟩`. -/
theorem mv_x2_plus_xy_in_span_x_y_meta :
    (((MvPolynomial.X (0 : Fin 2)) ^ 2 +
        MvPolynomial.X (0 : Fin 2) * MvPolynomial.X (1 : Fin 2) :
          MvPolynomial (Fin 2) ℚ) ∈
      Ideal.span
        {MvPolynomial.X (0 : Fin 2), MvPolynomial.X (1 : Fin 2)}) := by
  mathevidence_ideal_membership

/-- MvPolynomial Meta over ℤ: `X₀·X₁ ∈ ⟨X₀, X₁⟩`. -/
theorem mv_xy_in_span_x_y_meta_int :
    ((MvPolynomial.X (0 : Fin 2) * MvPolynomial.X (1 : Fin 2) : MvPolynomial (Fin 2) ℤ) ∈
      Ideal.span
        {MvPolynomial.X (0 : Fin 2), MvPolynomial.X (1 : Fin 2)}) := by
  mathevidence_ideal_membership

/-- Non-monomial generator (trivial): `X₀² − X₁ ∈ ⟨X₀² − X₁⟩`. -/
theorem mv_x2_minus_y_in_own_span_meta :
    (((MvPolynomial.X (0 : Fin 2)) ^ 2 - MvPolynomial.X (1 : Fin 2) :
          MvPolynomial (Fin 2) ℚ) ∈
      Ideal.span
        {((MvPolynomial.X (0 : Fin 2)) ^ 2 - MvPolynomial.X (1 : Fin 2) :
            MvPolynomial (Fin 2) ℚ)}) := by
  mathevidence_ideal_membership

/-- Non-monomial generator (non-trivial): `X₀³ − X₀·X₁ ∈ ⟨X₀² − X₁⟩`. -/
theorem mv_x3_minus_xy_in_span_x2_minus_y_meta :
    (((MvPolynomial.X (0 : Fin 2)) ^ 3 -
        MvPolynomial.X (0 : Fin 2) * MvPolynomial.X (1 : Fin 2) :
          MvPolynomial (Fin 2) ℚ) ∈
      Ideal.span
        {((MvPolynomial.X (0 : Fin 2)) ^ 2 - MvPolynomial.X (1 : Fin 2) :
            MvPolynomial (Fin 2) ℚ)}) := by
  mathevidence_ideal_membership

/-- Two-generator Meta with one non-monomial generator:
`X₀³ − X₀·X₁ ∈ ⟨X₀² − X₁, X₁⟩` (pair search recovers `(X₀, 0)`). -/
theorem mv_x3_minus_xy_in_span_x2_minus_y_and_y_meta :
    (((MvPolynomial.X (0 : Fin 2)) ^ 3 -
        MvPolynomial.X (0 : Fin 2) * MvPolynomial.X (1 : Fin 2) :
          MvPolynomial (Fin 2) ℚ) ∈
      Ideal.span
        {((MvPolynomial.X (0 : Fin 2)) ^ 2 - MvPolynomial.X (1 : Fin 2) :
            MvPolynomial (Fin 2) ℚ),
          MvPolynomial.X (1 : Fin 2)}) := by
  mathevidence_ideal_membership

/-- Fin 3 Meta: `X₀·X₁·X₂ ∈ ⟨X₀⟩` over `MvPolynomial (Fin 3) ℚ`. -/
theorem mv3_xyz_in_span_x_meta :
    ((MvPolynomial.X (0 : Fin 3) * MvPolynomial.X (1 : Fin 3) * MvPolynomial.X (2 : Fin 3) :
          MvPolynomial (Fin 3) ℚ) ∈
      Ideal.span {MvPolynomial.X (0 : Fin 3)}) := by
  mathevidence_ideal_membership

/-- Fin 4 Meta: `X₀·X₁·X₂·X₃ ∈ ⟨X₀⟩` over `MvPolynomial (Fin 4) ℚ`. -/
theorem mv4_xyzw_in_span_x_meta :
    ((MvPolynomial.X (0 : Fin 4) * MvPolynomial.X (1 : Fin 4) *
        MvPolynomial.X (2 : Fin 4) * MvPolynomial.X (3 : Fin 4) :
          MvPolynomial (Fin 4) ℚ) ∈
      Ideal.span {MvPolynomial.X (0 : Fin 4)}) := by
  mathevidence_ideal_membership

/-- Checker still owns the IR Boolean gate used by the Meta path. -/theorem ir_x2_minus_1_accepts :
    MathEvidence.Checkers.IdealMembership.example_x2_minus_1.check = true :=
  MathEvidence.Checkers.IdealMembership.example_x2_minus_1_accepts

/-- IR multivariate `xy` package still accepts. -/
theorem ir_xy_accepts :
    MathEvidence.Checkers.IdealMembership.example_xy.check = true :=
  MathEvidence.Checkers.IdealMembership.example_xy_accepts

/-- IR non-monomial principal package accepts. -/
theorem ir_mv_x3_minus_xy_accepts :
    MathEvidence.Checkers.IdealMembership.example_mv_x3_minus_xy.check = true :=
  MathEvidence.Checkers.IdealMembership.example_mv_x3_minus_xy_accepts

end MathEvidence.Tactic.Examples.IdealMembership
