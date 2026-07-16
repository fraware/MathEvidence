# Product 8 — MathEvidence Foundry

## 1. Purpose

The Foundry converts complete computational-proof interactions into high-quality datasets for verification-aware mathematical AI, capability evaluation, and system diagnosis.

## 2. Problem solved

Most formal-mathematics datasets contain theorem statements, final proofs, or tactic states. They rarely capture why an external tool was selected, how a mathematical object was encoded, which conditions were introduced, why evidence failed, and how the statement was repaired.

## 3. Episode schema

An episode contains:

- source and licensing metadata;
- original Lean environment and goal;
- capability candidates;
- selected operation and requested claim class;
- typed request;
- backend and adapter versions;
- candidate result;
- evidence;
- checker output;
- semantic and system errors;
- proof obligations;
- repairs;
- final theorem or failure status;
- dependency and axiom report;
- human review labels;
- and resource usage.

## 4. Quality tiers

- `Q0_raw` — unreviewed execution record;
- `Q1_schema_valid` — complete and replayable metadata;
- `Q2_formally_verified` — final theorem or certified rejection;
- `Q3_semantically_reviewed` — expert confirms statement fidelity;
- `Q4_library_grade` — integrated or accepted by a maintained formal library.

Training releases must disclose tier composition.

## 5. Negative data

The Foundry retains:

- unsupported requests;
- missing assumptions;
- incorrect backend candidates;
- rejected certificates;
- translation defects;
- claim-strength mismatch;
- and agent tool-selection errors.

Synthetic negatives are labeled separately from naturally occurring failures.

## 6. Contamination controls

- immutable benchmark splits;
- source-date and repository-commit tracking;
- theorem equivalence and duplicate detection;
- separation of training and evaluation evidence;
- and explicit flags for results already present in public libraries.

## 7. Privacy and licensing

Private user sessions are excluded by default. Publication requires source license, solver artifact rights, and user consent where applicable. Sensitive mathematical work may contribute aggregate metrics without releasing content.

## 8. Pipelines

- capture;
- schema validation;
- replay;
- de-identification;
- deduplication;
- semantic review queue;
- quality scoring;
- split assignment;
- and release packaging.

## 9. Failure modes

- dataset dominated by trivial algebra;
- mislabeled semantic correctness;
- backend-specific shortcuts;
- contamination from existing proofs;
- unlicensed redistribution;
- or models learning to call tools excessively.

## 10. Acceptance criteria

1. Every `Q2+` episode replays.
2. Quality tiers are independently auditable.
3. Negative episodes improve failure diagnosis on held-out tasks.
4. Dataset use improves verified tool selection, not merely call frequency.
5. Releases include datasheets, licenses, benchmark exclusions, and known biases.
