# Human gates — one-sitting runbook (G1)

Engineering on `implement/master-plan` is packaged. This page is the **only**
checklist a human needs to finish **G1-A through G1-D** in one sitting (or one
outreach day plus reviewer callbacks).

**Live status board:** [`g1-blocker-status.md`](g1-blocker-status.md)  
**Do not** set `"status": "stable"` or invent users, signatures, funding, or
session results.

**Time budget (realistic):** ~3–4 hours of human work if contacts respond the
same day; outreach follow-ups may span days. Engineering (G1-D) is already
ready — re-confirm only.

---

## Prep (15 min)

1. Open [`g1-blocker-status.md`](g1-blocker-status.md) and keep it beside you.
2. Re-confirm engineering (G1-D): run `just check`, or confirm latest green CI
   on `implement/master-plan` for `lean.yml`, `adapter-conformance.yml`,
   `offline-replay.yml`, `adversarial.yml`.
3. Skim trust one-pager: `docs/SECURITY_AND_TRUST_MODEL.md`.
4. Have demo ready: `just replay` + optional SymPy discovery
   (`MATHEVIDENCE_DISCOVERY=1`).
5. Open this folder: `docs/validation/`.

---

## G1-A — Outreach (closes S21.10, M0.U; feeds M0.U2) (~60–90 min active)

| Step | Action | Fill / use |
| --- | --- | --- |
| A1 | Select ≥3 non-maintainer contacts | [`outreach-checklist.md`](outreach-checklist.md) candidate boxes |
| A2 | Send problem-confirmation emails | [`outreach-email-templates.md`](outreach-email-templates.md) **Email 1** |
| A3 | Send ≥1 workflow-win ask to a Lean contributor | Templates **Email 2** |
| A4 | On **real consent**, write ≥3 completed rows | [`user-confirmation.md`](user-confirmation.md) → **≥3/3** |
| A5 | On **real consent**, write ≥1 completed win | [`workflow-win-log.md`](workflow-win-log.md) → **≥1 entry** |

Optional same day: adoption ask → [`adoption-log.md`](adoption-log.md) (Milestone 2; not required to finish G1).

**Exit G1-A:** matrix rows S21.10 + M0.U can move to `MET` only with dated
entries (name or anonymize, affiliation, date, consent note). Leave template
rows empty until consent exists.

---

## G1-B — Domain expert packet (closes M0.U2 eng+human; domain checklist box)

| Step | Action | Fill / use |
| --- | --- | --- |
| B1 | Copy SAMPLE → new signed-ready file **without** `-unsigned` | See signing steps below |
| B2 | Score every rubric item; meet pass bar | [`expert-review-rubric.md`](expert-review-rubric.md) |
| B3 | Reviewer signs with real identity + date | Same packet file |

**Signing steps (exact):**

1. Copy
   [`review-packets/SAMPLE-rational-equality-unsigned.md`](review-packets/SAMPLE-rational-equality-unsigned.md)
   to e.g. `review-packets/2026-rational-equality-<REVIEWER>.md`
   (any name **without** the `-unsigned` suffix).
2. Or start from [`review-packets/TEMPLATE.md`](review-packets/TEMPLATE.md) and
   paste SAMPLE metadata (statement, digest, evidence path).
3. Reviewer fills **Scores** (0–2 each), **Reviewer** identity fields, and
   checks **Decision** (`revise` or `approve…` — clear `pending`).
4. Pass bar: no zeros; total ≥ 9 / 12; semantic fidelity and claim strength ≥ 1.
5. Optional same sitting: Hypothesis A/B/C unsigned packets (Product P2 — not
   required for G1-B exit).

**Exit G1-B:** ≥1 signed domain packet on disk; tick Domain review in
[`stable-capability-checklist.md`](stable-capability-checklist.md).

---

## G1-C — Trust-model second-area review

| Step | Action | Artifact |
| --- | --- | --- |
| C1 | Second maintainer from a **different** [`GOVERNANCE.md`](../../GOVERNANCE.md) area reviews replay, digest binding, claim strength | Written note: promotion PR comment **or** `review-packets/trust-model-YYYY-MM-DD.md` from [`review-packets/TRUST-MODEL-TEMPLATE.md`](review-packets/TRUST-MODEL-TEMPLATE.md) |
| C2 | Tick checklist box “Trust-model review” | [`stable-capability-checklist.md`](stable-capability-checklist.md) |

**Exit G1-C:** two distinct maintainer areas named on the record (e.g. Domain
checkers / Semantic IR for G1-B, plus Core and trust model or Security for
G1-C).

---

## G1-D — Engineering verification (already ready; re-confirm only)

```text
just check
```

Confirm green CI on the branch for:

| Workflow | Covers |
| --- | --- |
| `lean.yml` | soundness build, import-boundary, sorry-audit |
| `adapter-conformance.yml` | RFC 0001 conformance, registry, Agent tests |
| `offline-replay.yml` | SymPy/Mathematica offline replay + Tactic.Examples |
| `adversarial.yml` | adversarial seed catalog |

Engineering boxes on
[`stable-capability-checklist.md`](stable-capability-checklist.md) are already
`[x]` — do **not** re-litigate. A green `just check` does **not** authorize
`"status": "stable"`.

---

## After G1 (not this packaging; do not invent)

| Next | When | Doc |
| --- | --- | --- |
| G2 ADR wolframscript | Engineering sibling track | ADR + roadmap/matrix (separate) |
| G3 Stable promotion PR | Only after G1-A–D (+ G2) | [`stable-promotion-draft.md`](stable-promotion-draft.md) |
| P1 Studio S01–S03 | Prefer after G3; can parallel if facilitators free | [`studio/usability/PROTOCOL.md`](studio/usability/PROTOCOL.md) |

---

## Still intentionally human / external (not G1 alone)

| Row | Why |
| --- | --- |
| Live federation ≥2 peers | Maintainer agreements — `docs/architecture/federation-agreements.md` |
| Funding / frontier acceleration | Org / research — `docs/foundry/exit-gate-status.md` |
| Trained Foundry selector uplift | Research train/eval — not packaging |
| Studio usability session results | P1 — do not invent |

---

## Exit when G1 is done

- [`user-confirmation.md`](user-confirmation.md) ≥3 completed (real consent)
- [`workflow-win-log.md`](workflow-win-log.md) ≥1 completed (real consent)
- ≥1 signed domain review packet (not SAMPLE-unsigned)
- Trust-model second-area note filed (PR or `trust-model-*.md`)
- G1-D re-confirmed (`just check` / green CI)
- Update [`g1-blocker-status.md`](g1-blocker-status.md) rows to reflect reality
- Then — and only then — open promotion PR using
  [`stable-promotion-draft.md`](stable-promotion-draft.md) (G3; after G2)
