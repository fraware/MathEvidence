# P02 MATH-AI cross-context feasibility-harness conformance note

Status: protocol-conformance record only; no publication claim is authorized by this note.

## Why this note exists

The original cross-context raw smoke harness at commit `736ce4c4faf9cf5ad89148047af755fc2fa62f53` implemented 15 raw cases: clean plus the four frozen single-perturbation families in each of the three frozen contexts. The written preregistration in `labtrust-portfolio/papers/P02_KernelCheckedEvidence/MATHAI_CROSS_CONTEXT_CONTEXT_FREEZE.md` additionally requires the exact inverse repair of each single mutation and pairwise repair-commutativity checks before the 48-state compound corpus is frozen.

The 15-case harness was therefore a partial feasibility smoke, not the complete preregistered feasibility gate.

## Timing and blinding

An initial GitHub Actions attempt of the 15-case harness failed during transitive dependency build before any smoke case executed. An exact rerun of that old commit was subsequently started. Before consulting the scientific outcome of that rerun, the harness was brought into conformance with the already-written feasibility protocol and committed as `c5000d879bb1dcb8875842b84f107cc99f7fd822`.

No context, perturbation family, clean target, wrong target, proof body, transferred observation ordering, diagnostic classifier, timeout, compound-state prediction, or scientific scoring rule was changed in that conformance commit.

## What changed in v2

`p02_mathai_cross_context_smoke_raw_v2` preserves the three contexts and four frozen active perturbation mechanisms from v1 and adds only protocol-required feasibility checks:

1. deterministic source-level application of each already-frozen mutation;
2. an exact deterministic inverse repair for each mutation;
3. an assertion that each inverse repair restores the byte-identical clean source;
4. execution of clean, four single-perturbation, and four inverse-repair cases per context (27 raw cases total);
5. pairwise repair-commutativity checks for all six unordered mechanism pairs in each context (18 checks total);
6. explicit hashes and a conformance digest.

The conformance checks are source-construction checks. They do not assign diagnostic classes and are not evidence of cross-context transfer, compound-state prediction accuracy, repair-transition accuracy, or external validity.

## Preserved timing discrepancy for CX1 wrong target

The original v1 harness already fixed the CX1 `WRONG_TARGET` source as

`contract.assuranceLevel = .verifiedReferenceAlgorithm`

before any smoke case executed. The prose context-freeze document had stated that the concrete CX1 wrong target would be frozen after a pre-execution clean/wrong-target feasibility smoke. These two records are not perfectly aligned in timing. The implementation choice is preserved unchanged in v2; it is not retroactively reselected based on any observed outcome. Any later report of the extension must disclose this discrepancy.

## Claim boundary

Completion of the feasibility gate does not make the cross-context extension publication-claim eligible. The 48 compound states and 96 directed one-perturbation removals must still be frozen before compound execution, executed under the pinned environment, classified with the frozen interface without label leakage or post-outcome changes, reported per context without IID pooling, and independently reviewed. `UNKNOWN` outcomes and mismatches must be retained.
