# Current system map — what works and what remains incomplete


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Core protocol

### Working

- Digest classes are nominally separated in Lean.
- Canonical JSON and SHA-256 implementations exist in Lean and Python.
- Rational requests can be encoded and hashed on the Lean side.
- Evidence Bundle v0.2 records per-file content digests.
- Bundle path validation rejects common traversal forms.
- `CheckerReceipt` names the major artifacts expected in a certification chain.

### Incomplete

- Public constructors allow malformed digest strings to inhabit typed wrappers.
- `Request.ofClaim` uses an all-zero fallback on canonicalization failure.
- Receipt validation checks mostly non-empty strings and does not establish cryptographic or semantic coherence.
- Bundle metadata does not define a true bundle identity.
- Mandatory role semantics are underspecified.
- Candidate and certified artifacts are mixed inside one mutable directory.

### Required state

Every digest type must have an opaque constructor or invariant-preserving smart constructor. Every verified receipt must pass independent recomputation of every digest. Candidate evidence and theorem certification must be separate immutable objects.

## Rational equality

### Working

- Restricted rational syntax is explicit.
- Division and denominator conditions are visible.
- Polynomial normalization is implemented in Lean.
- Checker soundness proves equality under explicit definedness conditions.
- Live discovery compares the certificate digest with the Lean-derived request digest.
- The tactic refuses goal mismatch and malformed evidence.

### Incomplete

- Checker resource bounds are not enforced in Lean.
- Denominator coverage uses structural expression equality.
- The theorem tactic ultimately closes with `field_simp` and `ring`.
- Standalone replay emits theorem-level status without constructing a theorem.
- Offline bundle IDs are hardcoded.
- The external backend contributes little computational value for the supported fragment.

### Required state

The tactic must apply `checkBool_sound` and the semantic bridge to the current goal. Standalone replay must compile or elaborate a theorem declaration. Rational equality must be labeled a protocol-reference capability.

## Exact linear algebra

### Working

- Exact rational matrix and vector syntax exists.
- Witness checks cover inverse, solution, kernel vector, and determinant identity.
- Soundness lemmas connect executable checks to exact evaluated relations.
- A restricted Meta reifier recognizes concrete matrix expressions.
- A tactic can close selected concrete goals.

### Incomplete

- Reifier correctness is not formally proved.
- The tactic checks a certificate and separately uses `native_decide`.
- Bundle replay and certification receipts are not end-to-end for this capability.
- No completeness claims are supported, which is correct but must remain prominent.
- Matrix shape and coefficient restrictions are narrower than ordinary Mathlib usage.

### Required state

The checker theorem must be applied to the original goal through a proved encoding. The capability must produce real receipts through the common replay path. Scope remains exact witness validation.

## Finite counterexamples

### Working

- Explicit finite domains and typed assignments exist.
- Counterexample checker validates domain membership and predicate falsification.
- Restricted Meta reification handles Fin, Bool, bounded Nat, and bounded Int patterns.
- The tactic constructs an explicit proof for bounded Int and uses decision procedures for finite cases.
- “No counterexample found” is not treated as proof.

### Incomplete

- Reifier correctness is unproved.
- The checker and final goal proof are parallel.
- Agent conjecture states rely on a Python checker mirror.
- General finite structures and domain-specific objects are unsupported.

### Required state

The reifier must produce a theorem that connects the IR predicate to the Lean predicate. Checker acceptance must directly yield the refutation theorem. Agent transitions must require a verified certification record.

## Formal rational calculus

### Working

- The capability is correctly renamed to `algebra.formal_rational_calculus`.
- Derivative, antiderivative, recurrence, and ODE residual candidate checks are explicitly weaker than completeness.
- Mathematica and SymPy candidate generation paths exist for the rational fragment.

### Incomplete

- This is formal algebra over rational expressions, not analytic calculus.
- Domain interpretation is limited to algebraic definedness.
- Public file paths still retain `symbolic_calculus` legacy names.
- Capability and benchmark naming remain partially inconsistent.

### Required state

Complete the naming migration, keep the scope explicit, and route all verified claims through the certification-record architecture.

## Analytic calculus

### Working

- An `AnalyticExpr` syntax exists.
- Mathlib `HasDerivAt` examples are present.
- Domain-conditioned inverse and log examples show the intended semantics.
- Completeness flags are rejected.

### Incomplete

- Certificate acceptance does not imply a theorem about the interpreted expression.
- ODE residual and initial-condition fields are trusted Booleans.
- `sin`, `exp`, and `log` are syntax constructors without a complete derivative derivation checker.
- No Meta reifier or end-to-end adapter/checker/tactic path exists.
- The marker theorem `requiresHasDerivAt = true` is not a semantic soundness theorem.

### Required state

Implement an inductive derivation certificate, interpretation semantics, domain obligations, and an inductive soundness proof to Mathlib calculus propositions.

## Ideal membership

### Working

- Sparse integer polynomial syntax and executable arithmetic exist.
- SymPy can search for quotient witnesses.
- Sage and Mathematica fixture/live hooks exist.
- Restricted Polynomial and MvPolynomial reification covers useful examples.
- The tactic reconstructs ordinary Mathlib ideal-membership proofs.
- A 55-task benchmark corpus exists.

### Incomplete

- Custom checker acceptance is not formally connected to Mathlib polynomial semantics.
- The tactic’s actual proof is produced by `ring`.
- The capability is called `groebner_membership` although no Gröbner certificate is checked.
- Sparse monomials are represented by unvalidated exponent lists.
- Python arithmetic truncates mismatched exponent vectors through `zip`.
- Benchmark success is based on expected multipliers, not backend-proposed multipliers.
- Most tasks are synthetic and several are trivial family variants.
- The Lean tactic does not invoke external search.
- Registry conformance is false and backend conformance digests are null.

### Required state

Rename or implement genuine Gröbner semantics, prove the sparse interpretation, make the checker theorem authoritative, score proposed witnesses, and connect the tactic to external search with an explicit offline fallback.

## Agent API

### Working

- Backend routing consults registry support levels.
- Public bundle operations reject raw paths.
- Bundle writes are confined to an Agent store.
- Manifest-only verified status is downgraded when no receipt exists.
- Missing replay executable yields `tested`.

### Incomplete

- Content storage is keyed by request digest.
- Receipt verification binds only a subset of files.
- Standalone replay is treated as theorem authority despite its Boolean-only behavior.
- Responses expose local filesystem paths.
- Static compute-capability lists duplicate registry metadata.
- Candidate bundle generation uses theorem and axiom placeholders.

### Required state

Adopt true bundle identity, certification records, status derivation from kernel receipts, ID-only responses, and generated routing tables.

## Studio

### Working

- Proposition and assumptions appear before epistemic status.
- Manifest-only verified status is rendered Ambiguous.
- Computed, Tested, Certified, and Ambiguous are separated.
- Golden transcripts and cross-surface rules exist.

### Incomplete

- A structurally plausible unsigned receipt can allow Certified.
- Receipt verification lacks theorem, axiom, environment, and bundle-byte checks.
- Studio performs trust decisions without access to the full immutable certification object.
- Human usability sessions remain open.

### Required state

Studio must consume a verification result from the authoritative Agent verifier or a shared verifier with access to all content. It must never infer Certified from a receipt object alone.

## Hypothesis, conjecture, and Trace-to-Plan

### Working

- Minimality is guarded.
- Condition lattices record unresolved necessity.
- Bounded verification is separated from theorem proof.
- Trace DAGs enforce acyclicity and restrict hint advancement.

### Incomplete

- Python mirror acceptance is called `proved`.
- Mirror counterexamples are called certified and directly set `falsified`.
- An arbitrary theorem reference string can set `formally_proved`.
- Trace-to-Plan can advance from a structurally verified receipt.
- Direct proof steps can advance without an actual proof reference.

### Required state

Introduce preview-only states and require verified certification records for every proof-bearing transition.

## Foundry and benchmarks

### Working

- Acceptance influence is explicitly false.
- Source-family splits and contamination controls exist.
- Q3/Q4 are not auto-assigned.
- FiniteGraph campaigns create a substantial corpus.
- Review queues and independent evaluation scripts exist.

### Incomplete

- The corpus claims 554 Q2 formally verified episodes, although many source paths derive from mirrors or generated campaigns.
- `sourceCommit` is `workspace`.
- Domain diversity is low.
- Ideal membership benchmark methodology is invalid for backend success.
- Benchmarks are not all wired into CI.
- Large counts can conceal repeated task families.

### Required state

Reclassify episodes using verified certification records, pin source commits, report family-normalized statistics, correct benchmark scoring, and add external-project held-out sets.

## CI, security, release, governance

### Working

- GitHub actions are mostly SHA-pinned.
- Forensic tests exist.
- Ruff, mypy, pytest, schema validation, conformance, adversarial, and performance commands exist.
- Governance docs honestly record single ownership.
- All registry capabilities remain experimental.

### Incomplete

- Current-main CI is not attested.
- `uv.lock` is optional.
- Elan installation is fetched from mutable `master`.
- Actual CI uses regex trust-boundary and sorry scans.
- Encoding is omitted from the Python import-boundary scan.
- Several Lean packages are omitted from the sorry/axiom scan.
- Ideal membership and replay executable are absent from the full local gate.
- Release workflow creates provenance only and does not sign or publish.
- Registry stable validation does not enforce human gates.
- No repository issues track the remaining work.

### Required state

Implement protected required checks, commit a lock, pin all installers, run environment-level audits, include every flagship gate, produce signed release artifacts, and enforce machine-readable promotion records.
