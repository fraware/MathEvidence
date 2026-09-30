# MATH-AI cross-context final feasibility mapping

**Status:** FROZEN BEFORE FINAL FEASIBILITY EXECUTION  
**Date:** 2026-09-30  
**Primary project revision:** `946d2f7b14840837a5b641150c9df9008c4be9eb`  
**Lean:** `4.14.0`  
**Evidence role:** feasibility only; no compound-state result

The initial selected-context smoke is retained unchanged at commit
`d3998c4eb2021d3e4895fa2a27b8b0f0f941b84a`. It showed that each original
WRONG_TARGET choice remained target-matching. No compound state was executed.

The August 27 context freeze expressly left CX1 RationalEquality's concrete
alternative target to the feasibility stage. The first concrete candidate
`contract.claimsCompleteness = contract.claimsCompleteness` failed that gate.
Before any further CX1 execution, the final candidate is now fixed as
`contract.linksDecls = true`, with the unchanged proof body
`native_decide`. No further CX1 fallback will be attempted.

The exact wrong-target families for the original CX2 and CX3 were frozen in
August and are not rewritten. They are replaced under the predeclared ordered
replacement rule. The first listed replacement, IdealMembership, has now been
shown to fail compilation in the untouched pinned project before any
replacement mutation execution. A build-only probe then established that the
next two listed modules, Counterexample and Level, compile at the pinned
revision. No mutation outcome from those replacements has been inspected.

The final three-context feasibility mapping is therefore fixed as:

- CX1R — RationalEquality. Clean target:
  `contract.claimsCompleteness = false`. Wrong target:
  `contract.linksDecls = true`. Proof: `native_decide`.
- RX2 — Counterexample. Clean target:
  `contract.claimsCompleteness = false`. Wrong target:
  `contract.assuranceLevel = .verifiedReferenceAlgorithm`. Proof:
  `native_decide`.
- RX3 — Level. Clean target:
  `AssuranceLevel.toWire .outputVerification = "output_verification"`.
  Wrong target:
  `AssuranceLevel.toWire .checkerSoundness = "checker_soundness"`. Proof:
  `rfl`.

The transferred operational signatures, precedence, frozen v2 classifier, and
four active mechanism names are unchanged. This stage executes only the clean
candidate, four singletons, and exact inverse repairs in each context. Any
failure blocks the full lattice. There is no additional replacement list and
no post-outcome target editing.
