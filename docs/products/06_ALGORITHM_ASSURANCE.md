# Product 6 — Algorithm Assurance

## 1. Purpose

Algorithm Assurance specifies, verifies, and audits the mathematical contracts underlying computational capabilities. It focuses on checkers, open reference implementations, restricted algorithm classes, and correspondence tests for production backends.

## 2. Problem solved

Output checking establishes individual results. Some community needs require stronger guarantees about a reusable algorithm, transformation, or implementation class. Full verification of proprietary CAS internals is usually inaccessible and is not the project objective.

## 3. Assurance targets

Ordered from most practical to strongest:

1. Individual output verification.
2. Verified checker soundness.
3. Verified executable reference algorithm.
4. Proof of completeness for a restricted input class.
5. Implementation correspondence for an open production implementation.
6. Differential and conformance evidence for a proprietary backend.

The assurance level is always reported.

## 4. Candidate initial projects

- rational-expression normalization;
- exact matrix inversion over fields;
- polynomial decomposition reconstruction;
- symbolic differentiation;
- recurrence verification;
- and selected finite enumeration algorithms.

## 5. Contract specification

An algorithm contract defines:

- input domain;
- output relation;
- termination condition;
- soundness;
- completeness, if claimed;
- complexity assumptions;
- and representation refinement.

## 6. Proprietary backend policy

For Mathematica, the project may:

- specify a restricted operation contract;
- validate every returned result;
- compare against open reference implementations;
- and characterize observed support.

It does not claim to verify Mathematica’s internal implementation without access to the relevant source and proof obligations.

## 7. Failure modes

- checker effectively duplicates the full solver;
- verified reference implementation is unusably slow;
- completeness theorem assumes an unrealistic domain;
- implementation correspondence is inferred from tests alone;
- or assurance language overstates what is proved.

## 8. Acceptance criteria

1. Every assurance claim identifies its exact level.
2. At least one reference algorithm has a complete specification and proof.
3. Performance and coverage are reported separately from correctness.
4. Proprietary conformance is described as empirical unless formally linked.
5. Verified components are reusable by domain checkers and external projects.
