# SPEC-04 — Exact Candidate-Bound Rational Equality Certification


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1 capability  
**Depends on:** SPEC-02, SPEC-03, SPEC-08 interface  
**Existing asset:** Lean rational-equality checker/soundness contract

## Objective

Enable theorem-level certification for the exact rational-equality grammar already supported by the repository's checker,
binding the actual submitted expressions/values to generated Lean replay.

## Scope discipline

The theorem path is for exact arithmetic. It MUST NOT infer exact rationals from binary floating-point approximations.

Recommended canonical scalar representation:

```json
{"num": -3, "den": 7}
```

with:

- integer numerator;
- strictly positive integer denominator;
- gcd normalization;
- zero represented canonically as `0/1`.

If the current evidence schema represents expressions rather than scalar pairs, preserve that schema's semantics and
normalize its rational literals using the same rules.

## Exact obligation

The generated Lean module must encode the exact candidate equality and invoke the existing verified checker/theorem in a way
that proves the candidate-specific proposition.

A fixture theorem containing unrelated hard-coded rationals is insufficient.

## Validation requirements

Reject before Lean:

- denominator zero;
- malformed integer literal;
- unsupported operator/expression constructor;
- float where exact rational is required;
- excessive expression depth/size;
- missing operand or claim target.

## Binding requirements

Certification metadata binds:

- canonical left/right expressions or candidate payload;
- operator/grammar version;
- generated source hash;
- checker/declaration identity;
- exact result.

## Test matrix

Positive:
- equal reduced rationals;
- equal unreduced input forms that canonicalize identically;
- negative values;
- zero;
- supported compound expressions if present in current grammar.

Negative:
- unequal rationals;
- denominator zero;
- candidate changed after generation;
- operator changed;
- numerator/denominator mutation;
- fixture replay substituted for candidate replay;
- float supplied to exact mode.

## Acceptance criteria

- [ ] Candidate-bound rational generator implemented.
- [ ] Generator uses only the checker grammar actually supported today.
- [ ] Equal supported candidates certify.
- [ ] Unequal candidates do not.
- [ ] All semantic candidate fields are bound into replay identity.
- [ ] Exact mode is enabled in registry only after E2E/offline/tamper tests pass.
- [ ] Fixture-backed replay cannot produce theorem-level CR for this capability.
- [ ] No float-to-rational silent coercion exists.

## Definition of done

`algebra.rational_equality` can safely move from "Lean checker exists" to "exact arbitrary supported candidate replay exists"
for its explicitly documented grammar.
