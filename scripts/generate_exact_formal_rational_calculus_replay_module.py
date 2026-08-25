#!/usr/bin/env python3
"""Thin wrapper around the exact formal calculus plugin."""

from __future__ import annotations

from adapters.common.exact_replay.plugins.formal_rational_calculus import (
    CAPABILITY,
    generate_exact_formal_rational_calculus_module,
)

__all__ = ["CAPABILITY", "generate_exact_formal_rational_calculus_module"]


def main() -> None:
    raise SystemExit(
        "generate_exact_formal_rational_calculus_replay_module is a library entry point; "
        "use adapters.common.exact_replay or kernel_replay"
    )


if __name__ == "__main__":
    main()
