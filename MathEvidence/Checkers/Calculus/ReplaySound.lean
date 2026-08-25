/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Calculus.Soundness
import MathEvidence.Checkers.Calculus.Spec

/-!
# Formal rational calculus kernel-replay soundness (SPEC-07 Track A)

`replaySound` is the theorem-producing authority for formal/algebraic calculus
identities. This is **not** analytic `HasDerivAt` / ODE semantics.
-/

namespace MathEvidence.Checkers.Calculus

/-- Kernel-replay soundness: checker acceptance implies the formal claim. -/
theorem replaySound
    (req : Request)
    (cert : Certificate)
    (hCheck : checkBool req cert = true) :
    Claim.proposition req.claim :=
  checkBool_sound req cert hCheck

end MathEvidence.Checkers.Calculus
