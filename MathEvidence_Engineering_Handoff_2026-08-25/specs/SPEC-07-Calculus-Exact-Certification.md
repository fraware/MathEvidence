# SPEC-07 — Calculus Exact Certification with Explicit Semantic Scope


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1/P2 capability — implement after simpler exact domains  
**Depends on:** SPEC-02, SPEC-03, SPEC-08  
**Existing assets:** formal rational-calculus Lean assurance module; analytic-calculus replay/profile infrastructure

## Problem

"Calculus" is semantically too broad to advertise as one theorem-certified capability. Formal differentiation of rational
expressions, analytic derivatives under domain hypotheses, numerical quadrature, and numerical differentiation have
different proof obligations.

## Objective

Split calculus assurance into narrowly specified capability grammars and certify only those exact obligations that are
actually formalized and candidate-bound.

## Track A — Formal rational calculus

Target: `algebra.formal_rational_calculus` or current equivalent.

- Reuse the existing Lean checker/soundness contract.
- Define a typed AST for the exact expression grammar already accepted.
- Bind variable identity, expression tree, requested formal operation, claimed result, and required algebraic side
  conditions.
- Implement deterministic candidate-bound generator.
- Keep scope described as formal/algebraic where that is what the checker establishes.

## Track B — Analytic calculus

Target: `analysis.analytic_calculus` only after a narrow theorem grammar is defined.

Every supported analytic theorem form must include its hypotheses. Depending on the actual formalized theorem this can
include:

- domain/interval;
- differentiability/integrability hypotheses;
- denominator nonzero assumptions;
- branch/continuity constraints;
- endpoint/interior conditions;
- exact target expression/value.

Do not infer missing hypotheses from a numerical sample.

Start with a whitelist of theorem forms backed by explicit Lean declarations. Unsupported claims fail closed.

## Numerical calculus

Numerical derivatives/integrals may retain useful evidence classes with error estimates or checks. They must not be routed
through exact theorem certification unless an exact formal theorem explicitly justifies that result and all hypotheses are
bound.

## Security

Expression AST only. No raw Lean code from request payloads.

## Tests

Formal:
- valid supported expression/result;
- wrong result;
- expression mutation;
- variable mutation;
- unsupported constructor;
- denominator/side-condition violation.

Analytic, for every enabled theorem form:
- positive theorem with all hypotheses;
- omitted hypothesis;
- domain mutation;
- singularity/branch counterexample where relevant;
- false claimed derivative/integral;
- numerical approximation submitted to exact mode.

## Acceptance criteria

- [ ] Formal and analytic calculus are separate assurance entries.
- [ ] Formal grammar is explicitly documented from current checker semantics.
- [ ] Formal rational-calculus candidate-bound replay is complete before CR enablement.
- [ ] Analytic exact modes are whitelisted theorem-by-theorem.
- [ ] Required analytic hypotheses are encoded and bound.
- [ ] Unsupported/underspecified analytic claim fails closed.
- [ ] Numerical calculus remains non-theorem evidence unless a separate exact theorem path applies.
- [ ] Offline/tamper tests pass for every enabled theorem form.

## Definition of done

"Calculus certification" is no longer an ambiguous umbrella: every promoted result names the exact formal/analytic grammar and
hypotheses that were verified.
