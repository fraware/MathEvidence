"""Built-in exact replay plugins."""

from __future__ import annotations

from adapters.common.exact_replay.plugins import analytic_calculus as analytic_calculus
from adapters.common.exact_replay.plugins import finite_counterexample as finite_counterexample
from adapters.common.exact_replay.plugins import formal_rational_calculus as formal_rational_calculus
from adapters.common.exact_replay.plugins import ideal_membership as ideal_membership
from adapters.common.exact_replay.plugins import linear_algebra as linear_algebra
from adapters.common.exact_replay.plugins import rational_equality as rational_equality

__all__ = [
    "analytic_calculus",
    "finite_counterexample",
    "formal_rational_calculus",
    "ideal_membership",
    "linear_algebra",
    "rational_equality",
]
