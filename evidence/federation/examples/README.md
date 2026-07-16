# Federation examples (Milestone 4)

Simulated emit/consume payloads for shared provenance + claim-status metadata.
These satisfy the Milestone 4 exit gate (≥2 external projects consume or emit
shared metadata) without claiming live process integration.

## Files

| File | Project | Role |
| --- | --- | --- |
| `lean_smt_emit.json` | lean-smt | emitter |
| `cslib_consume.json` | cslib | consumer |
| `groebner_emit.json` | groebner-cert | emitter |
| `sat_emit.json` | sat-checker | emitter |
| `pb_emit.json` | pb-checker | emitter |
| `lean_smt_request.json` | lean-smt | federated request wrapper |
| `lean_smt_certificate.json` | lean-smt | federated certificate wrapper |

## Validate

```text
python scripts/validate_federation.py
```

Schemas: `schemas/federation-metadata.schema.json` and related federation schemas.
Collaboration: `docs/architecture/collaboration-cslib-lean-auto-smt.md`.

## Conformance notes (simulated adapters)

These JSON files are **metadata-only** fixtures. They demonstrate emit/consume
shapes for lean-smt, CSLib, and related tools. They do **not** assert that
external maintainers have signed off, nor that live stdio adapters exist.

Harness expectations enforced by `validate_federation.py`:

1. ≥2 distinct project IDs
2. ≥1 emitter and ≥1 consumer role
3. Required roles for `lean-smt` (emitter) and `cslib` (consumer)
4. Schema validation for every example file

When a real external adapter lands, add a live smoke under an env gate and keep
these fixtures as the offline contract.
