"""SymPy JSON-RPC adapter entrypoint."""

from __future__ import annotations

from adapters.common.limits import ResourceLimits
from adapters.common.protocol import AdapterServer
from adapters.sympy.adapter import (
    ADAPTER_VERSION,
    SYMPY_CAPABILITIES,
    check_support,
    compute_handler,
    propose_conditions_handler,
)


def build_server() -> AdapterServer:
    import sympy

    return AdapterServer(
        backend_id="sympy",
        backend_version=str(sympy.__version__),
        adapter_version=ADAPTER_VERSION,
        capabilities=list(SYMPY_CAPABILITIES),
        compute=compute_handler,
        check_support=check_support,
        propose_conditions=propose_conditions_handler,
        limits=ResourceLimits(),
    )


def main() -> int:
    return build_server().serve()


if __name__ == "__main__":
    raise SystemExit(main())
