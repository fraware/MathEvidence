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
import MathEvidence.Tactic.LinearAlgebra

/-!
# Ordinary linear-algebra theorems via Meta reify + checker gate
-/

namespace MathEvidence.Tactic.Examples.LinearAlgebra

open Matrix

/-- Identity matrix over ℚ — densifies to integer literals under Meta. -/
def I2 : Matrix (Fin 2) (Fin 2) ℚ := fun i j => if i = j then 1 else 0

/-- Ordinary Mathlib theorem closed by Meta reify + IR inverse gate. -/
theorem identity_right_inverse : I2 * I2 = 1 := by
  mathevidence_linear_algebra

/-- Two-sided inverse as an ordinary ∧ goal. -/
theorem identity_two_sided_inverse : I2 * I2 = 1 ∧ I2 * I2 = 1 := by
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
