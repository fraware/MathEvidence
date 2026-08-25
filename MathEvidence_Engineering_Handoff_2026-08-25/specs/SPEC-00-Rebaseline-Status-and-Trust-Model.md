# SPEC-00 — Rebaseline Status and Trust Model


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P0  
**Owner profile:** Technical lead / assurance platform  
**Blocks:** Trustworthy execution of all later specs

## Problem

Repository documentation contains strong historical completion labels that predate the exact-candidate-binding correction.
Without a new source of truth, engineers can correctly implement a checker yet incorrectly infer theorem-level promotion
authority.

## Objective

Create one authoritative, machine-readable capability/maturity inventory and make documentation, API policy, CI assertions,
and human status reports agree with it.

## Current state

- `docs/STATUS.md`, roadmaps, and historical acceptance artifacts document substantial completed work.
- PR #53 changes the semantics of what counts as sufficient theorem-level replay.
- `agent/api/receipt.py` now has fail-closed behavior for unavailable assurance modes.
- Several capabilities have Lean checker/soundness assets but no generic candidate-bound exact replay generator.

## Required maturity dimensions

Every capability/version MUST expose independently:

```text
adapter_exists
checker_exists
lean_soundness_exists
bridge_replay_exists
exact_candidate_binding_exists
offline_replay_exists
cr_eligible
```

Additional recommended fields:

```text
status_as_of_commit
known_limitations
trusted_backend
supported_assurance_modes
allowed_certification_outcomes
```

## Implementation requirements

1. Add a version-controlled capability status/assurance registry.
2. Record the pinned status of every capability currently exposed by adapters/API.
3. Add a validation script that rejects:
   - `cr_eligible=true` without exact binding where exact theorem assurance is claimed;
   - unsupported assurance modes;
   - missing checker/verifier identity for promotable modes;
   - duplicate capability/version keys;
   - stale or malformed schema versions.
4. Update current status docs to distinguish historical implementation completion from current assurance authority.
5. Add an Architecture Decision Record defining the exact-candidate-binding invariant.
6. Preserve historical audit files as historical records; do not rewrite old dated evidence to appear contemporaneously true.
7. Generate or validate user-facing capability tables from the registry to prevent drift.
8. Add CI that fails if documentation claims CR eligibility inconsistent with the registry.

## Non-goals

- independent human governance;
- external reproduction program;
- cryptographic organizational signing policy.

## Acceptance criteria

- [ ] Every adapter-exposed capability is present in the registry.
- [ ] Exact mode availability is derivable from registry fields.
- [ ] Historical `MET`-style claims are contextualized by date/scope.
- [ ] CI rejects an intentionally inconsistent `cr_eligible=true` mutation.
- [ ] CI rejects a capability claiming exact assurance without exact generator metadata.
- [ ] Current status documentation names PR #53/post-repair semantics.
- [ ] No live doc states or implies that fixture replay alone authorizes theorem certification.

## Failure modes to test

- stale copied capability ID;
- exact assurance added in adapter but omitted from registry;
- registry says exact supported but generator is missing;
- docs claim CR eligibility while registry blocks it;
- unknown capability/mode pair reaches Certification Record code.

## Definition of done

The repository has a single, auditable answer to: **"What can this capability prove/check today, and may that result produce a
Certification Record?"**
