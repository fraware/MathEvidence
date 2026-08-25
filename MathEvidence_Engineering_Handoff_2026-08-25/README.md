# MathEvidence Engineering Handoff Package

> **Archive notice:** This directory is a **dated engineering assessment package**
> (2026-08-25), not live project status. For current public status, CR eligibility,
> and the operator runbook, use [`docs/STATUS.md`](../docs/STATUS.md) and
> [`docs/HANDOFF.md`](../docs/HANDOFF.md). Internal assessment banners and SPEC
> program language inside this tree describe the pinned baseline, not today's
> registry.

> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first record the delta (see
> [`docs/validation/handoff-2026-08-25-delta.md`](../docs/validation/handoff-2026-08-25-delta.md)).
> Historical status labels are not authority for theorem-level certification eligibility.


This package is a standalone engineering takeover specification for completing the MathEvidence vision without weakening its
central trust invariant: **the system may promote a mathematical claim to theorem-level certification only when the exact
candidate/claim instance has been validated by the declared trusted verification path.**

## How to use this package

1. Read `00_CURRENT_STATE.md` first. It is the pinned factual baseline.
2. Read `01_TARGET_ARCHITECTURE.md` to understand the intended end-state and trust boundary.
3. Use `02_EXECUTION_PLAN.md` as the dependency-ordered implementation program.
4. Treat `03_ACCEPTANCE_MATRIX.md` as the program-level exit gate.
5. Assign files under `specs/` as independently executable engineering work packages.

## Non-negotiable interpretation rule

Do **not** equate any of the following:

- an adapter exists;
- an evidence checker exists;
- a Lean soundness theorem exists;
- a fixture or bridge replay passes;
- an exact candidate-bound replay exists;
- a capability is authorized to mint a theorem-level Certification Record.

Those are separate maturity dimensions. The last item requires the preceding assurance obligations that are applicable to that
capability, plus an explicit fail-closed policy entry.

## Current priority

At the pinned PR head, security, adapter-conformance, supply-chain, and adversarial gates pass. The `lean`, `offline-replay`,
and `benchmarks` workflows are red. Available job metadata localizes the shared failure to the Lean/exact-replay build
integration path: schema/import/audit stages complete, while the Lean `lake build` stage and exact release-grade dependency
build do not. The benchmark suite itself is not established to be failing mathematically.

Therefore the immediate program order is:

1. restore the exact Lean replay build without bypassing audits;
2. rebaseline documentation and machine-readable capability status;
3. centralize assurance policy and exact-replay generation;
4. add exact candidate-bound replay capability-by-capability;
5. complete deterministic offline replay, adversarial coverage, and release-grade conformance.

## Deliberately deferred

This handoff prepares interfaces for, but does not require completion of:

- independent external reproduction by third parties;
- human governance processes;
- final release-signing/attestation policy.

These must not be used as excuses to defer machine-enforced assurance correctness.
