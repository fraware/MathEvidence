# Known limitations and trust gaps

This document lists **honest limitations** of the MathEvidence public preview.
It is part of the trust surface: do not treat experimental capabilities as
stable, and do not invent human confirmations to close the gates below.

All registry capabilities remain `"status": "experimental"` until the
[stable promotion checklist](../validation/stable-capability-checklist.md)
and [governance](../../GOVERNANCE.md) requirements are met with real artifacts.

For a short project status summary, see [`docs/STATUS.md`](../STATUS.md).

---

## Trust invariants (always)

- External backends are untrusted.
- Lean is the sole authority for theorem acceptance.
- A backend Boolean answer is never sufficient evidence.
- Accepted results must be bound to the exact request by cryptographic digest.
- Offline replay must recheck committed evidence without trusting the solver.

Forensic regressions under `tests/forensic/` guard several of these properties.

---

## Current engineering posture

Most historical P0 trust defects identified during the engineering-closure
audit have **engineering fixes** in this branch (request binding, offline digest
recompute, theorem-producing replay, Agent `bundleId`-only surface, typed
digests/receipts, registry-driven Agent dispatch, formal calculus capability
ID). Treat the table below as the **remaining honest gaps**, not a claim that
every historical row is still open.

| Area | Honest status |
| --- | --- |
| Rational equality | Protocol / semantic-boundary **reference**; `externalSearchEssential: false`. Lean can close many identities via `field_simp; ring` independently of backend output — this does **not** prove indispensable external search. |
| Linear algebra / finite CEX | Custom IR + Meta paths cover ordinary examples; Mathlib goal reification completeness is not claimed. |
| `algebra.formal_rational_calculus` | Formal rational-expression calculus only. Analytic `HasDerivAt` / ODE existence is a separate experimental vertical (`analysis.analytic_calculus`). |
| Ideal membership | Experimental Meta + Agent paths with offline fixtures for some backends; not a complete CAS ideal membership stack. |
| Agent API | Experimental orchestration. Public open/inspect/replay accept **`bundleId` only** (raw filesystem paths rejected). Content-addressed store; verified / `claimEstablished` only with content-bound receipt. Optional **dev-only** HMAC/Ed25519 receipt crypto — not production PKI. |
| Evidence bundles | Bundle schema **v0.2** (`.cjson` trees under `evidence/` for full Evidence Bundles). Dual-read retained for migration. |
| CI / `just check` | Workflow **definitions** exist under `.github/workflows/`. Immutable green runs on a release commit are not attested in-repo. Local green `just check` is not promotion evidence. |
| CODEOWNERS | Single-owner incubation stub (`@fraware`). Multi-area dual review is **not** enforceable yet. |
| Stable promotion | **Blocked** until human gates below close. |

---

## Open limitations (do not invent closures)

### Human and governance (blocking stable)

| ID | Limitation | Where to record progress |
| --- | --- | --- |
| H-1 | ≥3 external Milestone 0 user confirmations | `docs/validation/user-confirmation.md` (0 completed) |
| H-2 | ≥1 external workflow-win confirmation (§21.10) | `docs/validation/workflow-win-log.md` |
| H-3 | Independent domain + trust-model reviews for stable promotion | `docs/validation/review-packets/`, `docs/validation/stable-capability-checklist.md` |
| H-4 | Live federation agreements (≥2 external peers) | `docs/architecture/federation-agreements.md` (fixture peers only today) |
| H-5 | Studio usability session results (≥3 completed) | `docs/validation/studio/usability/` |
| H-6 | Expert judgments (hypothesis interfaces, conjecture precision, TTP lemma graph) | Unsigned review packets under `docs/validation/review-packets/` |
| H-7 | Real multi-area CODEOWNERS / dual approval | `.github/CODEOWNERS`, `GOVERNANCE.md` |

### Engineering and product (honest gaps)

| ID | Limitation | Notes |
| --- | --- | --- |
| E-1 | Immutable CI green on a release commit | Workflows exist; attested immutable green is still required before calling engineering gates “complete”. |
| E-2 | Lean toolchain pin | Project remains on the committed `lean-toolchain`; a bump is a deliberate, separately validated change. |
| E-3 | LeanLink native Mathematica bridge | Deferred; live Mathematica transport is `wolframscript` when `MATHEVIDENCE_WOLFRAMSCRIPT` is set. |
| E-4 | Sage rational equality | Declared / placeholder; not advertised as live Agent routing. |
| E-5 | Analytic calculus completeness | `analysis.analytic_calculus` is an experimental fragment, not a complete analysis stack. |
| E-6 | Production receipt PKI | Dev keys under `dev/receipt-keys/` are for local experiments only. |
| E-7 | Foundry frontier / funding exits | Trivial tool-selection lift may be measured on a tiny suite; frontier acceleration and maintenance funding remain open. |

---

## Capability naming notes

- Public calculus capability ID: **`algebra.formal_rational_calculus`**.
- Legacy schema and conformance paths may still use `symbolic_calculus` /
  `calculus` directory names; those are wire/fixture names, not analytic claims.
- Do not advertise a live `analysis.symbolic_calculus` registry ID.

---

## Forensic suite

Trust regressions live under `tests/forensic/`. They assert correct trust
behavior (binding, path rejection, registry/API honesty, and related cases).
A green forensic suite does **not** by itself authorize `"status": "stable"`.
