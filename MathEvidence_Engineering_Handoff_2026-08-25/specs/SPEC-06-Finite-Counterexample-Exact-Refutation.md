# SPEC-06 — Exact Finite Counterexample and Certified Refutation


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
**Existing asset:** Lean finite-counterexample checker/soundness contract

## Central semantic requirement

A verified counterexample establishes **refutation of the specified universal/general claim**, not proof of that claim.
Certification polarity must make this impossible to confuse.

## Objective

Bind the submitted claim/predicate representation, finite domain/model semantics, and exact witness into replay so that the
trusted checker establishes that the witness violates the candidate-specific claim.

## Required outcome model

Certification/result schema must support a distinct outcome such as:

```text
result = refuted
```

Do not encode refutation as `proved=true` without an explicit proposition such as "the original claim is false." Prefer a
first-class polarity field for clarity and downstream safety.

## Candidate binding

Bind all of:

- claim/predicate or canonical claim identifier/encoding;
- finite domain/model when semantically relevant;
- quantification scope;
- witness value/assignment;
- evaluation/check result;
- capability/checker/verifier identity.

## Exhaustive proof distinction

A valid witness can refute a universal claim without exhaustive search.

Conversely:

- failure to find a witness does not prove the universal claim;
- sampling does not prove universality;
- exhaustive finite proof is a different assurance path and must explicitly bind the complete finite domain and exhaustive
  checker if supported.

## Tests

Positive:
- known witness violates exact claim -> `refuted`.

Negative:
- witness does not violate claim;
- witness outside domain;
- predicate/claim mutated;
- domain mutated;
- witness mutated;
- fixture witness for another claim;
- empty search result treated as proof;
- sampled search result incorrectly requests theorem `proved`.

## Acceptance criteria

- [ ] Exact witness is candidate-bound.
- [ ] Claim/predicate semantics are candidate-bound.
- [ ] Domain/scope is bound where required.
- [ ] `refuted` and `proved` cannot be conflated in record/API.
- [ ] No-witness/sampling path cannot mint universal-proof CR.
- [ ] Registry lists allowed outcomes explicitly.
- [ ] Offline/tamper replay passes.
- [ ] Existing evidence-only search workflows remain usable without assurance inflation.

## Definition of done

MathEvidence can issue an independently replayable certified refutation whose semantics are explicit and whose witness is
provably tied to the submitted claim.
