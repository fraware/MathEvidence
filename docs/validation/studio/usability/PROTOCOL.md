# MathEvidence Studio — usability protocol (Product 09)

**Status:** engineering protocol ready; **human session results OPEN**  
**Owner (sessions):** Studio / UX lead  
**Do not invent** completed human study outcomes.

This document defines how to run scripted usability sessions for Product 09
acceptance criterion 1 (*Users correctly identify result status in usability
testing*). Machine-checkable Certified gates live under
[`studio/golden/`](../../studio/golden/) and
[`adapters/common/test_epistemic_studio.py`](../../adapters/common/test_epistemic_studio.py).

## Goals

1. Confirm participants distinguish **Computed / Tested / Certified / Ambiguous**
   without relying on color alone.
2. Confirm participants see the **exact Lean proposition** and **assumptions**
   *before* treating a result as Certified.
3. Record defects (false confidence, hidden assumptions, notebook/theorem
   divergence) without claiming pass rates until sessions complete.

## Participants

- Target: ≥3 external or non-author participants (same bar spirit as Milestone 0).
- Do not count authors of Studio surfaces as completing this gate.

## Materials

| Material | Path |
| --- | --- |
| Session templates | [`sessions/`](sessions/) |
| Golden transcripts (integration) | `studio/golden/transcripts/` |
| VS Code surface | `studio/vscode/` |
| Wolfram surface | `studio/wolfram/` |
| Defect log (fill during sessions) | [`defect-log.md`](defect-log.md) |

## Session flow (all templates)

1. Brief (≤5 min): trust model — Studio is not a checker; Lean status required for Certified.
2. Warm-up: open a **Computed** bundle / payload; ask for status label + why.
3. Scripted tasks from the chosen session template (S01–S03).
4. Debrief: where false confidence could arise; any missing assumption display.
5. Facilitator files defects in `defect-log.md` (severity + repro). Leave result
   rows **OPEN** until a real human completes them.

## Success criteria (when humans complete)

A session **passes** only if:

- Participant correctly labels Certified vs Ambiguous on the verified-without-Lean case.
- Participant identifies that proposition + assumptions appear before Certified.
- Exported / inspected theorem is understood as Lean-side, not Studio invention.

Aggregate Product 09 criterion 1 is **OPEN** until ≥3 completed session result
rows exist under [`sessions/`](sessions/).

## Explicitly out of scope

- Inventing pass rates, quotes, or signed consent forms.
- Claiming Stable capability promotion (R2).
- Treating golden/integration tests as substitute for human usability.
