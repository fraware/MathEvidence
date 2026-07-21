# Governance

MathEvidence is governed as shared formal-mathematics infrastructure.

## Maintainer areas (target)

- Core and trust model
- Semantic IR
- Domain checkers
- Backend adapters
- Agent API
- Studio
- Registry
- Foundry and benchmarks
- Security and releases

Stable protocol changes require two approvals from different areas. Domain
semantics require relevant mathematical expertise. No single maintainer may
unilaterally weaken replay, axiom, request-binding, or claim-strength
guarantees.

## Current incubation reality

`.github/CODEOWNERS` is a **single-owner stub** (`@fraware` on all paths).
GitHub teams for the nine areas above do not exist yet on the publishing org.
Treat documentation that describes dual-area review as the **intended** model,
not as an already enforceable process.

Until real teams exist:

- all capabilities remain `"experimental"`;
- stable promotion remains blocked by
  [`docs/validation/stable-capability-checklist.md`](docs/validation/stable-capability-checklist.md)
  and the human gates in
  [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md);
- trust-model or checker weakenings still require explicit scrutiny even if
  GitHub cannot yet enforce two distinct area teams.

## Capability status

Registry `"status": "stable"` is a governance event, not a documentation edit.
Engineering packaging and green local `just check` are insufficient without the
checklist artifacts (external confirmations, review packets, and CI evidence as
required there).
