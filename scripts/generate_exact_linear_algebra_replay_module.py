#!/usr/bin/env python3
"""Thin wrapper around the exact linear-algebra plugin."""

from __future__ import annotations

from adapters.common.exact_replay.plugins.linear_algebra import (
    CAPABILITY,
    generate_exact_linear_algebra_module,
)

__all__ = ["CAPABILITY", "generate_exact_linear_algebra_module"]


def main() -> None:
    raise SystemExit(
        "generate_exact_linear_algebra_replay_module is a library entry point; "
        "use adapters.common.exact_replay or kernel_replay"
    )


if __name__ == "__main__":
    main()
