# Outreach email templates (copy/paste)

Use with [`outreach-checklist.md`](outreach-checklist.md). Replace bracketed
fields. Do **not** invent replies into the logs — wait for real consent.
Project status: [`../STATUS.md`](../STATUS.md).

| Ask | Template |
| --- | --- |
| Problem confirmation (≥3) | Email 1 |
| Workflow win (≥1) | Email 2 |
| Domain packet | Email 3 |
| Studio usability | Email 4 |
| Adoption | Email 5 |
| Federation CSLib | Email 6 |
| Federation lean-smt | Email 7 |
| (P4 federation lean-auto; optional) | Email 8 |

---

## Email 1 — Milestone 0 problem confirmation (G1-A2)

**Subject:** Quick Lean/CAS trust-gap confirmation for MathEvidence?

Hi [Name],

I am working on MathEvidence — a project that lets computational evidence from
CAS backends enter Lean without expanding the Lean TCB (adapters untrusted;
Lean checkers trusted; offline replay).

Would you be willing to confirm (yes/no) whether you hit this class of problem
in your Lean work? Example bottlenecks from our inventory
(`docs/validation/bottlenecks.md`):

- #1 Rational function identity with many denominator conditions
- #3 Exact matrix inverse witness over rationals
- #9 Finite counterexample search for false lemmas

If yes, may we list a short anonymized or named entry in our public
confirmation log? Reply with:

1. Confirms problem? (yes/no)
2. Most relevant bottleneck ID or theme (or “none”)
3. Consent: public name / anonymize / no listing

Repo: https://github.com/fraware/MathEvidence  
Trust model: `docs/SECURITY_AND_TRUST_MODEL.md`

Thank you,
[Your name]

---

## Email 2 — §21.10 workflow win (G1-A3)

**Subject:** Did MathEvidence (or a MathEvidence-shaped path) help a real Lean workflow?

Hi [Name],

Following up on MathEvidence: we need one external confirmation of a **concrete
Lean workflow** problem where certified computational evidence would help (or
already helped via offline replay / discovery / Agent).

If you have 10 minutes, please reply with:

1. The workflow problem (1–3 sentences)
2. Whether MathEvidence helped or would help, and how (replay / discovery / Agent / Studio)
3. Most relevant bottleneck ID from `docs/validation/bottlenecks.md` (if known)
4. Consent to list publicly (yes / anonymize / no)

We will not invent or paraphrase beyond your words. Log template:
`docs/validation/workflow-win-log.md`.

Thank you,
[Your name]

---

## Email 3 — Domain expert statement review (G1-B)

**Subject:** Request: independent review of rational-equality statement interface

Hi [Name],

Could you review our repaired / canonical statement interface for rational
function equality under explicit nonzero denominator conditions?

**Target statement (also in the sample packet):**

`(x : ℚ) → (x - 1 ≠ 0) → (x^2 - 1)/(x - 1) = x + 1`

Materials:

- Rubric + pass bar: `docs/validation/expert-review-rubric.md`
- Packet start (copy, drop `-unsigned` from the new filename):
  `docs/validation/review-packets/SAMPLE-rational-equality-unsigned.md`
- Blank template: `docs/validation/review-packets/TEMPLATE.md`
- Signing steps: copy an unsigned packet, drop `-unsigned`, complete rubric
  scores, and record a real dated signature (see `expert-review-rubric.md`)

We need a real reviewer identity (or consented anonymize), rubric scores meeting
the pass bar, and a dated signature — not a rubber stamp for `stable`.

Thank you,
[Your name]

---

## Email 4 — Studio usability session invite

**Subject:** 20-minute MathEvidence Studio usability session?

Hi [Name],

Would you join a scripted ~20-minute session distinguishing Computed / Tested /
Certified / Ambiguous in MathEvidence Studio (VS Code or Wolfram)? No prior
MathEvidence authorship please.

We record labels + defects only with your consent; we do not invent results.

Facilitator will use `docs/validation/studio/usability/PROTOCOL.md`.

Thank you,
[Your name]

---

## Email 5 — External Lean project adoption (Milestone 2)

**Subject:** Would your Lean project adopt a MathEvidence component?

Hi [Name],

If your project could depend on a MathEvidence IR / checker / tactic / Agent
path (even replay-only), we would like to record a real adoption entry (with
consent) for Milestone 2.

What counts: named component + link (PR/commit) + consent.

Log template: `docs/validation/adoption-log.md`

Thank you,
[Your name]

---

## Email 6 — CSLib federation consume/interop (P4)

**Subject:** MathEvidence federation metadata — CSLib consume review?

Hi [Name],

MathEvidence is packaging a small **interop metadata** envelope so external
projects can share claim/status vocabulary without forking checkers. CSLib
would remain authoritative for its certified algorithms; we only ask whether
CSLib would be willing to **consume** (or dual-review) the shared fields.

Contract sketch:

- Schema: `schemas/federation-metadata.schema.json`
- Notes: `docs/architecture/collaboration-cslib-lean-auto-smt.md`
- Fixture consume example: `evidence/federation/examples/cslib_consume.json`
- Ledger (empty until real agreement): `docs/architecture/federation-agreements.md`
- Status: live federation remains OPEN (`docs/STATUS.md`)

We are **not** asking to replace CSLib checkers or expand Lean TCB.

If open to a short review, please reply with:

1. Willing to discuss consume / provenance reuse? (yes / later / no)
2. Preferred contact or issue tracker for a `federation/cslib` thread
3. Consent to list project + contact on the public agreements ledger when agreed

Thank you,
[Your name]

---

## Email 7 — lean-smt / SMT federation emit (P4)

**Subject:** Emit MathEvidence federation metadata alongside SMT reconstructions?

Hi [Name],

MathEvidence keeps SMT reconstruction authoritative in lean-smt (or your SMT
stack). We would like lean-smt to optionally **emit** shared federation
metadata next to existing proof objects so Studio / Agent can display common
status without claiming your checker.

Contract sketch:

- Schema: `schemas/federation-metadata.schema.json`
- Registry: capability `logic.smt` is federated metadata only
- Fixture emit example: `evidence/federation/examples/lean_smt_emit.json`
- Upgrade path: `evidence/federation/examples/UPGRADE_PATH.md`
- Ledger: `docs/architecture/federation-agreements.md`

If interested, please reply with:

1. Willing to emit metadata (or review the envelope)? (yes / later / no)
2. Schema pin concerns (`federationVersion`, claim/status enums)
3. Consent to list project + contact on the public ledger when agreed

No invented agreements — we only record what you confirm.

Thank you,
[Your name]

---

## Email 8 — lean-auto optional consume (P4)

**Subject:** Optional consume of MathEvidence federation metadata (lean-auto)?

Hi [Name],

Non-goal: embedding lean-auto search into MathEvidence TCB. Optional ask only —
would lean-auto accept **consuming** federation metadata on reconstructed
computational lemmas for display / routing?

Materials: `docs/architecture/collaboration-cslib-lean-auto-smt.md` and
`schemas/federation-metadata.schema.json`.

Reply yes / later / no + consent to ledger listing if ever agreed.

Thank you,
[Your name]
