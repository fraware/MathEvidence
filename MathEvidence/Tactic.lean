/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import MathEvidence.Tactic.Basic
import MathEvidence.Tactic.Status
import MathEvidence.Tactic.ReifyRational
import MathEvidence.Tactic.ReifyMatrix
import MathEvidence.Tactic.ReifyFinitePredicate
import MathEvidence.Tactic.ReifyPolynomial
import MathEvidence.Tactic.ReifierRegistry
import MathEvidence.Tactic.Discovery
import MathEvidence.Tactic.Replay
import MathEvidence.Tactic.Mathevidence
import MathEvidence.Tactic.LinearAlgebra
import MathEvidence.Tactic.Counterexample
import MathEvidence.Tactic.IdealMembership
import MathEvidence.Tactic.Examples
import MathEvidence.Tactic.ExamplesLinearAlgebra
import MathEvidence.Tactic.ExamplesCounterexample
import MathEvidence.Tactic.ExamplesIdealMembership

/-!
# MathEvidence.Tactic

Lean elaborator and tactic UX (`mathevidence`).

- Discovery mode: Meta-reify ℚ equality; offline fixture match by default;
  live adapter spawn when `MATHEVIDENCE_DISCOVERY=1`.
- Replay mode: load a committed bundle, run `RationalEquality.check`, close goals.
- LinearAlgebra / Counterexample / IdealMembership: Meta reify + checker gate +
  ordinary theorem examples (`Ideal.span` auto-bridge for univariate singleton /
  two-generator and `MvPolynomial (Fin 2/3)` monomial + non-monomial principal
  gens via grevlex exact division; bounded-Int CEX Meta close).
-/
