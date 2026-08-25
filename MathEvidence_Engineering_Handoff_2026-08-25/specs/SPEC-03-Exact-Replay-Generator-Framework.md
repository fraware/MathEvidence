# SPEC-03 — Generic Exact Candidate-Bound Replay Generator Framework


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1 foundation  
**Depends on:** SPEC-01, SPEC-02  
**Reference implementation:** existing exact ideal-membership generator

## Problem

Exact replay must prove/check the submitted candidate, not a fixture with similar shape. Implementing each capability through
unstructured one-off source templates risks code injection, inconsistent canonicalization, and drift in what is actually
bound to the Certification Record.

## Objective

Create a generic framework that converts a validated, canonical candidate into a deterministic typed replay IR, renders a
Lean module, verifies it with the pinned backend, and returns strongly bound replay metadata.

## Pipeline

```text
raw candidate
  -> schema validation
  -> canonical semantic object
  -> typed replay IR
  -> deterministic renderer
  -> generated Lean source
  -> source hash + manifest
  -> pinned Lean build/replay
  -> declaration/result identity
  -> certification metadata
```

## Required interfaces

Conceptually separate:

- `parse_and_validate(candidate) -> CanonicalCandidate`
- `to_replay_ir(canonical) -> ReplayIR`
- `render(ir, generator_version) -> GeneratedModule`
- `verify(module, toolchain_contract) -> VerificationResult`
- `bind(result, canonical, module, manifest) -> AssuranceEvidence`

Use actual project naming conventions in implementation.

## Generator requirements

- deterministic byte output for the same canonical input/version;
- no timestamps, random IDs, machine paths, or nondeterministic ordering in generated source;
- typed constructors for every Lean syntax fragment derived from untrusted inputs;
- no direct insertion of arbitrary caller-provided Lean code;
- explicit bounds on expression depth, collection dimensions, integer/rational sizes, and generated source size;
- canonical module naming derived from digest or controlled identifier;
- explicit generator/grammar version;
- semantic candidate digest embedded/bound in manifest;
- renderer output hash recorded before verification.

## Canonicalization rule

Canonicalization may normalize representation but MUST preserve semantics and be specified per capability. Examples:

- rational denominator sign normalized;
- map/object keys sorted;
- equivalent whitespace not semantically relevant;
- floating-point values never silently converted into exact rationals for theorem assurance.

## Migrate ideal membership

Refactor the existing exact ideal-membership generator to use the common framework without changing its mathematical
obligation. This migration is the framework conformance test.

## Security requirements

- no shell interpolation;
- path-safe generated filenames;
- isolated working directory;
- bounded input and generated output;
- bounded verification process;
- reject unsupported syntax before Lean execution.

## Tests

- golden source tests;
- determinism across repeated runs;
- canonical-equivalence tests where mathematically justified;
- semantic mutation tests;
- malicious string/path/metacharacter tests;
- oversized/deep input tests;
- generator-version mismatch tests;
- toolchain mismatch tests.

## Acceptance criteria

- [ ] Ideal-membership exact generator is implemented through the framework.
- [ ] Same candidate/version yields byte-identical generated source.
- [ ] Different semantic candidate yields different canonical/source binding.
- [ ] No raw untrusted Lean fragment API exists.
- [ ] Verification result returns declaration/result identity.
- [ ] Manifest contains candidate, generator, source, verifier, and toolchain bindings.
- [ ] Malformed/oversized/injection-shaped inputs fail before trusted verification.
- [ ] Framework has a capability plugin interface sufficient for SPEC-04–07.
- [ ] Security/adversarial CI stays green.

## Definition of done

Adding a new exact assurance capability becomes a small, typed semantic translation plus tests—not a new ad hoc replay
architecture.
