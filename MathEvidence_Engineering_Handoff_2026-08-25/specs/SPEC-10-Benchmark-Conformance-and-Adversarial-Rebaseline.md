# SPEC-10 — Benchmark, Conformance, Replay, and Adversarial Gate Rebaseline


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P2 integration  
**Depends on:** SPEC-03–09 as applicable  
**Owner profile:** Test/infrastructure engineer

## Problem

A single red "benchmarks" workflow can currently hide whether the benchmark itself failed or an exact replay prerequisite
failed. More importantly, benchmark performance and assurance correctness are orthogonal properties.

## Objective

Make CI explicitly test five independent dimensions:

1. mathematical/task benchmark behavior;
2. adapter/schema conformance;
3. exact certification soundness;
4. replay determinism/integrity;
5. bounded execution/security.

## Required CI structure

Recommended distinct jobs/statuses:

```text
benchmark-task-suite
adapter-conformance
assurance-exact-replay
offline-replay
replay-tamper
security-bounded-execution
supply-chain
lean-assurance-audit
```

A release-grade benchmark may depend on exact replay, but failures must identify whether setup/replay or benchmark logic failed.

## Assurance adversarial corpus

For every CR-eligible capability, include:

- candidate mismatch;
- fixture substitution;
- canonical hash mutation;
- generated source mutation;
- wrong capability/version;
- wrong generator/version;
- wrong verifier/declaration;
- unsupported assurance-mode request;
- stale/legacy record attempted as exact;
- relevant semantic side-condition omission.

## Benchmark doctrine

- benchmark score never changes `cr_eligible`;
- benchmark fixture replay never proves arbitrary candidate exactness;
- benchmark data should test capability quality/performance, while assurance tests independently test proof/check semantics;
- setup failures are reported separately from mathematical incorrectness.

## Regression requirements

Preserve current green baselines for:

- security;
- adapter conformance;
- supply chain;
- adversarial tests.

## Acceptance criteria

- [ ] CI job names/outputs distinguish environment failure from benchmark failure.
- [ ] Exact replay has a dedicated gate.
- [ ] Every CR-eligible capability has mismatch/substitution tests.
- [ ] Unsupported exact modes are covered.
- [ ] Benchmark score cannot mutate assurance policy.
- [ ] Legacy exact-upgrade attack is covered.
- [ ] Security/conformance/supply-chain/adversarial gates remain green.
- [ ] Release branch protection can require assurance-specific gates independently of benchmark score.

## Definition of done

The CI surface tells maintainers exactly whether a failure is scientific, schema-level, assurance-level, replay-level, or
security-level, and no benchmark success can mask a trust-boundary defect.
