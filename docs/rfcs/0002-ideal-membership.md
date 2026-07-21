# RFC 0002 — Ideal Membership Certificates

Status: draft; native witness checker partial  
Owner: MathEvidence federation / algebra maintainers  
Capability: `algebra.groebner_membership`

## Summary

This RFC scopes a federated ideal-membership evidence format for polynomial
ideals. Given polynomials `f` and generators `{g_i}`, a certificate consists of
multiplier polynomials `{q_i}` such that:

```text
f = sum_i q_i * g_i
```

If the equality is reconstructed by an authoritative external Lean Gröbner
project, MathEvidence records the claim class **membership only**:

```text
f ∈ Ideal.span {g_i}
```

MathEvidence must not claim a canonical Gröbner basis, minimal generators,
radical membership, ideal equality, completeness, or optimality from this
certificate.

## Certificate Shape

The certificate payload is:

- `target`: sparse polynomial `f`;
- `generators`: sparse polynomials `g_i`;
- `multipliers`: sparse polynomials `q_i`;
- `provenance`: backend/adapter metadata for the untrusted witness producer;
- `claimClass`: `witness` or `soundResult`, depending on external replay status.

The shared JSON schema lives at
`schemas/ideal-membership-certificate.schema.json`. The structural Lean syntax
lives at `MathEvidence.IR.Polynomial.Syntax`, and the native witness identity
checker lives at `MathEvidence.Checkers.IdealMembership.Check`.

## Federation Model

Existing Lean Gröbner projects remain authoritative for proof reconstruction.
MathEvidence provides:

- registry discovery for `algebra.groebner_membership`;
- shared provenance metadata using `schemas/federation-metadata.schema.json`;
- sparse-polynomial syntax scaffolding for future interop;
- fixture-only examples until maintainers opt into live emit/consume.

External projects should be able to emit or consume MathEvidence metadata
without replacing their own search/checking infrastructure. MathEvidence only
trusts the checked identity `f = sum_i q_i * g_i`, not a backend Gröbner basis.

## Gap Analysis

Open gaps:

- no parser from common CAS syntax into the sparse polynomial schema;
- no live maintainer agreement for Gröbner federation;
- no Sage/Mathematica live ideal-membership conformance evidence;
- numeric >=50-task harness present (55 tasks; skip/xfail honesty); SymPy always-on;
  Mathematica/Sage live only when env/binary present (not advertised otherwise);
  univariate Mathlib Ideal.span Meta auto-bridge covers singleton and two-generator spans;
  MvPolynomial (Fin 2/3/4) Meta reification covers monomial gens and non-monomial
  principal gens via grevlex exact ℤ division when a sparse quotient exists
  (Fin 4 Meta close wired; no Gröbner completeness; n>4 unsupported);
  committed Mathematica/Sage offline fixtures for ≥2 shared requests (live differential blocked without host tools);
- no full conformance suite for variable ordering, coefficient domains, or
  normalization beyond the current small witness benchmark;
- no proof that the sparse syntax maps faithfully to an external project's
  polynomial representation.

Until those gaps close, registry status remains experimental/federated and live
federation must remain OPEN.

## Non-Goals

- Do not replace Mathlib or external Gröbner implementations.
- Do not claim analytic, numerical, or approximate polynomial solving semantics.
- Do not claim ideal equality, radical membership, or basis minimality.
- Do not invent maintainer sign-off or user confirmations.
