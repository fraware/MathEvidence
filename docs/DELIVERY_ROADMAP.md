# Delivery Roadmap

## Milestone 0 — Project validation

Deliverables:

- project charter and trust model;
- twenty or more real computational bottlenecks;
- adversarial semantic benchmark seed;
- ecosystem RFC;
- rational-equality capability specification;
- LeanLink adapter design review.

Exit criteria:

- at least three external users confirm the problem;
- the initial capability is materially useful beyond existing tactics;
- the end-to-end trust theorem is understood;
- and the open-backend path is credible.

## Milestone 1 — Rational equality reference path

Deliverables:

- restricted rational-expression IR;
- reifier and soundness theorem;
- solver-independent request and evidence schema;
- Mathematica adapter (wolframscript; LeanLink deferred);
- SymPy or SageMath adapter;
- verified equality checker;
- offline evidence bundle;
- `mathevidence` tactic;
- conformance suite.

Exit criteria:

- two backends share one checker;
- all committed results replay offline;
- side conditions are explicit;
- request mismatch is rejected;
- no forbidden axioms or `sorry`.

## Milestone 2 — Cross-domain proof

Deliverables:

- exact matrix inverse and system-solution witnesses;
- finite counterexample checker;
- capability registry;
- first Agent API release;
- VS Code evidence inspector.

Exit criteria:

- common core remains small;
- no unsafe generic escape hatch is required;
- agent integration improves a held-out task set;
- one external Lean project adopts a component.

## Milestone 3 — Hypothesis intelligence

Deliverables:

- condition proposal interface;
- sufficient-condition proof loop;
- hypothesis deletion;
- certified counterexample generation;
- condition lattice artifact;
- training episodes.

Exit criteria:

- repaired statements pass semantic expert review;
- weaker variants receive certified counterexamples where claimed;
- minimality is never asserted without proof.

## Milestone 4 — Ecosystem federation

Deliverables:

- adapters or registry integration for existing Gröbner, SAT, pseudo-Boolean, and SMT projects;
- shared provenance and claim status;
- collaboration plan with CSLib and relevant maintainers.

Exit criteria:

- MathEvidence adds interoperability without replacing specialized checkers;
- at least two existing projects consume or emit shared metadata.

## Milestone 5 — Symbolic calculus vertical

Deliverables:

- derivative-candidate verification;
- antiderivative verification on explicit domains;
- recurrence identity checking;
- ODE candidate and initial-condition checking;
- Wolfram Studio workflow.

Exit criteria:

- repeated evidence patterns support several results;
- branch and singularity conditions are explicit;
- candidate validity remains separate from completeness.

## Milestone 6 — Foundry and frontier research

Deliverables:

- public certified tool-use corpus;
- verification-aware tool-selection benchmark;
- selected frontier mathematics collaborations;
- measured downstream library contributions.

Exit criteria:

- data improves held-out verified tool use;
- at least one frontier program is materially accelerated;
- maintenance funding and ownership are established.
