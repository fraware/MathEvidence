# 01 — Target Architecture and Trust Boundary


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


## 1. Target product contract

MathEvidence should accept a mathematical claim plus evidence, validate that evidence at an explicitly declared assurance
class, retain reproducible artifacts, and—only where the exact candidate has passed the authorized trusted path—emit a
Certification Record whose scope and semantics can be independently replayed from the recorded bundle.

The architecture should make overclaiming structurally difficult.

## 2. End-to-end data flow

```text
Claim / Candidate / Evidence
          |
          v
[Canonical schema validation]
          |
          v
[Capability adapter + evidence checker]
          |
          +------------------------------+
          |                              |
          | lower assurance              | exact/theorem assurance requested
          v                              v
[Evidence result]              [Assurance capability registry]
                                         |
                              unsupported? -> FAIL CLOSED
                                         |
                                         v
                              [Typed exact replay IR]
                                         |
                                         v
                             [Deterministic Lean generator]
                                         |
                                         v
                               [Generated replay module]
                                         |
                                         v
                          [Pinned Lean/toolchain verification]
                                         |
                                         v
                              [Declaration/result identity]
                                         |
                                         v
                           [Certification policy evaluator]
                                         |
                                         v
                              [Certification Record]
                                         |
                                         v
                           [Offline replay bundle + audit]
```

## 3. Trusted-computing boundary

The exact trust boundary must be explicitly documented for each assurance mode.

For theorem-level Lean-backed certification, the trusted path includes at minimum:

- canonical input decoding/validation;
- the semantics-preserving translation from typed candidate IR to generated Lean;
- the pinned Lean kernel/toolchain and declared dependencies;
- the specific checker/theorem/declaration invoked;
- Certification Record canonicalization and binding logic.

Everything outside that path can be useful but does not independently authorize theorem-level promotion.

## 4. Capability maturity state machine

Recommended states:

```text
REGISTERED
  -> CHECKER_AVAILABLE
  -> FORMALLY_SPECIFIED
  -> BRIDGE_REPLAY_AVAILABLE
  -> EXACT_REPLAY_AVAILABLE
  -> OFFLINE_REPLAY_VERIFIED
  -> CR_ELIGIBLE
```

These states are not purely linear in implementation order, so store the underlying booleans/metadata and derive the display
state. `CR_ELIGIBLE` must be a computed policy result, not a manually asserted marketing label.

## 5. Machine-readable assurance registry

One version-controlled registry should describe each capability/version:

```yaml
capability_id: algebra.rational_equality
capability_version: "..."
evidence_class: exact
checker:
  id: "..."
  version: "..."
lean:
  module: MathEvidence.Assurance.RationalEquality
  declaration: "..."
supported_assurance_modes:
  - evidence_check
exact_binding:
  supported: false
  generator_id: null
  generator_version: null
  grammar_version: null
replay:
  backend: lean
  offline_supported: false
certification:
  allowed_outcomes: []
  cr_eligible: false
limitations:
  - "Exact theorem certification unavailable until candidate-bound generator ships."
```

Once an exact implementation lands, the same record changes through review; callers do not hard-code policy independently.

## 6. Exact replay intermediate representation

The generator layer should consume a typed, canonical internal representation (IR), never arbitrary Lean strings.

Properties:

- fully schema-validated;
- deterministic normalization;
- semantic domain explicit (integer, rational, finite structure, formal rational expression, etc.);
- no implicit float-to-exact coercions;
- size/depth limits before rendering;
- operation discriminants explicit;
- all hypotheses/side conditions explicit;
- canonical digest computable before code generation.

## 7. Certification Record contract

A record must bind the claim and the verification event strongly enough that substitution is detectable. Required fields are
specified in SPEC-08, including:

- canonical claim/candidate hash;
- capability and version;
- evidence and assurance class;
- checker/verifier identity;
- generator and grammar identity;
- generated source hash;
- theorem/declaration identity;
- toolchain/dependency lock digest;
- artifact hashes;
- replay manifest hash;
- result polarity (`proved`, `refuted`, etc.).

## 8. Reproducibility target

For a fixed canonical candidate, generator version, and pinned toolchain/dependency closure:

- generated replay source is deterministic;
- bound hashes are deterministic;
- clean replay produces the same logical result;
- offline replay works after required dependencies are materialized;
- mutation of any bound semantic artifact causes replay or identity validation to fail.

## 9. Evidence-class honesty

The architecture should make lower-assurance evidence first-class. This is important: numerical checks, heuristic search,
symbolic computation, sampling, and benchmark performance can be valuable without being theorem proofs.

The target is not "make every capability theorem-certified." The target is "make the assurance label exactly match what was
verified."
