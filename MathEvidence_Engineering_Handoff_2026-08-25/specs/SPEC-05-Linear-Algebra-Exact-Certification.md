# SPEC-05 — Exact Candidate-Bound Linear Algebra Certification


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1 capability  
**Depends on:** SPEC-02, SPEC-03, SPEC-08  
**Existing asset:** Lean linear-algebra checker/soundness contract

## Problem

A broad label such as "linear algebra" can hide materially different proof obligations. Exact certification must correspond
to the concrete operation discriminants already represented by the current evidence schema/checker.

## Objective

Implement candidate-bound exact replay for the **existing** supported linear-algebra operations, with operation-specific
registry rows/tests and exact integer/rational payloads.

## Mandatory discovery step

Before coding, enumerate from the current schema/checker:

- every operation discriminant;
- exact input types;
- dimensional preconditions;
- claimed result/witness type;
- checker result semantics;
- associated Lean declaration.

Commit this table as part of the spec implementation. Do not add operations simply to make the capability look generic.

## Representation

For theorem-level paths:

- integer and exact rational entries only unless the existing checker proves another exact domain;
- dimensions explicitly bound;
- row/column ordering canonical;
- all entries bound;
- operation discriminant bound;
- claimed output/witness bound;
- assumptions/preconditions explicit.

Numerical floating-point linear algebra remains a different evidence class.

## Required checks

Before Lean:

- dimension consistency;
- rectangular shape where required;
- expected result shape;
- exact scalar validity;
- configured size limits.

Lean replay then checks the actual mathematical obligation.

## Registry strategy

Prefer operation-level sub-capability metadata or an explicit operation field with separate assurance entries. A user should
be able to determine exactly which operation is CR-eligible.

## Test matrix

For each existing exact operation:

- one positive candidate;
- one mathematically false candidate;
- dimension mismatch;
- single-entry mutation;
- result/witness mutation;
- operation-discriminant mutation;
- row/column permutation where semantics change;
- exact-vs-float mode misuse;
- fixture substitution.

## Acceptance criteria

- [ ] Supported-operation inventory committed and reviewed.
- [ ] No operation beyond existing verified semantics is advertised.
- [ ] Candidate-bound generator covers each enabled operation.
- [ ] Dimensions and every semantic entry are bound.
- [ ] Per-operation E2E tests pass.
- [ ] Numerical LA is not promoted through exact path.
- [ ] Registry enables only operations with complete exact/offline/tamper evidence.
- [ ] Unsupported operations fail `assurance_mode_unavailable` or the project's equivalent stable error.

## Definition of done

The repository can truthfully state exactly which linear-algebra obligations it certifies, instead of relying on a broad
capability label.
