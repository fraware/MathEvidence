/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Shared.Basic
import MathEvidence.Checkers.RationalEquality.Spec
import MathEvidence.Checkers.RationalEquality.SpecProp
import MathEvidence.Checkers.RationalEquality.Certificate
import MathEvidence.Checkers.RationalEquality.Check
import MathEvidence.Checkers.RationalEquality.Soundness
import MathEvidence.Checkers.RationalEquality.ReplaySound
import MathEvidence.Checkers.RationalEquality.Bridge
import MathEvidence.Checkers.RationalEquality.Replay
import MathEvidence.Checkers.RationalEquality.Decode
import MathEvidence.Checkers.RationalEquality.Tests
import MathEvidence.Checkers.RationalEquality.OfflineFixtures
import MathEvidence.Checkers.LinearAlgebra.Spec
import MathEvidence.Checkers.LinearAlgebra.Certificate
import MathEvidence.Checkers.LinearAlgebra.Check
import MathEvidence.Checkers.LinearAlgebra.Soundness
import MathEvidence.Checkers.LinearAlgebra.Bridge
import MathEvidence.Checkers.LinearAlgebra.Replay
import MathEvidence.Checkers.LinearAlgebra.ReplaySound
import MathEvidence.Checkers.LinearAlgebra.OfflineFixtures
import MathEvidence.Checkers.LinearAlgebra.Tests
import MathEvidence.Checkers.Counterexample.Spec
import MathEvidence.Checkers.Counterexample.Certificate
import MathEvidence.Checkers.Counterexample.Check
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Bridge
import MathEvidence.Checkers.Counterexample.Replay
import MathEvidence.Checkers.Counterexample.ReplaySound
import MathEvidence.Checkers.Counterexample.OfflineFixtures
import MathEvidence.Checkers.Counterexample.Tests
import MathEvidence.Checkers.Calculus.Spec
import MathEvidence.Checkers.Calculus.Certificate
import MathEvidence.Checkers.Calculus.Check
import MathEvidence.Checkers.Calculus.Soundness
import MathEvidence.Checkers.Calculus.Replay
import MathEvidence.Checkers.Calculus.Tests
import MathEvidence.Checkers.IdealMembership.Spec
import MathEvidence.Checkers.IdealMembership.Certificate
import MathEvidence.Checkers.IdealMembership.Check
import MathEvidence.Checkers.IdealMembership.Soundness
import MathEvidence.Checkers.IdealMembership.ReplaySound
import MathEvidence.Checkers.IdealMembership.OfflineFixtures
import MathEvidence.Checkers.IdealMembership.Wire
import MathEvidence.Checkers.IdealMembership.WireTests
import MathEvidence.Checkers.IdealMembership.Search
import MathEvidence.IR.Polynomial.Syntax
import MathEvidence.IR.Polynomial.Normalize
import MathEvidence.IR.Polynomial.Interpret
import MathEvidence.IR.Polynomial.Soundness
import MathEvidence.Checkers.AnalyticCalculus.Spec
import MathEvidence.Checkers.AnalyticCalculus.Certificate
import MathEvidence.Checkers.AnalyticCalculus.Check
import MathEvidence.Checkers.AnalyticCalculus.Soundness
import MathEvidence.Checkers.AnalyticCalculus.Wire
import MathEvidence.Checkers.AnalyticCalculus.Tests
import MathEvidence.Checkers.AnalyticCalculus.OfflineFixtures
import MathEvidence.Checkers.AnalyticCalculus.Basic
import MathEvidence.Encoding

/-!
# MathEvidence.Checkers

Candidate and certificate structures, executable checkers, and soundness theorems.

Checkers MUST NOT invoke external processes. Encoding theorems are the visible
home for IR↔Mathlib interpretation bridges (master closure spec §5).
-/
