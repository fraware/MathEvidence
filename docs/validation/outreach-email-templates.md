# Outreach email templates (copy/paste)

Use with `outreach-checklist.md`. Replace bracketed fields. Do **not** invent
replies into the logs — wait for real consent.

---

## Email 1 — Milestone 0 problem confirmation

**Subject:** Quick Lean/CAS trust-gap confirmation for MathEvidence?

Hi [Name],

I am working on MathEvidence — a project that lets computational evidence from
CAS backends enter Lean without expanding the Lean TCB (adapters untrusted;
Lean checkers trusted; offline replay).

Would you be willing to confirm (yes/no) whether you hit this class of problem
in your Lean work? Example bottlenecks are listed in our inventory (rational
identities with side conditions, exact linear algebra witnesses, finite
counterexamples, etc.).

If yes, may we list a short anonymized or named entry in our public
confirmation log? Reply with:

1. Confirms problem? (yes/no)
2. Most relevant bottleneck theme (or “none”)
3. Consent: public name / anonymize / no listing

Repo: https://github.com/fraware/MathEvidence  
Trust model: `docs/SECURITY_AND_TRUST_MODEL.md`

Thank you,
[Your name]

---

## Email 2 — §21.10 workflow win

**Subject:** Did MathEvidence (or a MathEvidence-shaped path) help a real Lean workflow?

Hi [Name],

Following up on MathEvidence: we need one external confirmation of a **concrete
Lean workflow** problem where certified computational evidence would help (or
already helped via offline replay / discovery / Agent).

If you have 10 minutes, please reply with:

1. The workflow problem (1–3 sentences)
2. Whether MathEvidence helped or would help, and how (replay / discovery / Agent / Studio)
3. Consent to list publicly (yes / anonymize / no)

We will not invent or paraphrase beyond your words.

Thank you,
[Your name]

---

## Email 3 — Domain expert statement review

**Subject:** Request: independent review of rational-equality statement interface

Hi [Name],

Could you review our repaired / canonical statement interface for rational
function equality under explicit nonzero denominator conditions?

Materials:

- Rubric: `docs/validation/expert-review-rubric.md`
- Packet start: `docs/validation/review-packets/SAMPLE-rational-equality-unsigned.md`
- Template: `docs/validation/review-packets/TEMPLATE.md`

We need a real reviewer identity (or consented anonymize) and rubric scores —
not a rubber stamp for `stable`.

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
