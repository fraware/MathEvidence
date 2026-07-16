"""Resource limits for adapter processes.

See ``docs/architecture/process-isolation.md`` for the normative CPU / memory /
wall / output budget contract and cancel→kill behavior.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from adapters.common.errors import stable_error

# Defaults aligned with registry capability ``limits`` and request resourcePolicy.
DEFAULT_MAX_WALL_TIME_MS = 60_000
DEFAULT_MAX_OUTPUT_BYTES = 4_194_304
DEFAULT_MAX_REQUEST_BYTES = 1_048_576
DEFAULT_MAX_NESTING_DEPTH = 64
# Soft advisory defaults when OS cgroups are unavailable (documented; not enforced
# by the Python supervisor on all platforms).
DEFAULT_MAX_CPU_TIME_MS = 60_000
DEFAULT_MAX_MEMORY_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class ResourceLimits:
    max_wall_time_ms: int = DEFAULT_MAX_WALL_TIME_MS
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES
    max_nesting_depth: int = DEFAULT_MAX_NESTING_DEPTH
    max_cpu_time_ms: int | None = DEFAULT_MAX_CPU_TIME_MS
    max_memory_bytes: int | None = DEFAULT_MAX_MEMORY_BYTES

    @classmethod
    def from_policy(cls, policy: dict[str, object] | None) -> ResourceLimits:
        if not policy:
            return cls()
        return cls(
            max_wall_time_ms=int(policy.get("maxWallTimeMs", DEFAULT_MAX_WALL_TIME_MS)),  # type: ignore[arg-type]
            max_output_bytes=int(policy.get("maxOutputBytes", DEFAULT_MAX_OUTPUT_BYTES)),  # type: ignore[arg-type]
            max_cpu_time_ms=(
                int(policy["maxCpuTimeMs"])  # type: ignore[arg-type]
                if "maxCpuTimeMs" in policy
                else DEFAULT_MAX_CPU_TIME_MS
            ),
            max_memory_bytes=(
                int(policy["maxMemoryBytes"])  # type: ignore[arg-type]
                if "maxMemoryBytes" in policy
                else DEFAULT_MAX_MEMORY_BYTES
            ),
        )


class ResourceTracker:
    def __init__(self, limits: ResourceLimits) -> None:
        self.limits = limits
        self._t0 = time.monotonic()
        self.cancelled = False

    def check(self) -> None:
        if self.cancelled:
            raise stable_error("cancelled", "operation cancelled")
        elapsed_ms = int((time.monotonic() - self._t0) * 1000)
        if elapsed_ms > self.limits.max_wall_time_ms:
            raise stable_error(
                "resource_limit_exceeded",
                f"wall time exceeded ({elapsed_ms}ms > {self.limits.max_wall_time_ms}ms)",
                details={"kind": "wall_time", "elapsedMs": elapsed_ms},
            )

    def ensure_output_size(self, nbytes: int) -> None:
        if nbytes > self.limits.max_output_bytes:
            raise stable_error(
                "resource_limit_exceeded",
                f"output size exceeded ({nbytes} > {self.limits.max_output_bytes})",
                details={"kind": "output_bytes", "bytes": nbytes},
            )

    def usage(self) -> dict[str, int]:
        return {
            "wallTimeMs": int((time.monotonic() - self._t0) * 1000),
        }
