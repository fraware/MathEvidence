"""Typed exact-candidate replay generator framework.

Pipeline:

    raw candidate
      -> parse_and_validate
      -> to_replay_ir
      -> render
      -> verify (optional / caller-owned lake path)
      -> bind

ReplayIR is typed. Callers must not insert raw Lean fragments.
"""

from __future__ import annotations

from adapters.common.exact_replay.pipeline import (
    AssuranceEvidence,
    CanonicalCandidate,
    GeneratedModule,
    ReplayIR,
    VerificationResult,
    bind,
    parse_and_validate,
    render,
    to_replay_ir,
    verify,
)
from adapters.common.exact_replay.registry import (
    get_plugin,
    list_plugins,
    register_plugin,
)

# Ensure plugins register on import.
import adapters.common.exact_replay.plugins  # noqa: F401

__all__ = [
    "AssuranceEvidence",
    "CanonicalCandidate",
    "GeneratedModule",
    "ReplayIR",
    "VerificationResult",
    "bind",
    "get_plugin",
    "list_plugins",
    "parse_and_validate",
    "register_plugin",
    "render",
    "to_replay_ir",
    "verify",
]
