#!/usr/bin/env python3
"""Measure held-out Agent pass rate vs no-MathEvidence baseline (R4 / M2).

`scripts/run_agent_held_out.py` already scores MathEvidence vs baseline and
fails unless MathEvidence strictly improves. This entrypoint exists so the
gate name matches the workstream deliverable.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "run_agent_held_out.py"


def main() -> int:
    # Execute the held-out runner as __main__ so its SystemExit propagates.
    try:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
