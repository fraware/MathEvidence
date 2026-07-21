# Research products — engineering scaffolding status

Product specs ME-301–307 ship as **separate** PRs after ideal-membership value
proof. This note records what exists vs what remains. Do not advertise stubs as
live products. Do not invent human confirmations.

| Issue | Product | In-repo today | Remaining |
| --- | --- | --- | --- |
| ME-301/302 | Hypothesis synthesis | Typed `SufficiencyEvidence` + three-way `proveSufficient`; denom-coverage refusal tests | ≥30 interfaces / expert reviews (human) |
| ME-303 | Conjecture falsification | **Primary:** `Domains.FiniteGraph` + Lean empty-graph falsification; executable atlas **1252** nonduplicate n≤7 graphs; 8 invariants; calibrated + scaled mirror-certified falsification; artifacts under `evidence/conjecture/finite_graph/`; Nat fixtures secondary | Expert precision judgment (human); field-level precision not claimed from campaign batches |
| ME-304 | Trace-to-Plan | Typed Lean `ProofPlan.isAcyclic`; Agent DAG invariants; hint non-advance; **receipt-required** reconstructible advance + tests | Expert lemma-graph coherence (human) |
| ME-305 | Algorithm assurance | Machine-checkable `AlgorithmContract` + six levels; LA/CEX/rational/calculus/ideal linked; LA `referenceCheck_sound` + op eval bridges | Restricted completeness / CAS correspondence levels still open by design |
| ME-306 | Foundry Q3 | Q0–Q4 scoring; **Q2=554** replayable (evidence+conformance+FiniteGraph); source-family splits; datasheet + contamination; `scripts/evaluate_foundry_corpus.py`; **refuse Q1 as positive verified**; **Q3 corpus=0**; **100** unlabeled review-queue packets | Human Q3 labels (≥100); contamination judgment at larger release volume |
| ME-307 | Studio receipts | Shared `verify_checker_receipt`; Certified gate tests | Usability ≥5 sessions (human) |

Human gates ME-401–408: see `docs/validation/human-gates-status.md` (all OPEN).
