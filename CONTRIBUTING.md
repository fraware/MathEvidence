# Contributing

Contributions must preserve the project trust model and repository dependency
rules. Read [`docs/security/KNOWN_TRUST_GAPS.md`](docs/security/KNOWN_TRUST_GAPS.md)
and [`docs/STATUS.md`](docs/STATUS.md) before proposing promotions or
trust-surface changes.

## Before opening a pull request

1. Identify the owning product and capability.
2. Add or update the normative specification under `docs/` (and RFCs when the
   protocol changes).
3. Include positive, negative, adversarial, and replay tests as appropriate.
4. State whether the change modifies semantics, evidence, assurance, or
   compatibility.
5. Run the local engineering gate: `just check`. For trust-sensitive changes,
   also run `pytest tests/forensic -q`.

Cross-cutting protocol changes require an RFC. Stable checker changes require
independent review from a domain maintainer and a trust-model maintainer once
multi-area ownership is real (see below).

## Ownership reality

`.github/CODEOWNERS` currently routes all paths to a **single owner** as an
incubation stub. That is not multi-area governance. Dual-area review for
trust/checker changes is a governance goal, not an enforceable GitHub team
setup yet. See [`GOVERNANCE.md`](GOVERNANCE.md).

Do **not** flip any capability `"status": "stable"` from a contribution alone.
Follow [`docs/validation/stable-capability-checklist.md`](docs/validation/stable-capability-checklist.md)
with real human artifacts.

## Agent and evidence conventions

- Public Agent open/inspect/replay accept opaque **`bundleId`** values only —
  never filesystem paths.
- Prefer Evidence Bundle **v0.2** (`.cjson`) layouts under `evidence/`.
- Formal rational calculus capability ID is `algebra.formal_rational_calculus`.

## Conduct and security

- Follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- Report vulnerabilities privately per [`SECURITY.md`](SECURITY.md).
