#!/usr/bin/env python3
"""Thin SPEC-04 wrapper around the exact rational-equality plugin."""

from __future__ import annotations

from adapters.common.exact_replay.plugins.rational_equality import (
    CAPABILITY,
    generate_exact_rational_equality_module,
)

__all__ = ["CAPABILITY", "generate_exact_rational_equality_module"]


def main() -> None:
    raise SystemExit(
        "generate_exact_rational_equality_replay_module is a library entry point; "
        "use adapters.common.exact_replay or kernel_replay"
    )


if __name__ == "__main__":
    main()
