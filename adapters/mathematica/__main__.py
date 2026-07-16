"""Mathematica JSON-RPC adapter entrypoint."""

from __future__ import annotations

from adapters.common.limits import ResourceLimits
from adapters.common.protocol import AdapterServer
from adapters.mathematica.adapter import (
    ADAPTER_VERSION,
    MATHEMATICA_CAPABILITIES,
    RATIONAL_EQUALITY_CAPABILITY,
    check_support,
    compute_handler,
    discover_runtime,
)


def build_server() -> AdapterServer:
    rt = discover_runtime()
    return AdapterServer(
        backend_id="mathematica",
        backend_version="0.1.0",
        adapter_version=ADAPTER_VERSION,
        capabilities=list(MATHEMATICA_CAPABILITIES),
        compute=compute_handler,
        check_support=check_support,
        limits=ResourceLimits(),
        extra_initialize={
            "runtime": {
                "mode": rt.mode,
                "available": rt.available,
                "executable": rt.executable,
                "leanLink": rt.leanlink_path,
                "detail": rt.detail,
            }
        },
    )


def main() -> int:
    return build_server().serve()


if __name__ == "__main__":
    raise SystemExit(main())
