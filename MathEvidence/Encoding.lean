/-
Copyright (c) 2026 MathEvidence contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: MathEvidence contributors
-/
import MathEvidence.Encoding.Rat
import MathEvidence.Encoding.Matrix
import MathEvidence.Encoding.Finite
import MathEvidence.Encoding.Polynomial
import MathEvidence.Encoding.Examples

/-!
# MathEvidence.Encoding

Mandatory package separating executable IR from Mathlib-facing interpretation
theorems (master closure spec §5). Checkers and tactics should cite these
modules for reification correctness rather than ad-hoc bridges.

Mathlib densify/quote (`Encoding.Matrix`), Fin/Bool/bounded CEX bridges
(`Encoding.Finite`), and sparse↔`Polynomial`/`MvPolynomial` evaluation identities
(`Encoding.Polynomial`) live here; `Encoding.Examples` fails the Lake build if
those bridges regress.
-/
