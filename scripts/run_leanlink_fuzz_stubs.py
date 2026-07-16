#!/usr/bin/env python3
"""CI entrypoint for LeanLink fuzz stubs (native bridge stays disabled)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.mathematica.leanlink_fuzz import (  # noqa: E402
    MAX_FUZZ_BYTES,
    classify_fuzz_blob,
    load_config_safely,
    run_corpus,
)


def main() -> int:
    cfg = load_config_safely(None)
    if cfg.enabled:
        print("FAIL: LeanLink enabled without review", file=sys.stderr)
        return 1
    results = run_corpus()
    oversized = classify_fuzz_blob(b"\xff" * (MAX_FUZZ_BYTES + 8), name="generated_oversized")
    if oversized.accepted_as_bridge_input:
        print("FAIL: oversized accepted", file=sys.stderr)
        return 1
    print(
        f"leanlink fuzz stubs ok ({len(results)} corpus files; "
        f"bridge disabled; oversized rejected)"
    )
    for r in results:
        print(f"  {r.name}: reject ({r.reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
