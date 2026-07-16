# Product 9 — MathEvidence Studio

## 1. Purpose

MathEvidence Studio provides human-facing workflows in Mathematica and Lean editors for moving from exploration to an explicitly certified theorem.

## 2. Problem solved

Mathematicians work through notebooks, plots, informal formulas, and experiments. Formal proof environments expose stronger guarantees but impose a separate workflow. LeanLink already makes Lean objects and tactics available inside Wolfram Language; Studio adds the missing semantic requests, evidence states, and export lifecycle.

## 3. Surfaces

### Wolfram Studio

Built on LeanLink. Principal actions:

- inspect Lean theorem and type-class context;
- convert a supported Mathematica expression into a candidate MathEvidence request;
- display inferred domains and conditions;
- `CertifyInLean`;
- inspect failed obligations;
- export theorem and evidence bundle;
- browse proof and dependency graphs.

### VS Code extension

Principal actions:

- capability code lens;
- evidence status panel;
- bundle inspector;
- replay command;
- backend policy selection;
- and link to generated theorem and remaining goals.

## 4. Epistemic UI states

The interface must visibly distinguish:

- Computed
- Tested
- Witness verified
- Soundness verified
- Completeness verified
- Optimality verified
- Approximation certified
- Rejected
- Ambiguous

Color alone is insufficient. Every state includes text and a detailed report.

## 5. Certification workflow

1. User selects or generates an expression.
2. Studio identifies a supported capability.
3. User sees the exact proposed Lean statement and assumptions.
4. Ambiguities require explicit resolution.
5. Backend generates candidate and evidence.
6. Lean checker runs.
7. Studio displays the exact established status and unresolved goals.
8. User exports a theorem and bundle.

No result is labeled certified before step 6.

## 6. Usability principles

- progressive disclosure;
- one-click replay;
- exact theorem always inspectable;
- assumptions shown near the result;
- solver provenance available;
- and no requirement that a casual user understand certificate internals.

## 7. Failure modes

- polished UI creates false confidence;
- notebook state and theorem state diverge;
- hidden default assumptions;
- backend-specific behavior leaks into common UX;
- or Studio becomes the project’s center while checkers remain weak.

## 8. Acceptance criteria

1. Users correctly identify result status in usability testing.
2. Exported theorems replay outside Mathematica.
3. Studio displays every backend-introduced condition.
4. The exact Lean proposition is available before certification.
5. The UI uses only stable capability and orchestration APIs.
6. No unique mathematical semantics live in Studio code.
