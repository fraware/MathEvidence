# External validation outreach checklist

Operational companion to `docs/validation/user-confirmation.md`.
Completing outreach is **human work**; this checklist only makes the process
repeatable. Do not invent confirmations.

## Before contacting anyone

- [ ] Bottleneck inventory reviewed (`docs/validation/bottlenecks.md`)
- [ ] Trust-model one-pager ready (`docs/SECURITY_AND_TRUST_MODEL.md` § summary)
- [ ] Demo path ready: offline `mathevidence replay` + optional discovery with
      SymPy on a laptop (`MATHEVIDENCE_DISCOVERY=1`)
- [ ] Consent language prepared (public listing vs anonymize)

## Candidate sources (≥3 distinct non-maintainers)

- [ ] Mathlib / Lean Zulip domain experts (algebra / analysis as relevant)
- [ ] Educators teaching Lean+CAS workflows
- [ ] Library authors with computational proof obligations
- [ ] Industry/research groups using Mathematica↔Lean bridges

## Per contact

1. Share README + trust boundary diagram (adapters untrusted).
2. Ask which bottlenecks match their work (IDs from bottlenecks.md).
3. Record yes/no on problem confirmation.
4. Obtain consent for `user-confirmation.md` listing.
5. File entry only after consent; leave template rows empty otherwise.

## Exit metric

| Metric | Target |
| --- | --- |
| Confirmations in `user-confirmation.md` | ≥ 3 completed |
| Maintainer-only confirmations | do **not** count |

## Status

Outreach pending. Confirmations completed: see summary table in
`user-confirmation.md` (currently 0/3).
