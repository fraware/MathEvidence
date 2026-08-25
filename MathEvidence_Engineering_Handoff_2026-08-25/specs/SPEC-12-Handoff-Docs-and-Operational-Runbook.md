# SPEC-12 — Engineering Handoff Documentation and Operational Runbook


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** Continuous; finalization P2  
**Owner profile:** Technical lead + each workstream owner

## Objective

Make the repository operable by engineers who did not participate in the original design, without requiring oral knowledge
to preserve assurance semantics.

## Required `docs/HANDOFF.md` content

1. repository purpose and non-negotiable assurance invariant;
2. current release/PR/commit baseline;
3. architecture diagram and trust boundary;
4. setup instructions;
5. local verification commands;
6. CI gate map;
7. capability registry format;
8. Certification Record lifecycle;
9. exact replay generation/replay lifecycle;
10. status table generated from registry;
11. known limitations;
12. incident/triage workflow.

## Capability onboarding checklist

Every new capability must execute:

```text
[ ] define capability ID/version and evidence class
[ ] define canonical candidate/evidence schema
[ ] implement adapter
[ ] implement/check evidence checker
[ ] state exact mathematical proposition and semantic domain
[ ] add Lean/reference soundness contract where exact theorem assurance is intended
[ ] add typed exact replay translation/generator
[ ] register verifier/generator/grammar versions
[ ] add exact E2E positive/negative tests
[ ] add candidate mismatch / fixture substitution tests
[ ] add offline replay bundle test
[ ] add bounded-execution/adversarial tests
[ ] update registry
[ ] enable CR eligibility only after all applicable gates pass
[ ] update generated/validated docs
```

## CI triage table

Document at least:

| Failure class | First investigation |
|---|---|
| schema/conformance | candidate/evidence schema and adapter contract |
| Lean build | toolchain, dependency closure, generated module, import/declaration |
| exact replay | candidate binding, generator, manifest, verifier identity |
| offline replay | dependency materialization, network assumptions, bundle integrity |
| benchmark | only benchmark logic/data after prerequisites are green |
| security | execution bounds, input validation, path/process handling |
| supply chain | locks/vendor hashes/dependency provenance |

## "How not to lie about assurance"

Include explicit examples:

- checker passes ≠ theorem certification;
- fixture theorem passes ≠ submitted candidate proved;
- numerical agreement ≠ exact proof;
- no counterexample found ≠ theorem true;
- benchmark success ≠ assurance;
- formal rational calculus ≠ arbitrary analytic calculus.

## Maintenance rule

Status documentation should be generated from or validated against the capability registry. A hand-edited summary may add
context, but it must not independently define CR eligibility.

## Acceptance criteria

- [ ] New engineer can identify the exact current blocker from docs.
- [ ] All local/CI verification commands are documented and tested.
- [ ] Capability onboarding checklist exists.
- [ ] Trust boundary is diagrammed.
- [ ] Status table is registry-backed.
- [ ] Known unsupported assurance modes are visible.
- [ ] Historical audit/status docs are clearly dated and not confused with current policy.
- [ ] No required assurance knowledge exists only in PR discussion or maintainer memory.

## Definition of done

A competent engineer can take over MathEvidence, add or repair a capability, and preserve the project's assurance contract
using repository-local specifications alone.
