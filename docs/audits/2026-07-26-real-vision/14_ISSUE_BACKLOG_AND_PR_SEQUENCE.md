# Standalone issue backlog and pull-request sequence


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Execution rule

Open one GitHub issue per item below. Copy the full specification for that item into the issue. Each PR must name exactly one primary issue, preserve green required checks, and contain no unrelated product expansion.

## Wave 0 — Correct public assurance claims

### ME-RV-001 — Downgrade standalone replay assurance

Priority: P0  
Depends on: none

Implement:

- rename current executable behavior to bundle verification;
- emit `native_checked`/`checker_accepted`;
- remove `kernel_replay`, `soundness_verified`, and `claimEstablished`;
- update Agent, Studio, tests, docs, and status matrix;
- preserve rejection behavior.

Acceptance:

- no current executable path can emit theorem-level status;
- forensic test asserts this;
- public documentation matches.

### ME-RV-002 — Remove theorem and axiom placeholders

Priority: P0  
Depends on: none

Implement:

- delete default placeholder writers;
- reject placeholder roles;
- regenerate/migrate examples as candidate-only;
- downgrade verified statuses lacking real certifications.

Acceptance:

- repository search finds no `mathevidence_bundle_theorem_placeholder`;
- no release artifact contains `pending_compiled_audit`;
- bundle tests pass.

### ME-RV-003 — Freeze stable promotion and record current CI truth

Priority: P0  
Depends on: none

Implement:

- add machine-readable CI status record for current head;
- require PRs and checks;
- update status docs;
- create actual issue labels/milestones.

Acceptance:

- exact commit has complete green checks;
- branch protection report committed;
- stable remains blocked.

## Wave 1 — Artifact identity

### ME-RV-010 — Evidence Bundle v0.3 Candidate Bundle

Priority: P0  
Depends on: ME-RV-002

Implement candidate/certification split, role enum, strict manifest, true bundle digest, and migration.

### ME-RV-011 — True content-addressed store

Priority: P0  
Depends on: ME-RV-010

Implement bundle-digest keys, atomic commit, collision rejection, and request index.

### ME-RV-012 — Certification Record and receipt v0.3

Priority: P0  
Depends on: ME-RV-010

Implement complete digest and coherence verification.

### ME-RV-013 — Migrate repository evidence

Priority: P0  
Depends on: ME-RV-010, ME-RV-012

Migrate all examples, conformance fixtures, Agent smoke bundles, and store objects. Produce deterministic report.

## Wave 2 — Real kernel replay

### ME-RV-020 — Replay target and theorem identity

Priority: P0  
Depends on: ME-RV-012

Implement elaborated theorem identity, environment lock, and digest vectors.

### ME-RV-021 — Bundle verifier executable

Priority: P0  
Depends on: ME-RV-010

Refactor current executable into strict operational verifier.

### ME-RV-022 — Rational kernel replay

Priority: P0  
Depends on: ME-RV-020, ME-RV-021

Generate/elaborate theorem, apply checker soundness, query axioms, emit Certification Record.

### ME-RV-023 — Rational tactic proof authority

Priority: P0  
Depends on: ME-RV-022

Refactor tactic to apply soundness theorem to current goal; remove independent final proof authority.

### ME-RV-024 — Agent and Studio certification gate

Priority: P0  
Depends on: ME-RV-012, ME-RV-022

Consume only verified Certification Records.

## Wave 3 — Flagship ideal membership

### ME-RV-030 — Fixed-arity sparse polynomial IR

Priority: P0  
Depends on: Wave 2

Implement typed monomials, normalization, resource bounds, codecs.

### ME-RV-031 — Sparse polynomial interpretation and soundness

Priority: P0  
Depends on: ME-RV-030

Prove arithmetic/normalization semantics into Mathlib polynomial structures.

### ME-RV-032 — Ideal-membership request, checker, and soundness

Priority: P0  
Depends on: ME-RV-031

Prove checker acceptance implies Mathlib ideal membership.

### ME-RV-033 — Proof-producing polynomial reifier

Priority: P0  
Depends on: ME-RV-031

Return interpretation equality proofs.

### ME-RV-034 — External-search ideal tactic

Priority: P0  
Depends on: ME-RV-032, ME-RV-033

Route to SymPy/Sage/Mathematica, check witness, apply soundness.

### ME-RV-035 — Correct ideal benchmark

Priority: P0  
Depends on: ME-RV-032

Score proposed witness and theorem certification. Add realistic held-out set.

### ME-RV-036 — Capability rename and RFC update

Priority: P1  
Depends on: ME-RV-032

Rename to ideal-membership witness or implement genuine Gröbner certificate semantics.

## Wave 4 — Cross-domain theorem production

### ME-RV-040 — Linear algebra reifier bridge

Priority: P1  
Depends on: Wave 2

### ME-RV-041 — Linear algebra kernel replay

Priority: P1  
Depends on: ME-RV-040

### ME-RV-042 — Finite predicate reifier bridge

Priority: P1  
Depends on: Wave 2

### ME-RV-043 — Counterexample kernel replay

Priority: P1  
Depends on: ME-RV-042

## Wave 5 — Analytic calculus

### ME-RV-050 — Analytic interpretation and domain obligations

Priority: P1

### ME-RV-051 — Derivative derivation certificate

Priority: P1  
Depends on: ME-RV-050

### ME-RV-052 — Inductive `HasDerivAt` soundness

Priority: P1  
Depends on: ME-RV-051

### ME-RV-053 — ODE candidate certificate

Priority: P1  
Depends on: ME-RV-052

### ME-RV-054 — Analytic adapter, reifier, and kernel replay

Priority: P1  
Depends on: ME-RV-053

## Wave 6 — Product epistemology

### ME-RV-060 — Hypothesis preview/certified states

### ME-RV-061 — Conjecture certified transitions

### ME-RV-062 — Trace-to-Plan proof evidence

All depend on ME-RV-024.

## Wave 7 — Reproducibility and release

### ME-RV-070 — Frozen Python dependencies

### ME-RV-071 — Environment import audit

### ME-RV-072 — Environment axiom audit

### ME-RV-073 — Complete required CI

### ME-RV-074 — Signed experimental release

ME-RV-074 depends on all P0 items.

## Wave 8 — Foundry, federation, and governance

### ME-RV-080 — Reclassify Foundry Q2

### ME-RV-081 — Held-out external benchmark

### ME-RV-082 — Live federation peer one

### ME-RV-083 — Live federation peer two

### ME-RV-084 — Real maintainer teams and CODEOWNERS

### ME-RV-085 — External user validation

### ME-RV-086 — External project adoption

### ME-RV-087 — Candidate promotion record

## Recommended PR order

1. PR-A claim correction and placeholders.
2. PR-B Candidate Bundle v0.3.
3. PR-C content store.
4. PR-D Certification Record.
5. PR-E theorem identity.
6. PR-F rational kernel replay.
7. PR-G Agent/Studio gate.
8. PR-H typed polynomial IR.
9. PR-I polynomial interpretation and checker soundness.
10. PR-J ideal tactic.
11. PR-K ideal benchmark.
12. PR-L cross-domain bridges.
13. PR-M analytic checker.
14. PR-N product state corrections.
15. PR-O reproducibility and CI.
16. PR-P experimental release.
17. Separate human/adoption PRs.

No later wave may block correction of an overclaim in Wave 0.
