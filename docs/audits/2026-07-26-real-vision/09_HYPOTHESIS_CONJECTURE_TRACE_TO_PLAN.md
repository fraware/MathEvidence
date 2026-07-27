# Standalone specification — Hypothesis, Conjecture, and Trace-to-Plan products


Audit target: `fraware/MathEvidence`  
Audited branch: `main`  
Audited commit: `c7040e6c60979bc0a05334ce5011e5ac7bcf4b03`  
Audit date: `2026-07-26`

This specification is normative for the work it covers. Requirements written as MUST, MUST NOT, SHOULD, and MAY have their ordinary RFC meanings. No acceptance criterion may be satisfied by a placeholder file, a documentation-only declaration, a Python mirror of a Lean checker, or an unverified status string.

The audit inspected repository contents and GitHub workflow records through the GitHub connector. The execution environment could not resolve `github.com` for a local clone, so this audit does not claim that `just check` was executed locally. Current-main CI is also unverified because the available GitHub status endpoint returned no attested status set for the audited head.


## Shared epistemic model

Define these product states:

- `proposed`
- `mirror_accepted`
- `checker_accepted`
- `kernel_certified`
- `rejected`
- `unknown`

Only `kernel_certified` carries a theorem or refutation claim.

## Hypothesis synthesis

### Outcome vocabulary

Change `prove_sufficient_python`:

- current `proved` from Python mirror becomes `mirror_accepted`;
- `sufficient: true` becomes `mirrorSufficient: true`;
- `authorityStatus` becomes `python_checker_mirror`;
- no theorem declaration or empty receipt identifier may be presented as evidence.

Add a kernel operation that receives a candidate condition set, constructs the theorem obligation, runs kernel replay, and returns a Certification Record.

### Lattice nodes

Each sufficient set must record:

- preview status;
- candidate bundle ID;
- certification record ID when available;
- theorem declaration;
- exact assumptions;
- reviewer status.

A set enters `sufficientSetsCertified` only after kernel certification.

### Minimality

Retain the current no-minimality default. A minimality claim requires:

- certified sufficiency of the selected set;
- for every retained condition, a certified refutation of the theorem with that condition removed, or a direct necessity theorem;
- explicit finite search completeness when a finite argument is used.

## Conjecture falsification

### Refutation transition

`certify_refutation` must accept a verified Certification Record, not a Python certificate alone.

Python mirror acceptance sets:

```text
state = candidate_statement
refutationPreview = mirror_accepted
```

Kernel certification sets:

```text
state = falsified
certifiedRefutationId = certificationRecordId
```

### Formally proved transition

Remove `mark_formally_proved(episode, theorem_ref : str)`. Replace it with a function that validates:

- theorem declaration exists in a pinned environment;
- theorem type matches the conjecture;
- certification or source proof record exists;
- axiom policy passes.

### Precision metric

Rename `precisionRate = falsified/proposed` to `refutationRate`. Add:

- candidate validity rate;
- theorem conversion rate;
- open rate;
- bounded-only rate;
- false-positive rate after expert review.

## Trace-to-Plan

### Receipt gate

`reconstruct_from_receipt` must call the authoritative certification verifier. Studio’s structural receipt checker cannot authorize proof advancement.

### Direct proof steps

A `direct_proof_step` may advance only when it includes:

- theorem declaration;
- theorem type digest;
- environment lock digest;
- axiom report or imported proof provenance.

A status string is insufficient.

### DAG semantics

Add a final plan soundness check:

- every proved node has proof evidence;
- every dependency target type matches;
- the target node becomes proved only when all required incoming dependencies are proved and a reconstruction theorem exists;
- suggestion edges never imply proof dependency.

## Tests

- mirror-accepted sufficiency never enters certified set;
- forged refutation receipt does not set falsified;
- arbitrary theorem reference cannot set formally proved;
- hint cannot advance;
- checker receipt with certificate-only binding cannot advance;
- direct step without theorem digest cannot advance;
- cyclic and dangling plans reject;
- certified condition deletion updates lattice correctly;
- minimality refuses incomplete necessity coverage.

## Acceptance

Every proof-bearing product state must cite a verified Certification Record or an independently validated existing Lean declaration.
