# Standalone specification — Agent API and Studio


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Objective

Ensure public surfaces expose exact epistemic status derived from immutable artifacts and kernel verification.

## Agent API

### IDs only

Public responses MUST return:

- `candidateBundleId`;
- `certificationRecordId`;
- request digest;
- capability and version.

They MUST NOT return local filesystem paths.

### Operation split

Expose:

- `compute_evidence` — returns candidate bundle, status `computed`;
- `verify_bundle` — returns checker evaluation, status `checker_accepted` or `rejected`;
- `kernel_replay` — returns certification record, verified status;
- `open_bundle`;
- `open_certification`;
- `list_certifications_for_request`.

`replay_bundle` should become an alias to `kernel_replay` only after the real kernel path exists.

### Registry-derived routing

Generate dispatch metadata from registry entries. Remove `_COMPUTE_CAPABILITIES` as a second hand-maintained source.

The runtime must verify that an adapter module actually exposes the declared capability/version.

### Receipt verification

`trusted_status_from_receipt` is replaced by `verify_certification_record`.

It must verify:

- candidate bundle digest;
- certification-record digest;
- all role content digests;
- theorem type and declaration digests;
- axiom report;
- environment lock;
- claim/result coherence;
- optional signature policy.

Certificate content alone is insufficient.

### Errors

Use stable machine errors and preserve domain-specific causes. Never map arbitrary exceptions to malformed evidence without a diagnostic cause chain.

## Studio

### Certified gate

Studio may render Certified only when the Agent returns:

```json
{
  "certificationVerified": true,
  "certificationRecordId": "...",
  "claimEstablished": "...",
  "resultStatus": "...",
  "theoremType": "...",
  "assumptions": [...]
}
```

A raw receipt object is never sufficient.

### Local mode

Local Studio may verify a certification record directly only through the same shared verifier used by Agent. Structural receipt checks can support diagnostics but must yield `Tested` or `Ambiguous`.

### Display requirements

The certification surface must display, in order:

1. exact original Lean proposition;
2. imported environment and source revision;
3. assumptions and unresolved obligations;
4. candidate bundle and backend provenance;
5. checker and soundness theorem;
6. theorem declaration and axiom report;
7. epistemic status.

### Mutation and refresh

Studio must detect when:

- a bundle has changed;
- a certification record no longer matches;
- the Lean environment lock changed;
- a theorem source changed.

Any mismatch immediately removes Certified status.

### Human usability

Run at least three sessions with external Lean users. Record:

- whether users distinguish Computed, Checker Accepted, and Certified;
- whether assumptions are noticed;
- whether users can locate the theorem and axiom report;
- whether stale certification is understood;
- observed defects and remediation.

## Security tests

- forged unsigned receipt;
- valid self-digest with false claim;
- certificate byte substitution;
- theorem byte substitution;
- bundle ID collision;
- stale environment lock;
- path injection in display fields;
- oversized proposition;
- Unicode spoofing in declaration names;
- revoked federation key.

## Acceptance

No public API or Studio code path may derive Certified from manifest status, executable success, Python mirror acceptance, or receipt structure alone.
