# MATH-AI cross-context replacement feasibility clarification

**Status:** FROZEN BEFORE REPLACEMENT EXECUTION  
**Date:** 2026-09-30  
**Parent evidence:** initial feasibility smoke at commit `d3998c4eb2021d3e4895fa2a27b8b0f0f941b84a`  
**Evidence role:** post-smoke protocol clarification implementing the predeclared 2026-08-27 replacement rule

The initial feasibility smoke is retained unchanged. In all three originally
selected contexts, the clean candidate, source-corruption mutation,
invalid-proof mutation, prohibited-placeholder mutation, and inverse repairs
were operational. The frozen WRONG_TARGET construction remained accepted by
the requested-target probe, so the intended target-mismatch mechanism was not
operational. No compound lattice was executed.

The August 27 design predeclared the ordered replacement list
`IdealMembership`, `Counterexample`, `Level`. Because all three original
contexts failed the same feasibility requirement simultaneously, this
clarification applies the ordered list one-for-one:

- RX1: `MathEvidence.Assurance.IdealMembership`
- RX2: `MathEvidence.Assurance.Counterexample`
- RX3: `MathEvidence.Assurance.Level`

This simultaneous mapping was not spelled out in the August 27 document and is
therefore explicitly labeled a post-smoke protocol clarification. No
replacement-context execution has been inspected before fixing this mapping.

The exact target pairs are frozen here:

- RX1 clean: `contract.claimsCompleteness = false`; wrong:
  `contract.linksDecls = true`; proof body `native_decide`.
- RX2 clean: `contract.claimsCompleteness = false`; wrong:
  `contract.assuranceLevel = .verifiedReferenceAlgorithm`; proof body
  `native_decide`.
- RX3 clean:
  `AssuranceLevel.toWire .outputVerification = "output_verification"`; wrong:
  `AssuranceLevel.toWire .checkerSoundness = "checker_soundness"`; proof
  body `rfl`.

The four mechanism names and transferred classes remain unchanged. The frozen
v2 classifier remains unchanged. This stage executes only clean candidates,
singletons, and exact inverse repairs. If any replacement fails feasibility,
the full 48-state/96-edge extension remains blocked. No alternate target or
additional replacement will be selected from replacement outcomes.
