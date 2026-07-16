"""Shared JSON-RPC framing, schema validation, digests, and resource limits.

Implements ADR 0003 methods:
initialize, listCapabilities, checkSupport, compute, cancel, shutdown.
"""

from adapters.common.canonical import (
    canonical_dumps,
    reject_duplicate_keys,
    sha256_digest,
    sha256_hex,
)
from adapters.common.errors import AdapterError, ErrorCategory, stable_error
from adapters.common.limits import ResourceLimits, ResourceTracker
from adapters.common.protocol import AdapterServer, CapabilityDescriptor, HandlerResult
from adapters.common.schema_validate import SchemaStore, load_default_schema_store

__all__ = [
    "AdapterError",
    "AdapterServer",
    "CapabilityDescriptor",
    "ErrorCategory",
    "HandlerResult",
    "ResourceLimits",
    "ResourceTracker",
    "SchemaStore",
    "canonical_dumps",
    "load_default_schema_store",
    "reject_duplicate_keys",
    "sha256_digest",
    "sha256_hex",
    "stable_error",
]
