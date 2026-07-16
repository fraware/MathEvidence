# Product 3 — Hypothesis Synthesis

## 1. Purpose

Hypothesis Synthesis repairs mathematically incomplete theorem statements by proposing side conditions, proving their sufficiency in Lean, testing weakenings, and producing certified counterexamples when assumptions are removed.

## 2. Problem solved

Informal mathematics frequently omits conditions that are obvious to experts or conventional in a domain. Autoformalization systems can produce statements that are false, overspecified, or semantically misaligned. External CAS systems can often identify validity regions or counterexamples, but their conditions must be translated and formally justified.

## 3. Output

The primary output is a **condition lattice artifact**, not one opaque repaired statement.

It records:

- original assumptions;
- backend-proposed conditions;
- sufficient condition sets proved in Lean;
- redundant conditions proved removable;
- weakened variants tested;
- certified counterexamples;
- unresolved necessity questions;
- and the final recommended theorem interface.

## 4. Workflow

1. Receive a candidate Lean proposition.
2. Identify partial operations and domain-sensitive identities.
3. Generate candidate condition sets through backend reasoning and library heuristics.
4. Attempt Lean proof under each candidate set.
5. Remove one condition at a time according to a bounded search policy.
6. Ask backends for counterexamples to failed variants.
7. Verify returned counterexamples in Lean.
8. Rank theorem interfaces by generality, clarity, and library conventions.
9. Require human review before upstreaming.

## 5. Invariants

- Proposed conditions are never silently inserted.
- Sufficiency is a Lean theorem.
- Necessity is claimed only when a proof or complete counterexample argument exists.
- Absence of a found counterexample is not evidence of necessity or truth.
- Numerical counterexamples must be converted to exact witnesses or certified enclosures.
- The recommended statement preserves the original intended mathematical domain.

## 6. Initial domains

- nonzero denominators;
- positivity and sign conditions;
- finite-domain counterexamples;
- simple parameter exclusions;
- and exact real/rational algebraic identities.

Branch-sensitive complex analysis is deferred.

## 7. APIs

Agent and tactic operations:

- `propose_conditions`
- `prove_sufficient`
- `delete_hypothesis`
- `find_counterexample`
- `verify_counterexample`
- `build_condition_lattice`

## 8. Ranking policy

The system may rank statements but must explain criteria:

- logical generality;
- alignment with existing library APIs;
- number and complexity of assumptions;
- availability of reusable lemmas;
- and human readability.

No model-only score determines semantic correctness.

## 9. Failure modes

- condition is sufficient but unnatural;
- backend returns conditions in a different domain;
- counterexample uses an unsupported coercion;
- exponential hypothesis search;
- accidental theorem strengthening;
- or false minimality claim.

## 10. Acceptance criteria

1. Repaired statements are proved in Lean.
2. Removed assumptions have either a proof of redundancy or a certified failing variant.
3. Minimality language is absent unless formally established.
4. Expert reviewers judge the recommended theorem interfaces mathematically appropriate.
5. The product improves autoformalization semantic accuracy on held-out examples.
