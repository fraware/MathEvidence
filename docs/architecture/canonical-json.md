# MathEvidence Canonical JSON Profile

## Status

Phase 1 Core digest helpers implement SHA-256 binding and Lean-side canonical
JSON fragments in `MathEvidence.Core.CanonicalJson` / `Digest`. Adapters must
emit the same UTF-8 byte sequence before hashing.

## Intent

Control-plane artifacts (requests, evidence metadata, capability declarations)
use canonical JSON compatible with [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)
principles so SHA-256 digests are stable across producers.

## v0 profile (planned)

1. **Encoding:** UTF-8 JSON text; no BOM.
2. **Object key order:** lexicographic by UTF-16 code unit sequence (RFC 8785).
3. **Numbers:** integers in canonical decimal form without leading zeros (except
   `0`); no floats in theorem-binding digests for v0 rational equality.
4. **Strings:** escaped per RFC 8785 §3.2.2.2.
5. **Whitespace:** none between tokens in the canonical serialization used for
   digests.
6. **Duplicate keys:** rejected before hashing (strict mode).
7. **Unknown fields:** rejected in theorem-producing mode; allowed only in
   explicitly versioned non-binding envelopes if introduced later.
8. **Digest:** SHA-256 over the canonical UTF-8 bytes; hex lowercase in
   manifests.

## Out of scope for digests

- Pretty-printed human evidence dumps.
- Backend-native binary certificates until a versioned Lean decoder exists
  (`docs/REPOSITORY_ARCHITECTURE.md` §12).

## Implementation hooks

- Python: `adapters/common` canonicalization shared with request binding
  (`canonical_dumps`, `bind_request_digest`).
- Lean: `MathEvidence.Core.JsonCanonical` recomputes the same profile over
  `Lean.Json` (key sort by UTF-16 code units; reject non-integral numbers).
- Lean fragments: `MathEvidence.Core.CanonicalJson` for hand-built IR digests.
- Conformance vectors: `evidence/conformance/vectors/canonical_json_vectors.json`
  (exercised in Python tests and `MathEvidence.Core.JsonCanonicalTests`).
- Wire request binding for rational equality: Lean
  `MathEvidence.Tactic.Discovery.bindRequestDigest` must match Python for the
  same request object (see `lean_wire_digest_matches_basic_sympy`).

Do not claim interoperability with a third-party JCS library until those vectors
remain green in CI (`adversarial.yml`).
