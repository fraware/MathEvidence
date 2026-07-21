# Threat Model Summary

This document summarizes `docs/security/SECURITY_AND_TRUST_MODEL.md` for the
`docs/threat-model/` tree. Detailed controls remain normative in that file.
See also [`../security/README.md`](../security/README.md).

## Objective

Untrusted solvers, adapters, agents, and evidence files may fail arbitrarily.
Failure must not authorize a false Lean theorem or compromise the host.

## Primary assets

- Theorem correctness and semantic fidelity of encodings.
- Evidence integrity and replayability.
- CI / developer host availability.
- Private mathematics, solver credentials, release keys, dataset provenance.

## Trust-boundary invariants (abbrev.)

1. Backends never create Lean declarations in a trusted environment.
2. Output is data, checked against the exact request digest.
3. Final theorems follow Lean soundness proofs, not backend status codes.
4. Replay CI disables external backends.
5. No project `sorry` / forbidden axioms; no silent claim-strength promotion.
6. Parsers and checkers are size-bounded; credentials stay out of bundles.

## Boundary sketches

| Boundary | Threats | Mitigations |
| --- | --- | --- |
| Adapter process | RCE, resource exhaustion, path escape | stdio JSON-RPC, limits, no shell, cwd jail |
| Evidence parser | Hostile JSON/binary, hash mismatch | strict schema, digests first, fuzz |
| LeanLink / native | Memory corruption, WXF malice | isolation, fuzz, outside TCB |
| Supply chain | Dependency compromise | pins, review, signed releases |
| Foundry | Privacy / license leakage | opt-in, review before publish |

## Incident priority

Checker soundness and request-binding defects are critical: withdraw capability,
repro, patch, revalidate evidence, postmortem.

Expand per-boundary analyses in this directory as implementations land.
