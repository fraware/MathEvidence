"""Newline-delimited JSON-RPC 2.0 framing over stdio."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import BinaryIO, TextIO

from adapters.common.errors import stable_error
from adapters.common.limits import ResourceLimits


def iter_ndjson_messages(
    stream: BinaryIO | TextIO,
    *,
    limits: ResourceLimits,
) -> Iterator[str]:
    """Yield one JSON text message per line from ``stream``."""
    while True:
        if isinstance(stream, TextIO) or hasattr(stream, "encoding"):
            line = stream.readline()  # type: ignore[union-attr]
            if line == "" or line is None:
                break
            if isinstance(line, bytes):
                raw = line
            else:
                raw = line.encode("utf-8")
        else:
            raw = stream.readline()
            if not raw:
                break
        if len(raw) > limits.max_request_bytes:
            raise stable_error(
                "resource_limit_exceeded",
                f"request line exceeds {limits.max_request_bytes} bytes",
                details={"kind": "request_bytes", "bytes": len(raw)},
            )
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        text = text.strip()
        if not text:
            continue
        yield text


def write_ndjson_message(
    message: str,
    *,
    stream: TextIO | None = None,
    limits: ResourceLimits | None = None,
) -> None:
    out = stream or sys.stdout
    data = message if message.endswith("\n") else message + "\n"
    if limits is not None and len(data.encode("utf-8")) > limits.max_output_bytes:
        raise stable_error(
            "resource_limit_exceeded",
            "response exceeds maxOutputBytes",
            details={"kind": "output_bytes"},
        )
    out.write(data)
    out.flush()
