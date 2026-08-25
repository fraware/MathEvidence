# SPEC-02 — Assurance Capability Registry and Fail-Closed Policy


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** P1 foundation  
**Depends on:** SPEC-00 interface decisions  
**Owner profile:** Platform/API + assurance engineer

## Problem

Assurance availability and promotion policy are currently too easy to distribute across adapters, replay profiles, receipt
logic, and docs. Distributed policy creates semantic drift.

## Objective

Make one typed registry the authoritative source for capability assurance modes, exact replay support, trusted verifier
identity, replay backend, and CR eligibility.

## Proposed schema

Use the repository's existing configuration conventions, but represent at least:

```yaml
schema_version: 1
capability_id: algebra.ideal_membership
capability_version: "..."
evidence_class: exact
checker:
  id: "..."
  version: "..."
lean:
  module: "..."
  declaration: "..."
supported_assurance_modes:
  - evidence_check
  - exact_replay
exact_binding:
  supported: true
  generator_id: "..."
  generator_version: "..."
  grammar_version: "..."
replay:
  backend: lean
  offline_supported: true
certification:
  allowed_outcomes:
    - proved
  cr_eligible: true
limitations: []
```

Do not invent a generic exact mode for capabilities that lack a generator.

## Policy rules

1. Unknown capability => no Certification Record.
2. Unknown assurance mode => `assurance_mode_unavailable`.
3. Exact requested + `exact_binding.supported=false` => fail closed.
4. No fallback from exact to fixture/bridge mode.
5. `cr_eligible=true` is valid only when required exact/verifier metadata exists.
6. Certification outcome must be in `allowed_outcomes`.
7. Capability/version is immutable in an issued record.
8. Registry changes that increase assurance are security-sensitive review changes.

## Integration points

- `agent/api/receipt.py`: query registry instead of ad hoc mapping.
- replay selection: resolve generator/backend from registry.
- adapter introspection: expose supported assurance modes from registry.
- docs/status generation: consume registry.
- tests: parameterize supported/unsupported combinations from registry.
- Certification Record: record registry capability/version and resolved verifier/generator IDs.

## Migration

1. Build registry reflecting the current conservative state.
2. Add read-only policy lookup while retaining old behavior behind assertions.
3. Run differential tests; any disagreement must be investigated.
4. Switch receipt/replay policy to registry.
5. Remove duplicate hard-coded authority mappings.
6. Add CI preventing reintroduction.

## Acceptance criteria

- [ ] All current capabilities represented.
- [ ] Registry schema validation runs in CI.
- [ ] `receipt.py` exact-mode decision is registry-driven.
- [ ] Unsupported exact modes return a stable fail-closed status.
- [ ] No silent downgrade exists.
- [ ] Duplicate IDs/versions rejected.
- [ ] Registry cannot mark CR eligible without verifier/generator metadata.
- [ ] Docs/status table is generated from or mechanically checked against registry.
- [ ] One test mutating a blocked capability to request exact assurance demonstrably fails.

## Definition of done

Assurance authority is explicit, centralized, versioned, and machine-enforced.
