# Product 5 — Trace-to-Plan Engine

## 1. Purpose

Trace-to-Plan converts external computational traces, transformations, and hints into structured proof plans that Lean agents can attempt. It improves medium-range mathematical planning without treating solver traces as trusted derivations.

## 2. Problem solved

A final CAS answer may hide the decomposition that made the result discoverable. Conversely, raw internal traces contain implementation details that do not correspond to useful mathematical lemmas. Agents need an intermediate representation distinguishing proof-relevant steps from search metadata.

## 3. Step taxonomy

Every trace item is classified as one of:

- `direct_proof_step` — has a stable inference meaning and can be reconstructed;
- `reconstructible_computation` — Lean can independently prove it through a checker or normalizer;
- `lemma_candidate` — a mathematically meaningful intermediate claim requiring proof;
- `search_hint` — substitution, decomposition, ordering, or strategy suggestion;
- `diagnostic_metadata` — performance or backend-internal information.

Only the first two categories can automatically advance formal proof status.

## 4. Proof-plan DAG

The output is a directed acyclic graph containing:

- target theorem;
- intermediate claims;
- dependencies;
- suggested tactics or capabilities;
- source trace references;
- confidence and status;
- and unresolved nodes.

Each node is either proved, checkable, proposed, rejected, or blocked.

## 5. Inputs

- Wolfram `ProofObject` through LeanLink;
- external SMT proof or hint data;
- Gröbner elimination artifacts;
- symbolic transformation sequences;
- recurrence discovery traces;
- and AI-generated plans.

## 6. Outputs

- Lean blueprint document;
- machine-readable plan DAG;
- generated intermediate theorem stubs;
- verified reconstructed steps;
- and foundry episode.

## 7. Non-goals

- reproducing every backend internal operation;
- trusting undocumented traces;
- generating unreadable tactic scripts merely to replay solver order;
- or requiring a trace for every certified computation.

## 8. Failure modes

- trace semantics unstable across backend versions;
- plan mirrors implementation instead of mathematics;
- excessive lemma fragmentation;
- cyclic plans;
- incorrect source-to-Lean mapping;
- and agent overreliance on low-confidence hints.

## 9. Acceptance criteria

1. Trace classifications are explicit and auditable.
2. Direct steps are independently reconstructed in Lean.
3. Hints never alter theorem status.
4. Plans improve success or human comprehension on multi-step tasks relative to final-answer-only baselines.
5. Generated lemma graphs remain mathematically coherent under expert review.
