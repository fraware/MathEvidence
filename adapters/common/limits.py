"""Resource limits for adapter processes."""

from __future__ import annotations

import time
from dataclasses import dataclass

from adapters.common.errors import stable_error


@dataclass(frozen=True)
class ResourceLimits:
    max_wall_time_ms: int = 60_000
    max_output_bytes: int = 4_194_304
    max_request_bytes: int = 1_048_576
    max_nesting_depth: int = 64
    max_cpu_time_ms: int | None = None
    max_memory_bytes: int | None = None

    @classmethod
    def from_policy(cls, policy: dict[str, object] | None) -> ResourceLimits:
        if not policy:
            return cls()
        return cls(
            max_wall_time_ms=int(policy.get("maxWallTimeMs", 60_000)),  # type: ignore[arg-type]
            max_output_bytes=int(policy.get("maxOutputBytes", 4_194_304)),  # type: ignore[arg-type]
            max_cpu_time_ms=(
                int(policy["maxCpuTimeMs"]) if "maxCpuTimeMs" in policy else None
            ),
            max_memory_bytes=(
                int(policy["maxMemoryBytes"]) if "maxMemoryBytes" in policy else None
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
