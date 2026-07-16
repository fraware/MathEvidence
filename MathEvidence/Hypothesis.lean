/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Hypothesis.Lattice
import MathEvidence.Hypothesis.Sufficiency
import MathEvidence.Hypothesis.Deletion
import MathEvidence.Hypothesis.CounterexampleBridge
import MathEvidence.Hypothesis.Build
import MathEvidence.Hypothesis.Tests

/-!
# MathEvidence.Hypothesis (Product 03)

Condition proposal → Lean sufficiency → hypothesis deletion → certified
counterexamples for weaker variants → condition lattice artifact.

Minimality is never asserted without an explicit necessity proof covering every
recommended condition. Core/IR/Checkers remain free of adapter imports; this
package only consumes checker APIs.
-/
