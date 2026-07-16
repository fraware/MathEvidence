# P2 blocker status — Product expert reviews

**Purpose:** Package unsigned Hypothesis A/B/C packets and Conjecture /
Trace-to-Plan expert-judgment templates so a real reviewer can sign without
guessing paths or pass bars.

**Do not invent** signatures, scores presented as signed, or “approve”
decisions. Leave Decision as `pending` until a human signs.

**Rubric:** [`expert-review-rubric.md`](expert-review-rubric.md)  
**Generic template:** [`review-packets/TEMPLATE.md`](review-packets/TEMPLATE.md)

Status vocabulary:

| Status | Meaning |
| --- | --- |
| `READY_FOR_HUMAN` | Unsigned packet / judgment template ready to fill |
| `BLOCKED_WAITING` | Waiting on a real reviewer signature |
| `ENGINEERING_READY` | Product engineering gates already PASS |

Last packaging pass: 2026-07-16 (engineering only; no signatures invented).

---

## Product 03 — Hypothesis Synthesis (closes M3.EX / criterion 4)

| Interface | Status | Path |
| --- | --- | --- |
| A — rational cancel `{c0}` | `READY_FOR_HUMAN` → sign → rename | [`review-packets/HYPOTHESIS-IFACE-A-rational-cancel-unsigned.md`](review-packets/HYPOTHESIS-IFACE-A-rational-cancel-unsigned.md) |
| B — no redundant hyp | `READY_FOR_HUMAN` → sign → rename | [`review-packets/HYPOTHESIS-IFACE-B-no-redundant-unsigned.md`](review-packets/HYPOTHESIS-IFACE-B-no-redundant-unsigned.md) |
| C — weaker CEX necessity | `READY_FOR_HUMAN` → sign → rename | [`review-packets/HYPOTHESIS-IFACE-C-weaker-cex-unsigned.md`](review-packets/HYPOTHESIS-IFACE-C-weaker-cex-unsigned.md) |
| Product 03 eng criteria 1–3, 5 eng path | `ENGINEERING_READY` | [`products/03_hypothesis_synthesis.md`](products/03_hypothesis_synthesis.md) |

**Signing (each A/B/C):**

1. Copy the `-unsigned.md` file to a new name **without** `-unsigned`
   (e.g. `HYPOTHESIS-IFACE-A-rational-cancel-SIGNED.md` or
   `HYPOTHESIS-IFACE-A-<REVIEWER>.md`).
2. Score every rubric row 0–2; fill Total.
3. Fill Reviewer Name / Affiliation / Area / Consent / Signature date.
4. Clear `pending`; check `revise` or `approve for library consideration`.
5. Pass bar: no zeros; total ≥ 9/12; semantic fidelity ≥ 1; claim strength ≥ 1.

Signed packets are **not** capability `stable` promotion.

---

## Product 04 — Conjecture / Falsification (criterion 4 precision)

| Item | Status | Path |
| --- | --- | --- |
| Precision-rate judgment template | `READY_FOR_HUMAN` | [`review-packets/CONJECTURE-PRECISION-JUDGMENT-unsigned.md`](review-packets/CONJECTURE-PRECISION-JUDGMENT-unsigned.md) |
| Campaign / accounting eng | `ENGINEERING_READY` | Lean `campaign_precision_accounting`; [`products/04_conjecture_falsification.md`](products/04_conjecture_falsification.md) |

**Exit when:** signed judgment records useful precision rate (or revise).

---

## Product 05 — Trace-to-Plan (criterion 5 lemma-graph coherence)

| Item | Status | Path |
| --- | --- | --- |
| Lemma-graph coherence template | `READY_FOR_HUMAN` | [`review-packets/TRACE-TO-PLAN-LEMMA-GRAPH-unsigned.md`](review-packets/TRACE-TO-PLAN-LEMMA-GRAPH-unsigned.md) |
| Multi-step demo eng | `ENGINEERING_READY` | `scripts/run_trace_to_plan_demo.py`; [`products/05_trace_to_plan.md`](products/05_trace_to_plan.md) |

**Exit when:** signed coherence judgment on the multi-step demo plan.

---

## Human todo

```text
[ ] Sign Hypothesis A  → drop -unsigned from filename
[ ] Sign Hypothesis B  → drop -unsigned from filename
[ ] Sign Hypothesis C  → drop -unsigned from filename
[ ] Sign Conjecture precision judgment
[ ] Sign Trace-to-Plan lemma-graph judgment
[ ] Update product reports + matrix only after real signatures
[ ] — Do NOT invent scores or treat unsigned as signed
```

---

## Confirmation (packaging integrity)

| Claim | Truth |
| --- | --- |
| Fake Hypothesis signatures? | **No** — A/B/C remain `-unsigned` / pending |
| Fake Conjecture / Trace judgments? | **No** — templates unsigned |
| Product expert criteria flipped PASS? | **No** — remain OPEN (human) |
