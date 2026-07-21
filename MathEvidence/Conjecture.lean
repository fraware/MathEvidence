/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Conjecture.States
import MathEvidence.Conjecture.Family
import MathEvidence.Conjecture.Engine
import MathEvidence.Conjecture.Precision
import MathEvidence.Conjecture.Domains
import MathEvidence.Conjecture.Tests

/-!
# MathEvidence.Conjecture (Product 04)

Disciplined computational discovery over formal object families.
**Primary domain scaffold:** finite simple graphs
(`Conjecture.Domains.FiniteGraph`) with Lean-certified falsification via the
Counterexample checker. Nat-bounded demos in `Conjecture.Tests` are regression
fixtures only — not the product vertical.

Candidates vs Lean-certified refutations only; bounded verification is never a
universal theorem. Training episode capture lives in Foundry and MUST NOT
influence conjecture acceptance.
-/
