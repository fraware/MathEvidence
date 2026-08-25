#!/usr/bin/env python3
"""Thin SPEC-07 Track B wrapper around the exact analytic calculus plugin."""

from __future__ import annotations

from adapters.common.exact_replay.plugins.analytic_calculus import (
    CAPABILITY,
    generate_exact_analytic_calculus_module,
)

__all__ = ["CAPABILITY", "generate_exact_analytic_calculus_module"]


def main() -> None:
    raise SystemExit(
        "generate_exact_analytic_calculus_replay_module is a library entry point; "
        "use adapters.common.exact_replay or kernel_replay"
    )


if __name__ == "__main__":
    main()
