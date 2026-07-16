"""Foundry pipelines — post-acceptance corpus construction only.

HARD INVARIANT: nothing in this package may be imported by Lean checkers,
Core, IR, or theorem-acceptance paths. Pipelines consume evidence and capture
records after orchestration decisions; they never feed ResultStatus.
"""

from __future__ import annotations

from foundry.pipelines.build_corpus import build_corpus
from foundry.pipelines.common import CONTENT_DIGEST_ALG

__all__ = [
    "build_corpus",
    "CONTENT_DIGEST_ALG",
]
