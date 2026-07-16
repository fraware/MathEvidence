# Expert review rubric (repaired statements)

Use this rubric when a human expert reviews Lean statements repaired or
proposed via MathEvidence (Hypothesis Synthesis, discovery, or Studio).

**This file does not record approvals.** Completed reviews belong in
`docs/validation/review-packets/` using the packet template.

## Scope

- Capability / claim under review
- Statement text (Lean + informal gloss)
- Evidence bundle path(s) and request digest(s)
- Assurance mode (`kernel_replay` expected for v0.1 algebra)

## Scoring (each 0–2)

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| **Semantic fidelity** | Wrong claim vs informal intent | Minor mismatch | Matches intent |
| **Side conditions** | Missing / wrong poles | Partial | Explicit, necessary & sufficient for the claim |
| **Claim strength** | Overclaims (e.g. identity at poles) | Hedge unclear | `soundResult` / witness correctly scoped |
| **Checker fit** | Wrong capability / IR | Borderline | IR + checker appropriate |
| **Replay** | Does not replay | Replays with caveats | Offline replay clean |
| **Library interface** | Not usable as stated | Needs rename/hyps | Ready for library PR (pending owner) |

**Pass bar:** no zeros; total ≥ 9 / 12; semantic fidelity and claim strength ≥ 1.

## Required reviewer notes

1. What would you change before merging into a library?
2. Any pole / branch / totality concern the certificate hides?
3. Is minimality of conditions claimed? (Must be **no** unless proved.)

## Non-goals

- Do not treat adapter provenance as a proof.
- Do not mark capability `stable` from a single packet.
- Do not invent reviewer identities.
