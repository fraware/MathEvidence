# Standalone specification — Evidence Bundle v0.3, certification records, and content storage


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Objective

Make evidence artifacts immutable, collision-safe, role-complete, and independently verifiable. Remove all theorem and axiom placeholders.

## Artifact split

### Candidate Bundle

A Candidate Bundle contains untrusted computation inputs and outputs:

- `request.cjson`
- `candidate.cjson`
- `certificate.cjson`
- `provenance.cjson`
- `manifest.cjson`

It contains no theorem, checker receipt, or axiom report. Its manifest status is `computed`.

### Certification Record

A Certification Record references one Candidate Bundle and contains:

- `replay-target.cjson`
- `checker-evaluation.cjson`
- `theorem-identity.cjson`
- `axiom-report.cjson`
- `certification-receipt.cjson`
- optional `signature.cjson`
- `manifest.cjson`

It contains the actual theorem declaration identity and environment evidence. It does not mutate the Candidate Bundle.

## Bundle digest

Define:

```text
bundleDigest = SHA256(JCS(manifestBindingPayload))
```

`manifestBindingPayload` includes:

- schema version;
- capability and version;
- request digest;
- claim requested;
- sorted role entries;
- each role path, media type, and content digest;
- backend provenance digest;
- resource policy digest.

It excludes only the `bundleDigest` field itself and any external signature envelope.

The complete directory identity is the canonical manifest digest. The manifest MUST list every file except itself. Unknown unlisted files MUST cause strict verification failure in release mode.

## Certification digest

Define the certification-record digest analogously over its canonical manifest. It binds:

- candidate bundle digest;
- replay target digest;
- checker evaluation digest;
- theorem identity digest;
- axiom report digest;
- certification receipt digest;
- environment lock digest.

## Role rules

Candidate Bundle mandatory roles:

- exactly one request;
- exactly one candidate;
- exactly one certificate;
- exactly one provenance.

Certification Record mandatory roles:

- exactly one replay target;
- exactly one checker evaluation;
- exactly one theorem identity;
- exactly one axiom report;
- exactly one certification receipt.

The verifier MUST reject duplicate roles even when paths differ.

## Remove placeholders

Delete `_default_theorem_lean` and `_default_axiom_report` from `adapters/common/bundle.py`.

Migration rules:

- Existing `theorem.lean` files declaring `mathevidence_bundle_theorem_placeholder : True` are discarded during v0.3 migration.
- Existing axiom reports with `pending_compiled_audit` are discarded.
- Existing bundles without a real certification record remain Candidate Bundles.
- Existing verified statuses are downgraded to `computed` unless a new kernel replay creates a Certification Record.

## True content-addressed store

Replace request-digest addressing with bundle-digest addressing.

Required directory layout:

```text
evidence/store/bundles/sha256/ab/<remaining-62-hex>/
evidence/store/certifications/sha256/cd/<remaining-62-hex>/
evidence/store/index/by-request/<request-hex>.cjson
```

The request index stores an ordered set of bundle digests. Multiple backends or regenerations for the same request are permitted.

`commit_content_addressed` MUST:

1. fully verify the source artifact;
2. compute the bundle digest;
3. copy to a temporary directory on the same filesystem;
4. fsync files and directory where supported;
5. atomically rename to the final digest path;
6. if the path exists, compare every listed byte and manifest;
7. return success only for byte-identical content;
8. raise `content_address_collision` for any difference.

It MUST never let an existing directory win silently.

## Receipt schema v0.3

Required fields for a verified certification receipt:

- `schemaVersion`
- `candidateBundleDigest`
- `certificationRecordDigest`
- `requestDigest`
- `certificateContentDigest`
- `replayTargetDigest`
- `theoremTypeDigest`
- `proofDeclarationDigest`
- `axiomReportDigest`
- `environmentLockDigest`
- `capability`
- `checker`
- `soundnessTheorem`
- `claimRequested`
- `claimEstablished`
- `unresolvedObligations`
- `assuranceMode`
- `resultStatus`
- `toolchain`

Coherence rules:

- verified result requires non-null `claimEstablished`;
- `kernel_replay` requires theorem and proof declaration digests;
- `native_checked` requires an operational-base declaration and may not report `soundness_verified`;
- unresolved obligations prevent a verified status unless the claim class explicitly permits obligations;
- `claimEstablished` may not exceed `claimRequested`;
- certificate and candidate bundle digests must recompute;
- theorem and axiom report digests must recompute;
- environment lock must match the replay environment.

## Signatures

Local kernel replay may produce an unsigned certification record whose integrity is established by local content hashes. Remote distribution requires an Ed25519 signature from a configured release or federation key.

HMAC is limited to tests. It MUST be excluded from release trust policies.

Unsigned self-digests are integrity metadata. They are not proof of origin. Studio may display local certification only after the full record is verified locally.

## Agent API behavior

- Write operations return bundle IDs, never filesystem paths.
- Open operations resolve IDs inside configured stores.
- `open_bundle` returns `computed` for a Candidate Bundle.
- `open_certification` returns verified status only after complete record verification.
- `replay_bundle` creates a new Certification Record; it never writes into the Candidate Bundle.
- Candidate and certification IDs are different types in API schemas.

## Migration

Implement `scripts/migrate_bundles_v03.py`.

For each v0.2 directory:

1. verify all listed content bytes;
2. classify files;
3. remove generated placeholder theorem/axiom artifacts from the migrated representation;
4. create a Candidate Bundle;
5. create a Certification Record only when real theorem and compiled axiom artifacts can be regenerated;
6. record legacy source path and digest in migration provenance;
7. emit a machine-readable migration report;
8. refuse ambiguous or invalid bundles.

Do not retain duplicate `.json` and `.cjson` files in new artifacts.

## Tests

- Same request, different backend certificates produce distinct bundle IDs.
- Recommitting identical bytes is idempotent.
- Existing-path different-byte collision rejects.
- Extra unlisted file rejects in strict mode.
- Duplicate role rejects.
- Candidate Bundle cannot contain a verified status.
- Certification Record cannot exist without a real theorem identity and axiom report.
- Placeholder theorem and pending axiom report are detected and rejected.
- Path traversal, symlink escape, hard-link substitution, race during commit, and case-folding collisions are tested.
- Windows and POSIX path behavior is covered.
- Migration is deterministic.

## Acceptance

No file named as a theorem or axiom report may contain placeholder content. No content address may be derived from request digest. A verified status must be reproducible from one immutable Candidate Bundle and one immutable Certification Record.
