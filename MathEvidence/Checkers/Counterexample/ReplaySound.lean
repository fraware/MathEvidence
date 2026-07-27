/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Checkers.Counterexample.Bridge
import MathEvidence.Checkers.Counterexample.Soundness
import MathEvidence.Checkers.Counterexample.Spec

/-!
# Counterexample kernel-replay soundness (ME-RV-043)

`replaySound` is the theorem-producing authority for finite-counterexample
kernel replay. Proof uses `checkBool_sound` — not an independent final
`native_decide` on the original Lean proposition.
-/

namespace MathEvidence.Checkers.Counterexample

/-- Kernel-replay soundness: checker acceptance implies the claim proposition. -/
theorem replaySound
    (req : Request)
    (cert : Certificate)
    (hCheck : checkBool req cert = true) :
    Claim.proposition req.claim cert.witness :=
  checkBool_sound req cert hCheck

end MathEvidence.Checkers.Counterexample
