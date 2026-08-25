# 02 — Dependency-Ordered Execution Plan


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


## Program rule

No workstream may expand theorem-level Certification Record eligibility while the pinned exact-replay Lean build is red or
while the capability lacks exact candidate binding.

## Phase 0 — Re-establish a trustworthy baseline

Run in parallel:

- **SPEC-00 — Rebaseline status and trust model**
- **SPEC-01 — Restore Lean exact-replay CI/build**
- **SPEC-11 — Preserve/extend bounded execution and security** as a cross-cutting review obligation

Exit gate:

- exact CI failure is reproduced and resolved;
- historical completion claims are reclassified;
- no unsupported exact mode can mint a CR.

## Phase 1 — Build the shared assurance substrate

Order:

1. **SPEC-02 — Assurance capability registry**
2. **SPEC-03 — Exact replay generator framework**
3. **SPEC-08 — Certification Record vNext**

These can overlap after their interfaces are agreed, but merge order should make fail-closed behavior observable at every
commit.

Exit gate:

- policy is registry-driven;
- ideal membership is migrated to the generic exact generator framework;
- CRs bind generator/candidate/toolchain/replay identity.

## Phase 2 — Expand exact capability coverage

Recommended order:

1. **SPEC-04 — Rational equality**
2. **SPEC-05 — Linear algebra**
3. **SPEC-06 — Finite counterexample / certified refutation**
4. **SPEC-07 — Calculus**

Reasoning:

- rational equality is a compact exact domain and a good stress test for canonicalization;
- linear algebra exercises dimensional structure and larger payloads;
- counterexample work forces result-polarity semantics (`refuted` vs `proved`);
- calculus carries the largest risk of semantic overbreadth and must be last, with a narrow grammar.

Each capability is enabled independently. There is no batch promotion.

## Phase 3 — Make replay and evaluation release-grade

- **SPEC-09 — Offline replay and release bundle**
- **SPEC-10 — Benchmark, conformance, and adversarial rebaseline**
- continue **SPEC-11 — Security hardening**

Exit gate:

- exact replay from clean materialized dependencies succeeds;
- tamper tests fail as designed;
- CI distinguishes benchmark-science failures from environment/replay prerequisite failures;
- all CR-eligible capabilities have exact mismatch/substitution tests.

## Phase 4 — Operationalize the takeover

- **SPEC-12 — Handoff documentation and runbook**

This spec is maintained throughout the program and becomes the final operator/onboarding interface.

## Dependency DAG

```text
SPEC-00 -----------+
                   |
SPEC-01 -----+     |
             |     v
             +--> SPEC-03 ----+----> SPEC-04
SPEC-02 -----------+           +----> SPEC-05
             |                 +----> SPEC-06
             |                 +----> SPEC-07
             v
          SPEC-08 ------------------> capability CR integration
             |                         |
             +----------+--------------+
                        v
                     SPEC-09
                        |
                        v
                     SPEC-10

SPEC-11 = cross-cutting gate on 01/03/04/05/06/07/09/10
SPEC-12 = continuous documentation/runbook work
```

## Work allocation recommendation

A practical ownership split for multiple engineers:

- **Assurance/Lean owner:** SPEC-01, Lean portions of 03–07.
- **Platform/API owner:** SPEC-02, SPEC-08, policy/receipt integration.
- **Replay/reproducibility owner:** SPEC-03, SPEC-09, CI integration in SPEC-10.
- **Security/test owner:** SPEC-11 plus adversarial portions of every capability.
- **Technical lead:** SPEC-00, interface review, acceptance matrix, SPEC-12.

Ownership does not remove cross-review: a new CR-eligible capability should require review from both the capability/Lean owner
and the platform/trust-boundary owner.

## Merge discipline

Every PR in this program should state:

1. which maturity dimensions it changes;
2. whether CR eligibility changes;
3. exact candidate-binding mechanism;
4. new trusted code/dependencies;
5. replay determinism impact;
6. adversarial/tamper tests added;
7. documentation/registry changes;
8. rollback behavior.

A PR that only adds a checker must not describe itself as "certification complete."
