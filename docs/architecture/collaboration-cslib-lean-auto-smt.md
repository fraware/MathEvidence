# Collaboration notes — CSLib, Lean-auto, Lean-SMT

Status: Milestone 4 working notes (not an RFC). MathEvidence adds
**interoperability metadata**; it does **not** replace specialized checkers.

See also: `docs/architecture/ecosystem-boundaries.md`.

## Shared contract

External projects that wish to interoperate SHOULD emit or consume
`schemas/federation-metadata.schema.json`:

- `claimClass` / `resultStatus` / `assuranceMode` from MathEvidence Core vocabulary
- `provenance.tool` identifying the producing stack
- `authority.checkerOwner = "external"` when their checker is authoritative
- `authority.mathEvidenceRole = "metadata_interop"` (default federation posture)

MathEvidence registry entries for federated capabilities use
`ownership: "federated"` and point `checker.package` at the external authority.

## CSLib

| Topic | MathEvidence posture |
| --- | --- |
| Verified algorithms | CSLib remains authoritative for its certified algorithm libraries |
| Generic interfaces | Prefer aligning serialization / formal-language generics after CSLib stabilizes (Product 01 note) |
| Near-term ask | Review federation metadata fields for provenance reuse; no checker fork |
| Contact path | Open a MathEvidence issue labeled `federation/cslib` with CSLib maintainer CC |

## Lean-auto / hammer tooling

| Topic | MathEvidence posture |
| --- | --- |
| Proof search | Lean-auto owns automation search |
| Evidence role | MathEvidence bundles are not substitutes for general proof search |
| Near-term ask | Accept optional consumption of federation metadata on reconstructed computational lemmas |
| Non-goal | Embedding Lean-auto search into MathEvidence TCB |

## Lean-SMT / SMT integrations

| Topic | MathEvidence posture |
| --- | --- |
| Reconstruction | Lean-SMT owns SMT proof reconstruction and trusted interfaces |
| Registry | Capability `logic.smt` is federated metadata only |
| Traces | SMT hints map to Trace-to-Plan as `search_hint` / `lemma_candidate` until reconstructed |
| Near-term ask | Emit federation metadata alongside existing proof objects so Studio / Agent can display shared status |

## Gröbner / SAT / pseudo-Boolean projects

Same rule as Lean-SMT: registry IDs
`algebra.groebner_membership`, `logic.sat_unsat`, `logic.pseudo_boolean`
declare discovery + shared status vocabulary. Certificate checking stays with the
specialized project.

## Simulated exit-gate integrations

Committed examples under `evidence/federation/examples/` demonstrate **two or
more** projects emitting and consuming the shared metadata envelope without live
process adapters. Live adapters land only after maintainer agreement.

**Current integration mode: `fixture_only`.** Upgrade checklist:
`evidence/federation/examples/UPGRADE_PATH.md`. Agreements ledger (empty until
real): `docs/architecture/federation-agreements.md`. Readiness board:
`docs/validation/p4-blocker-status.md`. Outreach: Emails 6–8 in
`docs/validation/outreach-email-templates.md`. Harness:

```text
python scripts/validate_federation.py
python scripts/run_federation_harness.py
```

## Proposed next steps (post M4)

1. RFC if federation vocabulary needs Core-level promotion beyond schemas.
2. Dual review with each external CODEOWNERS before any `supportLevel` upgrade.
3. Optional thin stdio adapters that only wrap metadata (still no checker fork).
4. Record agreements in the ledger; only then enable
   `MATHEVIDENCE_FEDERATION_LIVE=1` smoke (still no invented sign-off).
