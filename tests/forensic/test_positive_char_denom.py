"""Forensic: positive-characteristic denom cast must not treat Nat≠0 as field≠0.

P0-10 — Eval.lean `.rat n d` uses `d = 0` / `d ≠ 0` on Nat. In characteristic p,
casting p yields 0 in the field while Nat d ≠ 0.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "MathEvidence" / "IR" / "RationalExpr" / "Eval.lean"


def test_eval_rat_literal_requires_char_zero_or_cast_nonzero() -> None:
    text = EVAL.read_text(encoding="utf-8")
    # Forbidden underspecified pattern without CharZero / cast guard nearby.
    has_char_zero = "CharZero" in text
    has_cast_nonzero = "(d : α) ≠ 0" in text or "≠ (0 : α)" in text
    has_q_only = "evalℚ" in text and "Field α" not in text.split("def eval")[1][:400]
    # Accept either ℚ-only evaluator policy or CharZero + cast nonzero.
    assert has_char_zero or has_cast_nonzero or (
        "restrict" in text.lower() and "ℚ" in text
    ), (
        "P0-10: Eval.lean still uses Nat denominator checks without CharZero / "
        "cast-nonzero / ℚ-only policy. See docs/security/KNOWN_TRUST_GAPS.md.\n"
        f"charZero={has_char_zero} castNonzero={has_cast_nonzero} qOnly={has_q_only}"
    )


def test_defined_rat_does_not_only_check_nat() -> None:
    text = EVAL.read_text(encoding="utf-8")
    # The bare `| .rat _ d => d ≠ 0` is insufficient for generic fields.
    if "| .rat _ d => d ≠ 0" in text or "| .rat _ d => d != 0" in text:
        assert "CharZero" in text or "evalQ" in text or "ℚ" in text.split("Defined")[1][:800], (
            "P0-10: Defined for .rat only checks Nat ≠ 0 without CharZero policy"
        )
