# Final acceptance matrix

## Historical audit snapshot (frozen)

Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

The original audit recorded every box below as **open** at `c7040e6`. That
snapshot is preserved here for provenance. **Do not treat unchecked historical
boxes as the current engineering score.**

Authoritative living scorecard:
[`TRIPLE_CHECK_GAP_MATRIX.md`](TRIPLE_CHECK_GAP_MATRIX.md).

This specification is normative for the work it covers. Requirements written as
MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance
criterion may be satisfied by a placeholder file, a documentation-only
declaration, a Python mirror of a Lean checker, or an unverified status string.

---

## Current working-tree score (reconciled to TRIPLE_CHECK)

Scores below mirror
[`TRIPLE_CHECK_GAP_MATRIX.md`](TRIPLE_CHECK_GAP_MATRIX.md) as of post-crash
verification 2026-07-27 (local commits `1eb1e15` + `c1c3303`; not pushed).
Checked = **MET** (or MET for the stated fragment). Unchecked =
**PARTIAL** / **BLOCKED** / still open. Hybrid rows note the residual in text.

### Program-level release gates

| Gate | Current score |
| --- | --- |
| Exact request binding | **MET** (rational) |
| Immutable evidence | **MET** |
| Real theorem identity | **MET** (type + proof-term via `serializeExpr`; not `Expr.hash`) |
| Checker authority | **MET** (rational fixtures + ideal live Meta Fin≤3 + LA general sys/ker + general-n det + CEX + analytic) |
| Kernel acceptance | **MET** (rational + analytic fixtures; **Linux CI required**) / residual **PARTIAL(toolchain)** (Windows native Lake link; rsp required locally) |
| Axiom transparency | **MET** |
| Honest receipt | **MET** |
| Replay independence | **PARTIAL** |
| CI attestation | **PARTIAL** (awaiting push + Actions on local closure SHAs) |
| Reproducibility | **MET** (`uv.lock` @ `1eb1e15`) / remote attestation under P0-G |
| Governance | **BLOCKED(org/human)** |
| Adoption | **BLOCKED(human)** |

### Capability matrix

#### Rational equality

- [x] request construction has no fallback digest
- [x] Lean resource bounds enforced
- [x] tactic applies soundness theorem (fixtures + supported live elaborated `eq_of_replaySound` — ME-RV-023 / E-12)
- [x] kernel replay creates original theorem (Linux CI + Windows rsp path; native Lake Windows link PARTIAL)
- [x] true certification record
- [x] SymPy and Mathematica conformance (SymPy rfc0001; Mathematica when env present)
- [x] explicit protocol-reference role

#### Ideal membership

- [x] fixed-arity polynomial IR
- [x] interpretation into Mathlib polynomial
- [x] normalization soundness
- [x] checker soundness to `Ideal.span`
- [x] proof-producing reifier
- [x] external-search tactic (live Meta Fin≤3)
- [x] proposed-witness benchmark (candidate smoke MET; in-repo release-grade Certification Record MET via OfflineFixtures `--tier release` / nightly — P0-F / ME-RV-035)
- [ ] realistic held-out problems (**BLOCKED(human)** external; in-repo `held_out` synthetic)
- [ ] two live backends
- [ ] external adoption (**BLOCKED(human)**)

#### Linear algebra

- [x] reifier semantic bridge (general-n inv/sys/ker/det)
- [x] soundness theorem applied to goal
- [x] real kernel replay (fixtures)
- [x] witness-only claim scope
- [x] complete adversarial suite (engineering); practical det `n` bound by intentional `defaultSizeLimit` / Laplace cost (A5 resource policy — not a missing proof)

#### Finite counterexample

- [x] predicate/domain reifier bridge
- [x] checker soundness applied
- [x] verified refutation receipt
- [x] bounded search status honesty
- [x] Agent conjecture transition gated

#### Analytic calculus

- [x] complete interpretation (owned fragment)
- [x] explicit domain obligations
- [x] derivation certificate
- [x] inductive Mathlib soundness
- [x] ODE residual/IC propositions (candidate residual; no completeness/uniqueness)
- [x] no caller-trusted Booleans
- [x] kernel replay (fixtures; Linux CI + Windows rsp)

### Product matrix

#### Agent

- [x] ID-only public responses
- [x] true content storage
- [x] registry-generated routing
- [x] complete certification verification
- [x] no verified status from executable success alone

#### Studio

- [x] Certified requires verified Certification Record
- [x] theorem and assumptions displayed
- [ ] stale environment invalidates status (engineering present; full Studio surface PARTIAL)
- [ ] three external usability sessions (**BLOCKED(human)**)

#### Hypothesis

- [x] mirror states renamed
- [x] certified sufficient sets require theorem record
- [x] minimality requires necessity coverage

#### Conjecture

- [x] mirror witness does not set falsified
- [x] theorem string does not set formally proved
- [x] refutation rate correctly named

#### Trace-to-Plan

- [x] proof-bearing nodes require proof evidence
- [x] authoritative certification verifier
- [x] target proof closure checked

#### Foundry

- [x] Q2 redefined by kernel certification
- [ ] immutable source commit (PARTIAL with release attestation)
- [x] family-normalized metrics
- [ ] external held-out evaluation (**BLOCKED(human)**)
- [ ] Q3/Q4 human gates (**BLOCKED(human)**)

### Security and release matrix

- [x] committed dependency lock (`uv.lock` @ `1eb1e15` — ME-RV-070 lock-in-history MET; remote Actions under P0-G)
- [x] SHA-pinned setup actions and installer
- [x] environment import audit
- [x] environment axiom audit
- [x] forensic suite required
- [x] ideal benchmark required or nightly according to tier (candidate smoke MET; release-grade OfflineFixtures Cert Record MET / nightly `benchmarks.yml`)
- [x] bundle collision tests
- [ ] signed SBOM/provenance (**PARTIAL** → publish **BLOCKED(human)**)
- [ ] experimental GitHub release (**BLOCKED(human)**)
- [x] branch protection report (enabled; immutable release attestation still open)

### Stable promotion

Stable promotion is **BLOCKED(human)** until every relevant capability, product,
security, governance, and adoption box is complete. A green local command or
documentation declaration cannot substitute for any box.

---

## Historical checklist at `c7040e6` (open at audit time)

### Rational equality

- [ ] request construction has no fallback digest
- [ ] Lean resource bounds enforced
- [ ] tactic applies soundness theorem
- [ ] kernel replay creates original theorem
- [ ] true certification record
- [ ] SymPy and Mathematica conformance
- [ ] explicit protocol-reference role

### Ideal membership

- [ ] fixed-arity polynomial IR
- [ ] interpretation into Mathlib polynomial
- [ ] normalization soundness
- [ ] checker soundness to `Ideal.span`
- [ ] proof-producing reifier
- [ ] external-search tactic
- [x] proposed-witness benchmark
- [ ] realistic held-out problems (in-repo synthetic only; ME-RV-081 external BLOCKED(human))
- [ ] two live backends
- [ ] external adoption
- [x] in-repo release-grade Certification Record (OfflineFixtures `xy`/`x2m1`)

### Linear algebra

- [ ] reifier semantic bridge
- [ ] soundness theorem applied to goal
- [ ] real kernel replay
- [ ] witness-only claim scope
- [ ] complete adversarial suite

### Finite counterexample

- [ ] predicate/domain reifier bridge
- [ ] checker soundness applied
- [ ] verified refutation receipt
- [ ] bounded search status honesty
- [x] Agent conjecture transition gated

### Analytic calculus

- [ ] complete interpretation
- [ ] explicit domain obligations
- [ ] derivation certificate
- [ ] inductive Mathlib soundness
- [ ] ODE residual/IC propositions
- [ ] no caller-trusted Booleans
- [ ] kernel replay

### Agent / Studio / Foundry / security (historical)

All remaining historical product and security boxes were open at `c7040e6`
except the Hypothesis / Conjecture / Trace-to-Plan engineering renames already
checked in the original audit text. See git history of this file at that commit
for the exact checkbox set.
