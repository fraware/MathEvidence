# Trust-model review template (G1-C)

Copy to `docs/validation/review-packets/trust-model-YYYY-MM-DD.md` **or** paste
the completed table into the future stable-promotion PR description / comment.

**Requirements:**

- Reviewer is a maintainer from a **different** area than the domain packet
  signer ([`GOVERNANCE.md`](../../../GOVERNANCE.md) areas).
- Review confirms replay, digest binding, and claim-strength guarantees are
  **not** weakened for `algebra.rational_equality`.
- Do **not** invent a signature. Do **not** treat this as capability `stable`.

## Metadata

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Capability | algebra.rational_equality |
| Related domain packet | docs/validation/review-packets/… (signed packet path, if any) |
| Rubric / trust doc | docs/SECURITY_AND_TRUST_MODEL.md |

## Checklist (reviewer must answer yes/no + note)

| Question | Yes / No | Notes |
| --- | --- | --- |
| Offline replay path remains the authoritative check for committed bundles? | | |
| Request digest binding is preserved (evidence tied to request)? | | |
| Claim strength cannot silently upgrade (e.g. candidate → soundResult)? | | |
| Adapters remain untrusted; Lean checker remains trusted? | | |
| No new axiom / sorry / TCB expansion introduced by this capability path? | | |

## Reviewer

| Field | Value |
| --- | --- |
| Name | |
| Maintainer area (must differ from domain signer) | e.g. Core and trust model |
| Domain signer area (for contrast) | e.g. Domain checkers / Semantic IR |
| Consent to list publicly | yes / no / anonymize |
| Signature date | YYYY-MM-DD |

## Decision

- [ ] pending
- [ ] concerns (list below — block promotion until resolved)
- [ ] approve trust-model second-area review (not capability-stable by itself)

## Comments

_
