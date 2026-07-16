# Product 09 — MathEvidence Studio — acceptance report

**Workstream:** R6  
**Spec:** [docs/products/09_STUDIO.md](../../products/09_STUDIO.md)  
**Date:** 2026-07-16

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Users correctly identify result status in usability testing | **OPEN (human)** | Protocol + ≥3 scripted templates: [`docs/validation/studio/usability/`](../studio/usability/). Session result rows deliberately **OPEN** — do not invent human studies. |
| 2 | Exported theorems replay outside Mathematica | **PASS (eng)** | Studio export writes theorem + bundle; offline replay via Agent/`just replay` on committed `evidence/` (Studio is not TCB). |
| 3 | Studio displays every backend-introduced condition | **PASS (eng)** | `ShowAssumptions` / VS Code assumptions section from `knownAssumptions` / `domainConditions`; golden + UI order tests. |
| 4 | Exact Lean proposition available before certification | **PASS (eng)** | `buildCertificationSurface` / `CertificationSurface`: proposition + assumptions **before** epistemic Certified affordance; missing proposition → not Certified. |
| 5 | UI uses only stable capability and orchestration APIs | **PASS (discipline)** | Client of Agent API / committed bundles / registry; no checker reimplementation in Studio. Capability registry status remains **experimental** (R2). |
| 6 | No unique mathematical semantics live in Studio code | **PASS (eng)** | Documented in `studio/README.md`, Wolfram/VS Code READMEs; proposition fields sourced from Lean/Agent/manifest only. |

## Engineering gates (R6)

| Gate | Result | Evidence |
| --- | --- | --- |
| Certified iff Lean status | **PASS** | `studio/vscode/epistemic.js`, `studio/wolfram/MathEvidenceStudio.wl`, `studio/epistemic_contract.py` |
| Integration / golden transcripts | **PASS** | `studio/golden/transcripts/` (≥7 cases); `adapters/common/test_epistemic_studio.py` |
| Proposition + assumptions before Certified | **PASS** | Transcript order + VS Code `data-section` order + WL `display` Column order |
| Usability protocol + ≥3 session templates | **PASS (protocol)** | `PROTOCOL.md`, `S01`–`S03`; human fills **OPEN** |
| Usability criterion closed | **OPEN** | Owner: Studio / UX lead |

## Overall engineering gate

**PASS** for R6 engineering scope. Product 09 usability acceptance item 1 remains
**OPEN** until real human sessions are recorded. Do not flip capability `stable`.
