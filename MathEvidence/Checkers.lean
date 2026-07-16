/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Shared.Basic
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Checkers.RationalEquality.Decode
import MathEvidence.Checkers.RationalEquality.Tests
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.LinearAlgebra.Spec
import MathEvidence.Checkers.LinearAlgebra.Certificate
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Checkers.LinearAlgebra.Replay
import MathEvidence.Checkers.LinearAlgebra.Tests
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Replay
import MathEvidence.Checkers.Counterexample.Tests
import MathEvidence.Checkers.Calculus.Spec
import MathEvidence.Checkers.Calculus.Certificate
import MathEvidence.Checkers.Calculus.Check
import MathEvidence.Checkers.Calculus.Soundness
import MathEvidence.Checkers.Calculus.Replay
import MathEvidence.Checkers.Calculus.Tests

/-!
# MathEvidence.Checkers

Candidate and certificate structures, executable checkers, and soundness theorems.

Checkers MUST NOT invoke external processes.
-/
