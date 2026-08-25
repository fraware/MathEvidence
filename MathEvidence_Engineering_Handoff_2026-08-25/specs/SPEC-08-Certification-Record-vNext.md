# SPEC-08 — Certification Record vNext: Strong Claim, Replay, and Toolchain Binding


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1 foundation  
**Depends on:** SPEC-00/02 interface; coordinated with SPEC-03  
**Owner profile:** API/schema/reproducibility engineer

## Objective

Make a Certification Record sufficient to identify exactly **what was certified, by which capability/verifier/generator,
under which toolchain/dependency closure, with which replay artifacts and logical outcome.**

## Required logical fields

Use project naming conventions, but bind at least:

```text
schema_version
claim_id
canonical_claim_hash
candidate_hash
capability_id
capability_version
evidence_class
assurance_mode
result/outcome
checker_id
checker_version
verifier_backend
verifier_version
generator_id
generator_version
grammar_version
generated_source_hash
theorem_or_declaration_identity
toolchain_contract_digest
dependency_lock_digest
artifact_hashes
replay_manifest_hash
execution_policy_id
provenance
```

If some fields are non-applicable for a non-Lean evidence class, represent that explicitly; do not fill with misleading
pseudo-values.

## Canonicalization

- Define one canonical serialization for record identity/hashing.
- Exclude ephemeral fields (display timestamps, local paths) from semantic digest or define their role explicitly.
- Sort maps/sets deterministically.
- Version the canonicalization format.
- Ensure candidate/claim hashes are over canonical semantic representations, not unstable transport formatting.

## Result polarity

Represent semantic outcomes explicitly. At minimum distinguish:

- `proved` / verified true proposition;
- `refuted` / verified counterexample or false proposition;
- evidence-only/check result where no theorem assurance exists.

Do not overload a single boolean.

## Legacy migration

Existing records created under fixture-backed or weaker semantics MUST NOT be silently upgraded.

Required approach:

- parse legacy schema under its original version;
- map its assurance to an explicitly legacy/lower class where exact binding cannot be established;
- never synthesize a missing exact candidate hash/generator identity and call it equivalent;
- provide migration/read compatibility without semantic inflation.

## Verification API

Provide a function/process that validates a record against its replay bundle:

1. canonical record integrity;
2. candidate/claim hash;
3. artifact hashes;
4. registry capability/version;
5. generator/version;
6. generated source;
7. verifier/declaration identity;
8. toolchain/dependency contract;
9. replay result/outcome.

## Tests

- round-trip serialization;
- deterministic digest;
- field-by-field tamper tests;
- legacy record read;
- legacy record attempted exact upgrade -> reject;
- generator version mismatch;
- dependency lock mismatch;
- candidate hash mismatch;
- result polarity mismatch.

## Acceptance criteria

- [ ] CR schema version advanced where needed.
- [ ] Candidate/claim identity is mandatory for exact promotion.
- [ ] Generator, verifier/declaration, toolchain, and dependency identities are bound.
- [ ] Outcome polarity is explicit.
- [ ] Canonical serialization is deterministic.
- [ ] Legacy fixture-backed records cannot become exact by migration.
- [ ] Record verifier detects semantic tampering.
- [ ] Registry capability/version is recorded and checked.
- [ ] Governance/signature fields may be reserved, but no unimplemented signing guarantee is claimed.

## Definition of done

A Certification Record is an auditable binding between one exact mathematical proposition/candidate and one reproducible
verification event, not just a success receipt.
