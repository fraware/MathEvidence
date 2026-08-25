# SPEC-01 — Restore Lean Exact-Replay Build and CI


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P0 — immediate blocker  
**Owner profile:** Lean/toolchain/reproducibility engineer  
**Blocks:** All expansion of exact certification

## Problem

At the pinned PR head, `lean`, the Lean leg of `offline-replay`, and the release-grade benchmark job are red. The common
failure boundary is the Lean/exact replay build path.

The available metadata shows the Lean workflow progressing through schema/import/audit checks and then failing at `lake
build`. The release-grade benchmark job fails while building exact replay dependencies. The benchmark suite itself passes.

## Objective

Restore a clean, reproducible Lean build for the pinned exact replay architecture and make the exact ideal-membership
candidate replay pass without bypassing any trust/audit gate.

## Mandatory first diagnostic task

From a fresh checkout of `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`:

1. record OS/container image;
2. record `lean --version`, Lake version, toolchain file, dependency lock state;
3. run the exact failing CI commands locally or in an equivalent clean runner;
4. retain the full first compiler/dependency diagnostic;
5. identify whether failure originates in:
   - dependency/vendor materialization;
   - import path/module name;
   - generated replay source;
   - declaration identity/audit driver;
   - mathlib/toolchain incompatibility;
   - CI-only environment assumptions;
   - another cause established by evidence.

Do not speculate in the final fix PR; attach the reproduced diagnostic.

## Implementation requirements

- Pin or repair Lean/Lake/mathlib/vendor integration as required by the reproduced error.
- Generated exact replay modules must compile under the same pinned toolchain as verification.
- Offline/release-grade replay must not silently fetch mutable remote dependencies.
- Preserve import-boundary, declaration-identity, sorry/axiom, and trusted-boundary audits.
- Do not "fix" the failure by skipping the generated module, weakening the theorem, disabling an audit, or converting exact
  replay into fixture replay.
- Keep CI dependency setup shared enough that `lean`, `offline-replay`, and release-grade benchmark jobs exercise the same
  pinned closure.
- Emit diagnostics that distinguish dependency/setup failure from theorem/checker failure.

## Required tests

Positive:
- clean `lake build`;
- exact ideal-membership generated module builds;
- exact ideal-membership replay succeeds;
- offline saved replay succeeds after dependency materialization.

Negative/tamper:
- mutate candidate payload while retaining old expected hash -> fail;
- mutate generated source -> source/hash or replay validation fails;
- change declared verifier/declaration identity -> fail;
- omit a required vendored dependency in offline mode -> explicit failure;
- run with network disabled after materialization -> still succeeds.

## Acceptance criteria

- [ ] Exact failure reproduced and root cause documented.
- [ ] `lean` workflow green at implementation head.
- [ ] Lean leg of `offline-replay` green.
- [ ] Release-grade exact replay prerequisite job green.
- [ ] Benchmark suite still passes.
- [ ] Existing sorry/axiom/import/declaration audits remain enabled and green.
- [ ] No new unpinned mutable dependency is introduced.
- [ ] Exact ideal-membership candidate replay succeeds from a clean environment.
- [ ] Tampered exact candidate/replay artifacts fail.

## Definition of done

The repository again has a green Lean foundation on which exact candidate-bound certification can safely expand.
