"""Cross-language error taxonomy parity (Lean ErrorCode ↔ Python STABLE_CODES)."""

from __future__ import annotations

import re
from pathlib import Path

from adapters.common.errors import STABLE_CODES

ROOT = Path(__file__).resolve().parents[2]
ERROR_CODE_LEAN = ROOT / "MathEvidence" / "Core" / "ErrorCode.lean"


def _lean_wire_codes() -> set[str]:
    text = ERROR_CODE_LEAN.read_text(encoding="utf-8")
    # Match ErrorCode.toWire arms: | .foo => "wire_name"
    return set(re.findall(r'=>\s*"([a-z0-9_]+)"', text.split("def ErrorCode.toWire")[1].split("def ErrorCode.ofWire?")[0]))


def test_lean_error_codes_cover_python_stable_codes() -> None:
    lean = _lean_wire_codes()
    missing = sorted(set(STABLE_CODES) - lean)
    assert not missing, f"Lean ErrorCode.toWire missing Python STABLE_CODES: {missing}"


def test_python_stable_codes_cover_lean_wires() -> None:
    lean = _lean_wire_codes()
    extra = sorted(lean - set(STABLE_CODES))
    assert not extra, f"Lean ErrorCode.toWire has codes absent from Python STABLE_CODES: {extra}"
