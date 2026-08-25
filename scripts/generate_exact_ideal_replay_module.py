#!/usr/bin/env python3
"""Generate an exact ideal-membership Lean replay module.

Thin SPEC-03 wrapper around ``adapters.common.exact_replay`` ideal plugin.
This generator is untrusted. The generated module reconstructs the exact
mathematical claim and witness; request identity is recomputed inside Lean
from reconstructed wire-semantic fields before the checker can establish a
theorem. OfflineFixtures are not used by this path.
"""

from __future__ import annotations

from typing import Any

from adapters.common.exact_replay.plugins.ideal_membership import (
    CAPABILITY,
    generate_exact_ideal_membership_module,
)

__all__ = ["CAPABILITY", "generate_exact_ideal_membership_module"]


def main() -> None:
    raise SystemExit(
        "generate_exact_ideal_replay_module is a library entry point; "
        "use adapters.common.exact_replay or kernel_replay"
    )


if __name__ == "__main__":
    main()
