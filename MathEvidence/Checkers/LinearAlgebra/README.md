# LinearAlgebra checker

## Claim

Establishes **witness-strength** exact linear-algebra facts over `ℚ`
(Project Spec §11.2):

| Operation | Established fact |
| --- | --- |
| `inverse_witness` | `A B = I` and `B A = I` |
| `system_solution` | `A x = b` |
| `kernel_vector` | `A v = 0` with `v ≠ 0` |
| `det_identity` | `det A = d` |

## Assurance

- Mode: `kernel_replay` (exact rational arithmetic in Lean).
- Backends are untrusted generators only.

## Explicitly out of scope

- Completeness of a kernel **basis**
- Matrix **rank** claims
- Full parametric **solution families**

Those require separate stronger claim classes and additional evidence.

## Algorithm

1. Bind certificate `requestDigest` to the request digest.
2. Reject ill-formed / oversized matrices and zero denominators.
3. Recompute the operation-specific equality over `ℚ`.
4. Accept only when the witness checks succeed.

## Offline replay

`Replay.lean` reruns `check` with no adapter invocation.
Hand-written fixtures live in `Tests.lean` and discharge with `native_decide`.

## Axiom / `sorry` audit

- Project `sorry`: none in this checker or `IR/MatrixExpr`.
- Project-specific axioms: none.
