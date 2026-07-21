# Project status (public preview)

**Branch / preview:** `engineering-closure` public preview  
**Capability status:** all registry capabilities remain **`experimental`**  
**Authoritative limitations:** [`KNOWN_TRUST_GAPS.md`](../KNOWN_TRUST_GAPS.md)

This page is the short, honest status for outsiders. Detailed §21 / milestone
mapping lives in [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md).

## What this preview is

An **experimental** computational-evidence platform for Lean: protocol,
semantic IR, verified checkers, untrusted adapters, Agent API, Studio surfaces,
registry, Foundry schemas/corpus samples, and offline evidence bundles.

It is **not**:

- a stable computational-evidence layer;
- a claim that human gates (external confirmations, dual-area review, live
  federation, usability studies) are complete;
- attested immutable CI green on a tagged release commit.

## Engineering highlights in this preview

| Area | Status |
| --- | --- |
| Request binding / offline digest recompute | Engineering fixes present; guarded by `tests/forensic/` |
| Theorem-producing rational replay | `mathevidence-replay` path for rational equality with content-bound receipt |
| Agent API | **v0.1.0**; open/inspect/replay by opaque **`bundleId` only** (no public path API) |
| Evidence Bundle schema | **v0.2** (`.cjson`); dual-read retained |
| Calculus capability ID | `algebra.formal_rational_calculus` (formal rational calculus only) |
| CODEOWNERS | Single-owner incubation stub — see `GOVERNANCE.md` |

## Not yet

- Live federation with external projects (fixtures only).
- Human gates ME-style confirmations, expert signatures, Studio session results.
- Lean toolchain bump beyond the committed pin.
- `"status": "stable"` on any capability.
- Production receipt PKI.

## How to build and test

See [`README.md`](../README.md). Typical local gate: `just check` (Lean build,
schema/registry validation, Python tests, conformance, replay, and related
harnesses). Forensic subset:

```text
pytest tests/forensic -q
```

Workflow definitions: `.github/workflows/`. Do not treat local green alone as
promotion evidence.

## Related docs

| Doc | Role |
| --- | --- |
| [`KNOWN_TRUST_GAPS.md`](../KNOWN_TRUST_GAPS.md) | Known limitations / trust gaps |
| [`validation/stable-capability-checklist.md`](validation/stable-capability-checklist.md) | Only path to `stable` |
| [`validation/remaining-spec-matrix.md`](validation/remaining-spec-matrix.md) | §21 / milestone honesty matrix |
| [`RELEASE_NOTES_DRAFT.md`](RELEASE_NOTES_DRAFT.md) | Public-preview release notes draft |
| [`PROJECT_SPEC.md`](PROJECT_SPEC.md) | Normative specification |
