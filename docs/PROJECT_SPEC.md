# MathEvidence — Normative Project Specification

**Status:** Foundational design specification  
**Audience:** Lean maintainers, formal mathematics researchers, computer-algebra researchers, AI-for-mathematics teams, scientific-computing developers, and repository contributors  
**Normative language:** `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are requirements with their ordinary RFC meanings.

---

## 1. Executive definition

MathEvidence is an open computational-evidence layer for Lean. It provides a common method for translating a precisely delimited Lean problem into an external computational request, receiving a candidate result and mathematical evidence, validating that evidence through Lean-owned semantics and verified checkers, and returning an ordinary Lean theorem.

MathEvidence is not a computer-algebra system, a theorem prover, an AI model, or a Mathematica wrapper. It is the missing assurance and interoperability layer among those systems.

The project is designed around a strict asymmetry.

- External systems may perform expensive, heuristic, proprietary, stochastic, or highly optimized search.
- Lean decides whether the returned artifact establishes the requested mathematical claim.

The result of a successful run is not “Mathematica said true.” The result is a Lean theorem whose proof depends on a verified encoding and a checker soundness theorem.

---

## 2. Exact problem statement

Lean-based mathematical work currently faces a repeated integration problem. Important proof obligations are computationally straightforward for mature external tools and expensive or unavailable inside Lean. Existing bridges usually solve one operation, one backend, or one theorem. They establish local value while reproducing the same infrastructure costs.

Each integration must independently determine:

- how a typed Lean object is represented externally;
- which mathematical structure the backend may assume;
- how local hypotheses become solver assumptions;
- which branch, domain, totalization, or genericity conventions apply;
- what strength of claim the output represents;
- what evidence is sufficient;
- how evidence is parsed and bound to the exact input;
- how solver-level evidence implies the original Lean proposition;
- how the result is replayed without the original solver;
- and how the interaction is exposed to humans and AI agents.

This duplication fragments effort and creates a dangerous semantic gap. A certificate may correctly establish a fact about a serialized solver object while failing to establish the original mathematical statement. Kernel checking does not repair an incorrect specification or encoding.

MathEvidence solves the following problem.

> Formal mathematical systems lack a standard, solver-independent, end-to-end method for admitting external mathematical computation through explicit semantics and checkable evidence while preserving Lean’s trust boundary, supporting multiple claim strengths, enabling offline replay, and producing reusable data for mathematical AI.

---

## 3. North Star

> Every external computation that influences a formal mathematical conclusion crosses into Lean through an explicit semantic contract and independently checkable evidence, producing a reusable theorem without trusting the external solver.

A system satisfies the North Star only when all four conditions hold.

### 3.1 Semantic fidelity

The request preserves the intended types, mathematical structures, assumptions, domains, conventions, and quantified variables of the original Lean proposition.

### 3.2 Evidence clarity

The system states exactly what was established. Candidate validity, soundness, completeness, optimality, canonicality, and approximation are never collapsed into one generic “verified” status.

### 3.3 Independent verification

The accepted theorem can be rechecked from stored evidence using open Lean code. The backend is not part of the theorem’s trusted computing base.

### 3.4 Cumulative value

The result becomes at least one of the following:

- a normal reusable Lean theorem;
- a reusable checker or encoding;
- a capability entry usable by agents and humans;
- a portable evidence bundle;
- a benchmark item;
- or a structured training episode.

---

## 4. Primary users

### 4.1 Lean formalizers

Formalizers need computational subgoals discharged without implementing a full solver, weakening their trust policy, or manually translating external outputs.

### 4.2 Mathematical AI agents

Agents need a stable action space describing mathematical operations, supported fragments, claim strengths, expected evidence, and structured failure modes. Arbitrary shell or notebook access is insufficient.

### 4.3 Mathematicians and scientists

Users working in Mathematica or other computational environments need a path from exploration to an explicit Lean theorem, with assumptions and verification status visible throughout the workflow.

### 4.4 Library maintainers

Maintainers need mathematically appropriate abstractions, small trusted interfaces, offline reproducibility, explicit dependencies, and code that can be reviewed independently from proprietary backends.

### 4.5 Solver and CAS developers

Backend developers need a stable target for emitting mathematically meaningful evidence that can be consumed by Lean without coupling the checker to solver internals.

---

## 5. Design principles

### 5.1 Evidence first, solver second

The core abstraction is a mathematical request and an evidence contract. Backends are replaceable providers.

### 5.2 Lean owns the theorem

The original elaborated Lean proposition is authoritative. An adapter MUST NOT silently replace, weaken, strengthen, or reinterpret it.

### 5.3 Claim strength is typed

The API MUST distinguish at least:

- candidate;
- witness;
- refutation;
- decomposition;
- sound result;
- complete solution;
- optimum;
- enclosure;
- and canonical form.

A proof of a weaker class MUST NOT be promotable to a stronger class without a separate theorem.

### 5.4 Open replay is mandatory

Mathematica MAY be required to generate evidence. It MUST NOT be required to check a committed theorem or evidence bundle.

### 5.5 Small fragments beat universal translation

Each domain defines a restricted, explicit language with a proved interpretation. Unsupported input is rejected. Approximate translation, best-effort name matching, or silent fallback is forbidden in theorem-producing paths.

### 5.6 Existing projects remain authoritative

MathEvidence MUST reuse mature domain work, including certificate checkers, verified encodings, solver bridges, scientific libraries, and physics libraries. It MUST NOT duplicate a specialized checker merely to fit an umbrella architecture.

### 5.7 Deterministic replay, optional regeneration

Rechecking MUST be deterministic. Regenerating evidence from a solver MAY be nondeterministic and is reported separately.

### 5.8 Human and agent surfaces share semantics

A tactic, API call, notebook action, and benchmark episode MUST use the same operation identifier, request schema, claim class, and result status.

### 5.9 Failure is first-class data

Unsupported fragments, missing assumptions, rejected certificates, incorrect candidates, timeouts, and semantic ambiguities are retained as structured outcomes.

### 5.10 No abstraction without two implementations

A shared core interface SHOULD enter stable status only after at least two independent domains or backends need it. Premature universality is a project-level failure mode.

---

## 6. Scope

### 6.1 In scope

- Typed computational requests derived from Lean propositions.
- Domain-specific semantic IRs and reification.
- Solver-independent claim and evidence classes.
- Verified encodings between Lean objects and executable representations.
- Verified or reconstructing evidence checkers.
- Mathematica integration through LeanLink.
- Open adapters, initially SageMath or SymPy.
- Offline evidence replay.
- Lean tactics and programmatic APIs.
- AI-facing tool schemas.
- Capability discovery and conformance.
- Evidence bundles, provenance, benchmarks, and foundry episodes.
- Hypothesis synthesis, conjecture falsification, and proof-plan extraction as downstream products.

### 6.2 Explicit non-goals

- Reimplementing Mathematica.
- Creating a universal mathematical ontology.
- Accepting raw backend truth values.
- Verifying proprietary Mathematica internals.
- Replacing Mathlib, CSLib, Physlib, SciLean, LeanLink, Lean-SMT, or domain certificate projects.
- Supporting arbitrary Wolfram Language expressions in a theorem-producing path.
- Claiming completeness when only a witness or candidate has been checked.
- Using AI-generated statements as semantically reviewed mathematics without expert approval.
- Making a notebook the trust authority.
- Building a new monolithic Lean server where existing agent interfaces suffice.

---

## 7. Trust model

### 7.1 Untrusted components

The following are untrusted by default:

- Mathematica;
- SageMath;
- SymPy;
- external SAT, SMT, optimization, or numerical solvers;
- backend adapters;
- orchestration services;
- AI models;
- notebooks;
- network transport;
- generated explanations;
- and evidence-generation heuristics.

A defect in an untrusted component may cause failure, wasted computation, malformed evidence, or rejection. It MUST NOT authorize a false theorem.

### 7.2 Trusted or assurance-critical components

The theorem-level trust path consists of:

- the Lean kernel;
- the mathematical definitions and accepted axioms in the imported library environment;
- the reification and interpretation theorems;
- the verified encoding theorem;
- the checker soundness theorem;
- and the exact decoded evidence value accepted by the checker.

Native execution, external parsers, and compiled reflection MAY enlarge the operational trusted base. Every result MUST report its assurance mode.

### 7.3 Assurance modes

The project defines three initial assurance modes.

#### `kernel_replay`

The result is reconstructed or checked through ordinary Lean terms accepted by the kernel. This is the preferred release mode for small and medium evidence.

#### `verified_reflection`

A reified decision procedure has a Lean soundness theorem, and the kernel checks the theorem application. The implementation may use efficient evaluation while preserving an explicit soundness boundary.

#### `native_checked`

A verified checker executes through native compilation or runtime facilities for scale. The larger operational trusted base MUST be declared. High-value releases SHOULD provide a slower `kernel_replay` path for reduced instances or an independent checker.

### 7.4 Axiom policy

- Project-specific axioms are forbidden in release packages.
- `sorry` is forbidden outside explicitly marked experimental fixtures.
- Every release theorem MUST pass an axiom audit.
- Standard Mathlib axioms and classical principles are reported, not hidden.
- A backend premise imported from an external proof is an assumption unless Lean independently proves or accepts it as a user hypothesis.

---

## 8. Core domain model

### 8.1 `ProblemSpec`

A `ProblemSpec` defines the mathematical relation between an input and an admissible output.

Conceptually:

```lean
structure ProblemSpec where
  Input      : Type
  Output     : Type
  admissible : Input → Prop
  relation   : Input → Output → Prop
```

Production code MAY use indexed structures and type classes. The invariant remains that correctness is a Lean proposition independent of any solver.

### 8.2 `ClaimClass`

```lean
inductive ClaimClass
  | candidate
  | witness
  | refutation
  | decomposition
  | soundResult
  | completeSolution
  | optimum
  | enclosure
  | canonicalForm
```

Domain packages MAY introduce refined classes. They MUST declare their ordering and promotion theorems.

### 8.3 `Evidence`

Evidence is a typed object whose meaning is determined by the problem specification and claim class. Examples include:

- a factor list and reconstruction identity;
- coefficients establishing ideal membership;
- a primal-dual pair;
- an interval enclosure;
- a resolution or pseudo-Boolean trace;
- a concrete counterexample;
- or an inductive recurrence witness.

Evidence MUST be mathematical. It SHOULD NOT encode a backend’s private execution trace unless that trace has a stable, documented proof semantics.

### 8.4 `Encoding`

Each domain integration defines:

- an abstract Lean object;
- an executable representation;
- an encoder;
- an interpreter for the executable representation;
- and a theorem relating both semantics.

No headline capability is complete without this theorem.

### 8.5 `Checker`

A checker consumes the exact request, candidate output, and evidence. It returns a decidable acceptance result and has a soundness theorem.

Conceptually:

```lean
def check : Request → Candidate → Certificate → Bool

theorem check_sound :
  check req out cert = true →
  req.admissible →
  req.relation out
```

The concrete theorem MUST bind the certificate to the request. A valid certificate for another request is rejected.

### 8.6 `Capability`

A capability describes:

- a stable operation identifier;
- semantic version;
- supported domains;
- accepted expression fragment;
- available claim classes;
- evidence schema;
- checker package;
- assurance modes;
- backend implementations;
- deterministic limits;
- and conformance suite.

### 8.7 `ResultStatus`

The user-visible result status is distinct from claim class.

- `computed`
- `tested`
- `witness_verified`
- `soundness_verified`
- `completeness_verified`
- `optimality_verified`
- `approximation_certified`
- `native_verified`
- `rejected`
- `unsupported`
- `ambiguous`

### 8.8 `EvidenceBundle`

An evidence bundle is an immutable, content-addressed artifact containing everything required for offline replay.

Minimum contents:

```text
bundle/
├── manifest.json
├── request.json
├── candidate.json
├── certificate/
├── checker-report.json
├── theorem.lean
├── dependencies.json
└── README.md
```

The bundle MUST bind all files through SHA-256 digests. Control-plane JSON MUST use a canonical serialization profile. Large domain certificates MAY use a domain-defined binary representation with a documented decoder and digest.

---

## 9. End-to-end workflow

### 9.1 Discovery mode

1. Lean elaborates the original target and context.
2. Capability recognition determines whether a supported fragment applies.
3. Reification produces a typed internal object and a proof of semantic correspondence.
4. The orchestration layer constructs a versioned request.
5. A selected backend generates a candidate and evidence.
6. Lean decodes the response as untrusted data.
7. The domain checker validates evidence and exact request binding.
8. The soundness theorem produces the original or an explicitly related proposition.
9. Remaining side conditions become visible Lean goals.
10. The system emits a theorem and portable evidence bundle.

### 9.2 Replay mode

1. No backend is started.
2. The committed request, candidate, and certificate are read.
3. Digests and schema versions are validated.
4. The Lean checker reruns.
5. The theorem is rebuilt or revalidated.

Replay mode is the mode used by public CI and downstream consumers.

### 9.3 Agent mode

1. The agent receives capability metadata and exact schemas.
2. The agent selects an operation and requested claim strength.
3. The system validates preconditions before invoking a backend.
4. The response reports the strongest established status and unresolved obligations.
5. The agent may repair assumptions, select another capability, or continue the proof.

The agent never receives a generic “success” for a weaker claim than requested.

---

## 10. The nine products

MathEvidence contains nine products with independent specifications.

1. **Semantic Bridge** — typed domain IRs, reification, interpretation, and verified encodings.
2. **Certified Computation Service** — common orchestration, evidence checking, replay, and theorem production.
3. **Hypothesis Synthesis** — side-condition discovery, sufficiency proof, hypothesis deletion, and certified counterexamples.
4. **Conjecture and Falsification Engine** — computational experiments over formal object families, candidate conjectures, and certified refutations.
5. **Trace-to-Plan Engine** — converts computational traces and hints into Lean proof-plan DAGs without treating hints as proofs.
6. **Algorithm Assurance** — formal contracts, verified reference algorithms, checker verification, and restricted audits of external implementations.
7. **Capability Registry** — machine-readable capability discovery, conformance, and versioned support claims.
8. **MathEvidence Foundry** — structured episodes, provenance, quality tiers, contamination controls, and training datasets.
9. **MathEvidence Studio** — Mathematica and editor workflows that expose computed, tested, and formally established states.

Shared infrastructure includes the Agent API, evidence bundles, benchmarks, CI, security, governance, and documentation.

---

## 11. Initial capabilities

### 11.1 Rational-function equality

Supported v0 fragment:

- variables over `ℚ` initially;
- integer and rational constants;
- addition, subtraction, multiplication;
- natural powers;
- division;
- equality;
- explicit nonzero hypotheses.

The checker proves equality under all required denominator conditions. It does not claim a globally defined rational function identity at singular points.

### 11.2 Exact linear algebra

Initial operations:

- matrix inverse witness;
- exact linear-system solution;
- kernel vector witness;
- determinant identity.

Completeness of a kernel basis, rank, or solution family requires separate evidence.

### 11.3 Finite counterexample

The backend returns a typed finite witness. Lean evaluates the original predicate and produces a theorem establishing the refutation. Exhaustive absence of counterexamples is outside this initial capability.

---

## 12. API requirements

### 12.1 Lean tactic interface

The first user-facing commands SHOULD include:

```lean
by
  mathevidence
```

and explicit forms:

```lean
by
  mathevidence (operation := .rationalEquality)
    (backend := .mathematica)
    (claim := .soundResult)
```

A tactic MUST report:

- recognized operation;
- supported fragment;
- assumptions exported;
- conditions returned;
- backend used;
- claim requested;
- claim established;
- assurance mode;
- evidence bundle location;
- and remaining goals.

### 12.2 Backend protocol

Adapters communicate through versioned JSON-RPC over standard input/output for the initial implementation. The protocol MUST avoid persistent network services in the core path.

Required methods:

- `initialize`
- `listCapabilities`
- `checkSupport`
- `compute`
- `cancel`
- `shutdown`

Each response MUST include protocol version, backend identity, capability version, request digest, deterministic options, resource usage, and structured error information.

### 12.3 Agent API

The Agent API exposes operation-level tools. It MUST NOT expose arbitrary code execution as a MathEvidence capability.

Each tool has:

- a stable operation ID;
- JSON Schema input and output;
- supported claim strengths;
- maximum resource policy;
- result status;
- unresolved proof obligations;
- and evidence bundle reference.

### 12.4 Studio API

Studio integrations call the same orchestration API. The UI MUST display status and assumptions before presenting a result as certified.

---

## 13. Error taxonomy

Errors are stable, structured, and suitable for agents.

### Semantic errors

- `unsupported_expression`
- `unsupported_type`
- `ambiguous_interpretation`
- `missing_assumption`
- `branch_convention_required`
- `partial_operation_unresolved`
- `claim_strength_unavailable`

### Backend errors

- `backend_unavailable`
- `backend_timeout`
- `backend_crash`
- `backend_unsupported`
- `backend_nondeterministic_failure`

### Evidence errors

- `malformed_evidence`
- `request_digest_mismatch`
- `candidate_rejected`
- `certificate_rejected`
- `completeness_not_established`
- `approximation_bound_missing`

### System errors

- `schema_version_unsupported`
- `resource_limit_exceeded`
- `replay_dependency_missing`
- `assurance_mode_unavailable`

Free-form exception strings are diagnostic supplements, never the only error representation.

---

## 14. Security requirements

- Adapters run in constrained subprocesses with explicit CPU, memory, file, and wall-clock limits.
- No theorem-producing checker performs network access.
- All imported evidence is treated as hostile input.
- Parsers use bounded allocation and depth limits.
- Request and certificate sizes are capped per capability.
- The C bridge used by LeanLink receives separate fuzzing and review.
- Temporary directories are isolated and deleted.
- Backend command lines are constructed from fixed executables and structured arguments, never shell interpolation.
- Evidence bundles reject path traversal and symlink escape.
- CI includes malformed, adversarial, and resource-exhaustion cases.
- Security advisories follow coordinated disclosure.

See `docs/SECURITY_AND_TRUST_MODEL.md`.

---

## 15. Testing strategy

### Unit tests

Every parser, serializer, reifier, interpreter, checker, and result-state transition has deterministic unit tests.

### Property tests

Round-trip and semantic preservation properties are generated over bounded fragments.

### Differential tests

Two or more backends solve identical requests. Lean determines validity; disagreement becomes a retained test artifact.

### Adversarial tests

The suite includes wrong domains, omitted conditions, wrong request hashes, malformed certificates, extreme values, binder confusion, and resource attacks.

### Metamorphic tests

Equivalent syntactic variants, variable renamings, harmless reorderings, and redundant assumptions must preserve results where the semantics require it.

### Offline replay tests

Every committed evidence bundle is rechecked with all backends disabled.

### Axiom and `sorry` audits

Release CI rejects forbidden axioms and incomplete proofs.

See `docs/TESTING_AND_CI.md`.

---

## 16. Repository and dependency rules

- `MathEvidence/Core`, `IR`, and `Checkers` MUST NOT depend on adapter, agent, studio, foundry, or network code.
- Backend adapters MAY depend on LeanLink or language-specific packages.
- `Tactic` MAY invoke orchestration in discovery mode and MUST support replay mode without adapters.
- Registry declarations are data and MUST pass conformance tests.
- Foundry pipelines consume execution records; they never influence theorem acceptance.
- Examples and benchmarks MAY depend on several products but MUST NOT create reverse dependencies.
- Experimental code lives under an explicit namespace and cannot be imported by release modules.

See `docs/REPOSITORY_ARCHITECTURE.md`.

---

## 17. Governance

### 17.1 Maintainer areas

- Core protocol and trust model
- Semantic IR and encoding
- Domain checkers
- Backend adapters
- Agent API
- Studio
- Registry
- Foundry and benchmarks
- Security and release engineering

### 17.2 Decision process

- Cross-cutting semantic changes require an RFC.
- Local implementation changes use ordinary pull requests.
- Stable protocol changes require two approving maintainers from different areas.
- A capability cannot be marked stable until its conformance suite, checker soundness theorem, and offline replay are complete.
- Domain semantics are reviewed with maintainers or experts from the relevant Lean library.

### 17.3 Compatibility policy

- Core protocol uses semantic versioning.
- Capability schemas are independently versioned.
- Evidence bundles declare exact versions.
- Stable checkers retain backward replay support for at least two minor protocol generations or provide a deterministic migration tool.

---

## 18. Delivery roadmap

### Phase 0 — Validation and RFC

- collect real computational bottlenecks;
- publish the trust model;
- specify rational equality;
- agree ecosystem boundaries;
- build adversarial benchmark seed.

### Phase 1 — Reference path

- Mathematica adapter through LeanLink;
- open adapter through SageMath or SymPy;
- rational equality checker;
- offline bundle replay;
- initial tactic.

### Phase 2 — Cross-domain validation

- exact linear algebra;
- finite counterexamples;
- common registry and conformance;
- first agent API.

### Phase 3 — Hypothesis intelligence

- backend-proposed conditions;
- Lean sufficiency proof;
- hypothesis deletion;
- certified counterexamples;
- condition lattice artifacts.

### Phase 4 — Existing ecosystem integration

- integrate external Gröbner work;
- represent SAT, pseudo-Boolean, and SMT capabilities;
- align generic interfaces with CSLib and Lean-auto where appropriate.

### Phase 5 — Symbolic calculus vertical

- derivative candidates;
- antiderivative verification on explicit domains;
- recurrence identities;
- ODE candidate and initial-condition checking.

### Phase 6 — Foundry and frontier programs

- release certified tool-use corpus;
- train verification-aware tool selectors;
- deploy into selected frontier mathematical developments.

---

## 19. Success metrics

The primary metric is **verified computational coverage**:

> The fraction of genuine computational proof obligations in representative Lean developments that can be delegated and returned as independently checkable Lean theorems without bespoke integration code.

Secondary metrics:

- open replay rate;
- semantic defect rate;
- accepted theorem rate;
- improvement over Lean-only baselines;
- human time saved;
- certificate size and checking cost;
- number of backends sharing a checker;
- downstream package reuse;
- upstream library contributions;
- high-quality foundry episodes;
- and frontier results materially enabled.

Proof count alone is not a success metric.

---

## 20. Kill and pivot criteria

The project MUST reconsider its architecture if, after the initial implementation:

- three distinct capabilities cannot fit a small common lifecycle;
- two backends cannot share one checker;
- offline replay cannot be made routine;
- semantic translation errors remain frequent under expert audit;
- checker cost consistently dominates the workflow;
- existing projects reject the interfaces as duplicative or unsuitable;
- or the principal value remains notebook visualization.

The project SHOULD narrow its scope if analytic verticals require theorem-specific engineering with little reusable infrastructure.

---

## 21. Definition of done for version 0.1

Version 0.1 is complete only when:

1. Rational-function equality works end to end through Mathematica and one open backend.
2. The same Lean checker accepts both evidence formats after adapter normalization.
3. All side conditions are explicit.
4. Every example rechecks offline with backends unavailable.
5. Request/certificate mismatch and malformed evidence are rejected.
6. The Lean package contains no forbidden axioms or incomplete proofs.
7. The capability is discoverable through the registry and Agent API.
8. The benchmark includes real and adversarial tasks.
9. A user can invoke one stable tactic and receive precise status reporting.
10. At least one external Lean contributor or project confirms the component solves a real workflow problem.
