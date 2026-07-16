# Security and Trust Model

## 1. Security objective

Untrusted solvers, adapters, AI agents, and evidence files may fail arbitrarily. Their failure must not authorize a false Lean theorem or compromise the host environment.

## 2. Assets

- theorem correctness;
- semantic fidelity of encodings;
- integrity of evidence bundles;
- availability of CI and developer machines;
- private user mathematics;
- proprietary solver credentials and licenses;
- release signing keys;
- and dataset provenance.

## 3. Threat actors and failure sources

- accidental adapter defects;
- malicious evidence files;
- compromised backend binaries;
- prompt-injected AI agents;
- denial-of-service certificates;
- parser vulnerabilities;
- dependency supply-chain compromise;
- and repository contributors attempting to weaken assurance checks.

## 4. Trust-boundary invariants

1. Backends never create Lean declarations directly in a trusted environment.
2. Backend output is decoded into data and checked against the exact request.
3. Every certificate is cryptographically bound to the request digest.
4. The final theorem follows from a Lean soundness theorem, not a backend status code.
5. Replay CI disables all external backends.
6. Project-specific axioms and `sorry` are rejected.
7. Claim-strength promotion requires an explicit Lean theorem.
8. Approximate evidence cannot enter an exact checker.
9. Parser and checker inputs are bounded.
10. Adapter credentials are absent from evidence bundles.

## 5. Process isolation

- Backend processes run with explicit time, CPU, memory, and output limits.
- Network access is denied unless a capability explicitly requires it; stable theorem generation SHOULD avoid network dependence.
- Adapters receive an isolated working directory.
- Environment variables are allow-listed.
- Shell command construction is prohibited.
- Generated paths are normalized and contained under the workspace.

## 6. Evidence parser security

- Maximum nesting depth is fixed.
- Integer and array sizes are bounded before allocation.
- Unknown schema fields are rejected in strict theorem-producing mode.
- Duplicate JSON keys are rejected.
- Canonical digest verification occurs before expensive checking.
- Binary decoders are fuzzed and versioned.

## 7. LeanLink-specific boundary

The Mathematica adapter relies on LeanLink’s native runtime bridge. Native C and LibraryLink code receives:

- memory-safety review;
- cross-platform conformance tests;
- malformed WXF fuzzing;
- handle-lifetime tests;
- and toolchain compatibility tests.

LeanLink remains outside theorem acceptance unless a result is separately checked by MathEvidence Lean code.

## 8. Supply-chain controls

- Lean, Mathlib, Python, and adapter dependencies are pinned.
- Dependency updates are isolated and reviewed.
- Release workflows use least-privilege tokens.
- Artifacts include build provenance.
- Generated releases are signed.
- Public CI runs secret scanning, dependency review, and static analysis.

## 9. Privacy and licensing

Foundry collection is opt-in for private repositories and user sessions. Episodes record source licensing and publication permission. Mathematica-generated expressions and solver artifacts are reviewed for redistribution rights before dataset release.

## 10. Incident response

A checker soundness defect is a critical security incident. Response requires:

1. immediate capability withdrawal;
2. identification of affected bundle and theorem versions;
3. publication of a minimal reproducer;
4. patched checker and replay migration;
5. revalidation of downstream evidence;
6. and a public postmortem.

Adapter-only defects that cannot authorize false theorems follow a lower-severity process, while still preserving evidence provenance.
