# SPEC-09 — Deterministic Offline Replay and Release-Grade Bundle


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1/P2  
**Depends on:** SPEC-01, SPEC-03, SPEC-08  
**Owner profile:** Reproducibility/build engineer

## Objective

Allow a saved exact-certification bundle to be replayed from a clean workspace with the required dependency closure
materialized and network access disabled, while detecting any corruption or substitution.

## Bundle contents

At minimum:

- canonical claim/candidate payload or canonical representation;
- Certification Record;
- exact replay manifest;
- generated Lean source or deterministic regeneration inputs;
- generator/grammar versions;
- verifier/toolchain contract;
- dependency lock/vendor integrity metadata;
- artifact files/hashes;
- expected declaration/result identity;
- bounded-execution policy identifier;
- replay command/driver version.

Do not include local absolute paths as semantic requirements.

## Replay modes

### Regenerate-and-verify

Recreate generated source from canonical candidate + pinned generator, compare expected source hash, then verify.

### Artifact replay

Verify the saved generated source after checking its hash and all bound metadata.

Both modes should reach the same logical outcome for a valid bundle.

## Offline requirement

After dependency materialization:

- disable network;
- replay must not contact registries, GitHub, package servers, or mutable remote resources;
- missing dependencies must produce a clear integrity/setup error.

## Determinism requirement

For identical:

- canonical candidate,
- capability/version,
- generator/grammar version,
- toolchain/dependency closure,

the generated replay source and semantic hashes must be identical.

## Release-grade reference case

Use exact ideal membership as the first full release-grade replay case once SPEC-01 restores the Lean build.

## Tamper matrix

Replay must fail for:

- candidate mutation;
- generated source mutation;
- artifact mutation/deletion;
- manifest mutation;
- generator version mismatch;
- theorem/declaration identity mismatch;
- toolchain/dependency lock mismatch;
- capability/version mismatch.

## Acceptance criteria

- [ ] Exact reference bundle created by normal API path.
- [ ] Bundle replays in a clean workspace.
- [ ] Replay succeeds with network disabled after materialization.
- [ ] Regenerated source equals bound source hash.
- [ ] All tamper cases fail deterministically.
- [ ] Missing dependency reports setup/integrity failure, not theorem failure.
- [ ] No mutable remote URL is required at replay time.
- [ ] Same replay path is reusable for every CR-eligible capability.

## Deferred but prepared

Independent third-party reproduction is outside this handoff's required scope. The bundle format must nevertheless be usable
by an external reproducer later without needing hidden local state.

## Definition of done

A Certification Record can be accompanied by a self-contained, integrity-checked replay package whose logical result can be
re-established offline under the declared toolchain contract.
