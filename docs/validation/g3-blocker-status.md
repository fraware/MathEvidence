# G3 blocker status — stable promotion of `algebra.rational_equality`

**Purpose:** Track readiness for the v0.1 / §21.9 stable flip. Engineering
packaging for the promotion PR exists; **G3 must not run until G1 human gates
close** (and G2 is done).

**Status:** `BLOCKED_WAITING` on **G1** (human outreach + signed domain packet +
trust-model second-area review).

**Do not** open a stable promotion PR.  
**Do not** edit `registry/capabilities/algebra.rational_equality.json` to
`"status": "stable"`.  
**Do not** invent users, signatures, agreements, or funding to unblock this.

| Dependency | Status | Board / artifact |
| --- | --- | --- |
| G1-A Outreach (≥3 users + workflow win) | `BLOCKED_WAITING` | [`g1-blocker-status.md`](g1-blocker-status.md) |
| G1-B Domain signed packet | `BLOCKED_WAITING` | same |
| G1-C Trust-model second-area review | `BLOCKED_WAITING` | same |
| G1-D `just check` / CI re-confirm | `ENGINEERING_READY` | `just check` |
| G2 wolframscript ADR | **done** (prior eng) | ADR 0004 / matrix M0.LL / M1.LL |
| Stable promotion draft (PR body) | `READY_FOR_HUMAN` after G1 | [`stable-promotion-draft.md`](stable-promotion-draft.md) — still accurate; JSON remains `experimental` |
| Capability JSON flip | `BLOCKED_WAITING` | Only in a later PR after G1 artifacts exist |

## Confirmation

| Claim | Truth |
| --- | --- |
| Stable PR opened? | **No** |
| Capability JSON flipped? | **No** — remains `experimental` |
| Draft still matches checklist? | **Yes** — human gates listed in draft remain OPEN |
