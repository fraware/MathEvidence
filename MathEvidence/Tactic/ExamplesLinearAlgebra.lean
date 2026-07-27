/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Checkers.LinearAlgebra.Tests
import MathEvidence.Encoding.Matrix
import MathEvidence.IR.MatrixExpr.Ops
import MathEvidence.Tactic.LinearAlgebra

/-!
# Ordinary linear-algebra theorems via Meta reify + checker gate
-/

namespace MathEvidence.Tactic.Examples.LinearAlgebra

open Matrix
open MathEvidence.IR.MatrixExpr
open MathEvidence.Encoding.Matrix

/-- Identity matrix over ℚ — densifies to integer literals under Meta. -/
def I2 : Matrix (Fin 2) (Fin 2) ℚ := fun i j => if i = j then 1 else 0

/-- Ordinary Mathlib theorem closed by Meta reify + IR inverse gate. -/
theorem identity_right_inverse : I2 * I2 = 1 := by
  mathevidence_linear_algebra

/-- Two-sided inverse as an ordinary ∧ goal. -/
theorem identity_two_sided_inverse : I2 * I2 = 1 ∧ I2 * I2 = 1 := by
  mathevidence_linear_algebra

/-- Fin-3 identity inverse — uses general-n `mulRats_ofFn_square` / Bridge inverse. -/
def I3 : Matrix (Fin 3) (Fin 3) ℚ := fun i j => if i = j then 1 else 0

theorem identity_fin3_right_inverse : I3 * I3 = 1 := by
  mathevidence_linear_algebra

/-- System matrix `[[1,1],[0,1]]`. -/
def A_sys : Matrix (Fin 2) (Fin 2) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 1
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 1

def x_sys : Fin 2 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 2

def b_sys : Fin 2 → ℚ := fun
  | ⟨0, _⟩ => 3
  | ⟨1, _⟩ => 2

/-- Singular matrix with nontrivial kernel. -/
def A_ker : Matrix (Fin 2) (Fin 2) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 2
  | ⟨1, _⟩, ⟨0, _⟩ => 2
  | ⟨1, _⟩, ⟨1, _⟩ => 4

def v_ker : Fin 2 → ℚ := fun
  | ⟨0, _⟩ => 2
  | ⟨1, _⟩ => -1

/-- Ordinary system solve closed via Meta reify + `isSystemSolution`. -/
theorem system_solve_example : A_sys.mulVec x_sys = b_sys := by
  mathevidence_linear_algebra

/-- Ordinary kernel residual closed via Meta reify + `isKernelVector` (nonzero separate). -/
theorem kernel_mulVec_zero_example : A_ker.mulVec v_ker = 0 := by
  -- Reify path: treat as system A v = 0
  mathevidence_linear_algebra

theorem kernel_vector_nonzero : v_ker ≠ 0 := by
  decide

/-- Combined kernel witness as ordinary ∧ of residual and nonzero (native after IR). -/
theorem kernel_vector_example : A_ker.mulVec v_ker = 0 ∧ v_ker ≠ 0 :=
  ⟨kernel_mulVec_zero_example, kernel_vector_nonzero⟩

/-- Ordinary determinant closed via Meta reify + `isDetIdentity`. -/
def A_det : Matrix (Fin 2) (Fin 2) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 2
  | ⟨1, _⟩, ⟨0, _⟩ => 3
  | ⟨1, _⟩, ⟨1, _⟩ => 4

theorem det_example : A_det.det = (-2 : ℚ) := by
  mathevidence_linear_algebra

/-- Fin-3 system: upper-triangular solve. -/
def A_sys3 : Matrix (Fin 3) (Fin 3) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 1
  | ⟨0, _⟩, ⟨2, _⟩ => 0
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 1
  | ⟨1, _⟩, ⟨2, _⟩ => 1
  | ⟨2, _⟩, ⟨0, _⟩ => 0
  | ⟨2, _⟩, ⟨1, _⟩ => 0
  | ⟨2, _⟩, ⟨2, _⟩ => 1

def x_sys3 : Fin 3 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 2
  | ⟨2, _⟩ => 3

def b_sys3 : Fin 3 → ℚ := fun
  | ⟨0, _⟩ => 3
  | ⟨1, _⟩ => 5
  | ⟨2, _⟩ => 3

theorem system_fin3_example : A_sys3.mulVec x_sys3 = b_sys3 := by
  mathevidence_linear_algebra

/-- Fin-3 singular matrix with nontrivial kernel. -/
def A_ker3 : Matrix (Fin 3) (Fin 3) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 2
  | ⟨0, _⟩, ⟨2, _⟩ => 3
  | ⟨1, _⟩, ⟨0, _⟩ => 2
  | ⟨1, _⟩, ⟨1, _⟩ => 4
  | ⟨1, _⟩, ⟨2, _⟩ => 6
  | ⟨2, _⟩, ⟨0, _⟩ => 1
  | ⟨2, _⟩, ⟨1, _⟩ => 2
  | ⟨2, _⟩, ⟨2, _⟩ => 3

def v_ker3 : Fin 3 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 1
  | ⟨2, _⟩ => -1

theorem kernel_fin3_mulVec_zero : A_ker3.mulVec v_ker3 = 0 := by
  mathevidence_linear_algebra

theorem kernel_fin3_nonzero : v_ker3 ≠ 0 := by
  decide

theorem kernel_fin3_example : A_ker3.mulVec v_ker3 = 0 ∧ v_ker3 ≠ 0 :=
  ⟨kernel_fin3_mulVec_zero, kernel_fin3_nonzero⟩

/-- Fin-3 determinant via `det_of_isDetIdentity_fin3`. -/
def A_det3 : Matrix (Fin 3) (Fin 3) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 2
  | ⟨0, _⟩, ⟨2, _⟩ => 3
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 1
  | ⟨1, _⟩, ⟨2, _⟩ => 4
  | ⟨2, _⟩, ⟨0, _⟩ => 5
  | ⟨2, _⟩, ⟨1, _⟩ => 6
  | ⟨2, _⟩, ⟨2, _⟩ => 0

theorem det_fin3_example : A_det3.det = (1 : ℚ) := by
  -- det = 1*(1*0-4*6) - 2*(0*0-4*5) + 3*(0*6-1*5) = -24 + 40 - 15 = 1
  mathevidence_linear_algebra

/-- Fin-4 determinant via `det_of_isDetIdentity_fin4` (Laplace + Fin-3 minors). -/
def A_det4 : Matrix (Fin 4) (Fin 4) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 0
  | ⟨0, _⟩, ⟨2, _⟩ => 0
  | ⟨0, _⟩, ⟨3, _⟩ => 0
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 2
  | ⟨1, _⟩, ⟨2, _⟩ => 0
  | ⟨1, _⟩, ⟨3, _⟩ => 0
  | ⟨2, _⟩, ⟨0, _⟩ => 0
  | ⟨2, _⟩, ⟨1, _⟩ => 0
  | ⟨2, _⟩, ⟨2, _⟩ => 3
  | ⟨2, _⟩, ⟨3, _⟩ => 0
  | ⟨3, _⟩, ⟨0, _⟩ => 0
  | ⟨3, _⟩, ⟨1, _⟩ => 0
  | ⟨3, _⟩, ⟨2, _⟩ => 0
  | ⟨3, _⟩, ⟨3, _⟩ => 4

theorem det_fin4_example : A_det4.det = (24 : ℚ) := by
  -- diagonal det = 1*2*3*4 = 24
  mathevidence_linear_algebra

/-- Fin-5 determinant via general-n `det_of_isDetIdentity` (Laplace fuel). -/
def A_det5 : Matrix (Fin 5) (Fin 5) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 0
  | ⟨0, _⟩, ⟨2, _⟩ => 0
  | ⟨0, _⟩, ⟨3, _⟩ => 0
  | ⟨0, _⟩, ⟨4, _⟩ => 0
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 2
  | ⟨1, _⟩, ⟨2, _⟩ => 0
  | ⟨1, _⟩, ⟨3, _⟩ => 0
  | ⟨1, _⟩, ⟨4, _⟩ => 0
  | ⟨2, _⟩, ⟨0, _⟩ => 0
  | ⟨2, _⟩, ⟨1, _⟩ => 0
  | ⟨2, _⟩, ⟨2, _⟩ => 3
  | ⟨2, _⟩, ⟨3, _⟩ => 0
  | ⟨2, _⟩, ⟨4, _⟩ => 0
  | ⟨3, _⟩, ⟨0, _⟩ => 0
  | ⟨3, _⟩, ⟨1, _⟩ => 0
  | ⟨3, _⟩, ⟨2, _⟩ => 0
  | ⟨3, _⟩, ⟨3, _⟩ => 4
  | ⟨3, _⟩, ⟨4, _⟩ => 0
  | ⟨4, _⟩, ⟨0, _⟩ => 0
  | ⟨4, _⟩, ⟨1, _⟩ => 0
  | ⟨4, _⟩, ⟨2, _⟩ => 0
  | ⟨4, _⟩, ⟨3, _⟩ => 0
  | ⟨4, _⟩, ⟨4, _⟩ => 5

theorem det_fin5_example : A_det5.det = (120 : ℚ) := by
  -- diagonal det = 1*2*3*4*5 = 120
  mathevidence_linear_algebra

/-- Fin-6 determinant via general-n `det_of_isDetIdentity`. -/
def A_det6 : Matrix (Fin 6) (Fin 6) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨1, _⟩, ⟨1, _⟩ => 2
  | ⟨2, _⟩, ⟨2, _⟩ => 3
  | ⟨3, _⟩, ⟨3, _⟩ => 4
  | ⟨4, _⟩, ⟨4, _⟩ => 5
  | ⟨5, _⟩, ⟨5, _⟩ => 6
  | _, _ => 0

theorem det_fin6_example : A_det6.det = (720 : ℚ) := by
  -- diagonal det = 1*2*3*4*5*6 = 720
  mathevidence_linear_algebra

/-- Adversarial: wrong claimed determinant must not close (sign / value error). -/
def A_det5_sign : Matrix (Fin 5) (Fin 5) ℚ := A_det5

/-- Dimension-mismatch style negative: non-square claim is rejected by reifier/checker path.
    Here we keep a same-size wrong scalar so the Bridge predicate fails clearly. -/
theorem det_fin5_wrong_value_rejected :
    ¬ (isDetIdentity (quoteMatrix A_det5_sign) (RatLit.ofRat (119 : ℚ)) = true) := by
  native_decide

/-- Fin-4 system via general-n `system_of_isSystemSolution`. -/
def A_sys4 : Matrix (Fin 4) (Fin 4) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 1
  | ⟨0, _⟩, ⟨2, _⟩ => 0
  | ⟨0, _⟩, ⟨3, _⟩ => 0
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 1
  | ⟨1, _⟩, ⟨2, _⟩ => 1
  | ⟨1, _⟩, ⟨3, _⟩ => 0
  | ⟨2, _⟩, ⟨0, _⟩ => 0
  | ⟨2, _⟩, ⟨1, _⟩ => 0
  | ⟨2, _⟩, ⟨2, _⟩ => 1
  | ⟨2, _⟩, ⟨3, _⟩ => 1
  | ⟨3, _⟩, ⟨0, _⟩ => 0
  | ⟨3, _⟩, ⟨1, _⟩ => 0
  | ⟨3, _⟩, ⟨2, _⟩ => 0
  | ⟨3, _⟩, ⟨3, _⟩ => 1

def x_sys4 : Fin 4 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 2
  | ⟨2, _⟩ => 3
  | ⟨3, _⟩ => 4

def b_sys4 : Fin 4 → ℚ := fun
  | ⟨0, _⟩ => 3
  | ⟨1, _⟩ => 5
  | ⟨2, _⟩ => 7
  | ⟨3, _⟩ => 4

theorem system_fin4_example : A_sys4.mulVec x_sys4 = b_sys4 := by
  mathevidence_linear_algebra

/-- Rectangular 2×3 system (general `m×n` Bridge transport). -/
def A_rect : Matrix (Fin 2) (Fin 3) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 0
  | ⟨0, _⟩, ⟨2, _⟩ => 1
  | ⟨1, _⟩, ⟨0, _⟩ => 0
  | ⟨1, _⟩, ⟨1, _⟩ => 1
  | ⟨1, _⟩, ⟨2, _⟩ => 1

def x_rect : Fin 3 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 2
  | ⟨2, _⟩ => 3

def b_rect : Fin 2 → ℚ := fun
  | ⟨0, _⟩ => 4
  | ⟨1, _⟩ => 5

theorem system_rectangular_example : A_rect.mulVec x_rect = b_rect := by
  mathevidence_linear_algebra

/-- Fin-4 singular kernel via general `kernel_of_isKernelVector`. -/
def A_ker4 : Matrix (Fin 4) (Fin 4) ℚ := fun
  | ⟨0, _⟩, ⟨0, _⟩ => 1
  | ⟨0, _⟩, ⟨1, _⟩ => 2
  | ⟨0, _⟩, ⟨2, _⟩ => 3
  | ⟨0, _⟩, ⟨3, _⟩ => 4
  | ⟨1, _⟩, ⟨0, _⟩ => 2
  | ⟨1, _⟩, ⟨1, _⟩ => 4
  | ⟨1, _⟩, ⟨2, _⟩ => 6
  | ⟨1, _⟩, ⟨3, _⟩ => 8
  | ⟨2, _⟩, ⟨0, _⟩ => 0
  | ⟨2, _⟩, ⟨1, _⟩ => 0
  | ⟨2, _⟩, ⟨2, _⟩ => 0
  | ⟨2, _⟩, ⟨3, _⟩ => 0
  | ⟨3, _⟩, ⟨0, _⟩ => 0
  | ⟨3, _⟩, ⟨1, _⟩ => 0
  | ⟨3, _⟩, ⟨2, _⟩ => 0
  | ⟨3, _⟩, ⟨3, _⟩ => 0

def v_ker4 : Fin 4 → ℚ := fun
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 1
  | ⟨2, _⟩ => -1
  | ⟨3, _⟩ => 0

theorem kernel_fin4_mulVec_zero : A_ker4.mulVec v_ker4 = 0 := by
  mathevidence_linear_algebra

theorem kernel_fin4_nonzero : v_ker4 ≠ 0 := by
  decide

theorem kernel_fin4_example : A_ker4.mulVec v_ker4 = 0 ∧ v_ker4 ≠ 0 :=
  ⟨kernel_fin4_mulVec_zero, kernel_fin4_nonzero⟩

/-- Checker soundness still owns the IR-level proposition for offline fixtures. -/
theorem offline_inverse_proposition :
    MathEvidence.Checkers.LinearAlgebra.Claim.proposition
      MathEvidence.Checkers.LinearAlgebra.Tests.claim_inv
      MathEvidence.Checkers.LinearAlgebra.Tests.cert_inv.inverse
      MathEvidence.Checkers.LinearAlgebra.Tests.cert_inv.vector :=
  MathEvidence.Checkers.LinearAlgebra.Tests.sound_inv

theorem offline_kernel_proposition :
    MathEvidence.Checkers.LinearAlgebra.Claim.proposition
      MathEvidence.Checkers.LinearAlgebra.Tests.claim_ker
      MathEvidence.Checkers.LinearAlgebra.Tests.cert_ker.inverse
      MathEvidence.Checkers.LinearAlgebra.Tests.cert_ker.vector :=
  MathEvidence.Checkers.LinearAlgebra.Tests.sound_ker

/-- Offline system fixture evaluates `A * x = b` (ordinary semantic witness). -/
theorem offline_system_eval :
    ∃ ax bv,
      MathEvidence.Checkers.LinearAlgebra.Tests.A_sys.mulVecEval? MathEvidence.Checkers.LinearAlgebra.Tests.x_sys = some ax ∧
        MathEvidence.Checkers.LinearAlgebra.Tests.b_sys.eval? = some bv ∧ ax = bv :=
  MathEvidence.Checkers.LinearAlgebra.Tests.ordinary_system_eval

end MathEvidence.Tactic.Examples.LinearAlgebra
