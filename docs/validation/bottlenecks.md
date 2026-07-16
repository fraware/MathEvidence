# Computational Bottleneck Inventory (Milestone 0)

Real computational proof obligations that Lean users and libraries repeatedly
hit, where external exact computation would be materially useful **if** results
enter Lean through checkable evidence. Sources include Mathlib formalization
practice, theorem-proving folklore, and CAS–ITP integration literature. Each
row records a typical workaround today.

| # | Bottleneck | Domain | Typical Lean-only workaround | Why external computation helps |
| --- | --- | --- | --- | --- |
| 1 | Rational function identity with many denominator conditions | Algebra | Manual `field_simp` / `ring` case splits | CAS normalizes; Lean must still check denominators |
| 2 | Partial-fraction style equalities on `ℚ(x)` | Algebra | Hand-crafted algebraic manipulation | Candidate factorization + Lean identity check |
| 3 | Exact matrix inverse witness over rationals | Linear algebra | Adjugate by hand or `simp` blowup | CAS inverse; Lean verifies `A * B = I` |
| 4 | Exact solution of dense linear systems | Linear algebra | Gaussian elimination by tactics | Witness vector + residual proof |
| 5 | Kernel / nullspace vector for exact matrices | Linear algebra | Manual linear dependence proofs | Candidate kernel vector checked in Lean |
| 6 | Determinant identities for structured matrices | Linear algebra | Cofactor expansion proof | Candidate det + polynomial identity check |
| 7 | Polynomial identity after expansion (high degree) | Algebra | `ring` timeout / memory | Normalized certificate / sparse witness |
| 8 | Gröbner-derived membership for ideal problems | Algebra | Re-prove reductions manually | External Gröbner + reconstructible certificate (federate, don't replace) |
| 9 | Finite counterexample search for false lemmas | Logic / algebra | Random `native_decide` attempts | Typed finite witness evaluated in Lean |
| 10 | Disproving universal claims on small finite types | Combinatorics | Exhaustive `decide` when feasible | Guided search + certified witness |
| 11 | Trig / rational identities after Weierstrass substitution | Analysis prep | Manual rewriting | Candidate equality under explicit domains |
| 12 | Derivative candidate verification | Calculus | Unfold `deriv` definitions | Candidate derivative checked symbolically in Lean |
| 13 | Antiderivative verification on an interval | Calculus | FTC proofs by hand | Candidate + domain conditions checked |
| 14 | Recurrence closed-form checking | Discrete math | Induction with painful algebra | Candidate formula + inductive obligation evidence |
| 15 | Linear ODE candidate + IC checking | DE | Manual verifying substitution | Plug-in residual certificate |
| 16 | Resultant / eliminant computations | Algebra | Expanding huge determinants | External resultant + Lean check of key identity |
| 17 | Exact eigenvalue-free claims (charpoly identities) | Linear algebra | Charpoly expansion | Candidate polynomial + evaluation checks |
| 18 | Integer relation / lattice hints turned into proofs | Number theory | Guess then prove | Untrusted hint → proof plan (Trace-to-Plan) |
| 19 | SAT-backed finite combinatorial search | Logic | Custom encoding per problem | Federate SAT checker metadata / witnesses |
| 20 | SMT-backed linear/arithmetic side conditions | Logic | Manual inequality chaining | Lean-SMT reconstruction remains authoritative; MathEvidence shares status |
| 21 | Pseudo-Boolean counting constraints in formal models | Logic | Ad-hoc encodings | Capability metadata federation |
| 22 | Large rational coefficient normalization | Algebra | Kernel blowup on numerals | Backend normalizes; Lean checks reduced form |
| 23 | Condition mining for equalities that hold only off poles | Algebra | User invents hypotheses | Hypothesis synthesis + sufficiency proof |
| 24 | Deleting redundant hypotheses after repair | Algebra | Manual cleanup | Certified deletion / lattice artifact |
| 25 | Tool selection for AI agents (which CAS op?) | Agent | Trial-and-error tool calls | Registry + conformance-backed operations |

## Notes

- Items 8, 19–21 are **federation** targets (Milestone 4), not “replace the
  specialized checker.”
- Items 12–15 are Milestone 5 verticals; listed because they already appear as
  real bottlenecks in hybrid CAS workflows.
- Milestone 1 focuses on row 1 (RFC 0001) as the reference path.

## Maintenance

Add new bottlenecks with source citations when available. Retire rows only when
a stable MathEvidence capability covers them with measured adoption.
