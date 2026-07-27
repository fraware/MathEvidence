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

## Current E2E status

Wave 4 (ME-RV-040/041): Meta reification returns proof objects; the
`mathevidence_linear_algebra` tactic closes via Bridge /
`replaySound` / `checkBool_sound`. Determinant Mathlib transport is
general-n (`det_of_isDetIdentity`). Independent `native_decide` is not the
final theorem authority. Kernel-replay Certification Records are produced by
`adapters/common/kernel_replay.py` for LA capabilities.

### Practical det size limit (intentional resource policy)

`MathEvidence.IR.MatrixExpr.defaultSizeLimit` is **64 entries**. Combined with
factorial Laplace expansion cost in the det witness path, this bounds practical
matrix order. That bound is an **intentional resource / DoS policy**, not a
missing soundness theorem: Bridge proves `det_of_isDetIdentity` for all
`Fin n` within the accepted size. Oversized inputs are rejected before replay.

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
