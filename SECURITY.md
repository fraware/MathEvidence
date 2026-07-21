# Security Policy

## Reporting a vulnerability

Report vulnerabilities **privately**. Do not open a public GitHub issue before
coordinated disclosure.

Preferred channels (use either):

1. **GitHub Security Advisories** — open a private advisory on this repository
   via *Security → Advisories → Report a vulnerability* (or
   `https://github.com/<org>/<repo>/security/advisories/new` once the remote is
   published).
2. **Email** — `security@mathevidence.org`

Include:

- affected component (Core, IR, checker, adapter, evidence parser, CI);
- impact on theorem acceptance or host compromise;
- minimal reproducer or evidence bundle when safe to share;
- Lean toolchain and adapter versions.

## Severity guidance

| Severity | Examples |
| --- | --- |
| Critical | Checker soundness defect; request-binding failure; evidence path that can authorize a false theorem |
| High | Parser crash or RCE in an adapter boundary; secret leakage in evidence or CI |
| Medium | Resource exhaustion without theorem impact; incomplete isolation of backends |
| Low | Documentation that misstates trust boundaries without exploitable path |

Checker soundness defects, request-binding failures, and evidence paths capable
of authorizing a false theorem are **critical**. Follow the incident response
process in `docs/security/SECURITY_AND_TRUST_MODEL.md` §10.

## Scope

In scope:

- Lean packages under `MathEvidence/` (especially Core, IR, Checkers);
- evidence and schema parsers;
- adapter process isolation and credential handling;
- release signing and CI trust controls.

Out of scope for this policy:

- defects that only affect untrusted backend computation without Lean acceptance;
- third-party solvers (Mathematica, SymPy, SageMath) except adapter boundary bugs.

The complete security model is in `docs/security/SECURITY_AND_TRUST_MODEL.md`.
Known preview limitations: `docs/security/KNOWN_TRUST_GAPS.md`.
