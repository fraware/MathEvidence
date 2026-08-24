"""Theorem identity, environment lock, and replay-target digests (Wave 2 / ME-RV-020).

Current theorem serializer profile: mathevidence-theorem-identity-0.4.

Historical theorem/environment payloads remain recomputable because binding
functions preserve version fields and optional fields already present in each
payload instead of silently rewriting them to current defaults.
"""

from __future__ import annotations

from typing import Any

from adapters.common.canonical import sha256_digest

THEOREM_IDENTITY_SERIALIZER_VERSION = "mathevidence-theorem-identity-0.4"
THEOREM_IDENTITY_SCHEMA_VERSION = "0.4.0"
REPLAY_TARGET_SCHEMA_VERSION = "0.3.0"
# Legacy default used by historical rational-equality vectors. Exact replay
# constructs current 0.4 locks in adapters.common.environment_lock.
ENVIRONMENT_LOCK_SCHEMA_VERSION = "0.3.0"

RATIONAL_EQUALITY_DEFAULT_IMPORTS: tuple[str, ...] = (
    "MathEvidence.Checkers.RationalEquality.Check",
    "MathEvidence.Checkers.RationalEquality.Soundness",
    "MathEvidence.Checkers.RationalEquality.Wire",
)


def environment_lock_binding(lock: dict[str, Any]) -> dict[str, Any]:
    """Canonical binding payload for an environment lock (excludes self-digest).

    v0.4 exact locks additionally bind project revision, trusted Lean source-tree
    content, and the dependency lockfile. v0.3 payloads omit those fields and
    therefore retain their historical digest.
    """
    out: dict[str, Any] = {
        "schemaVersion": lock.get("schemaVersion", ENVIRONMENT_LOCK_SCHEMA_VERSION),
        "leanVersion": lock["leanVersion"],
        "lakeVersion": lock.get("lakeVersion", "lake"),
        "mathlibRevision": lock["mathlibRevision"],
        "imports": list(lock.get("imports") or []),
    }
    for key in (
        "toolchainDigest",
        "projectSourceDigest",
        "dependencyLockDigest",
    ):
        value = lock.get(key)
        if isinstance(value, str):
            out[key] = value
    project_revision = lock.get("projectRevision")
    if isinstance(project_revision, str):
        out["projectRevision"] = project_revision
    return out


def environment_lock_digest(lock: dict[str, Any]) -> str:
    return sha256_digest(environment_lock_binding(lock))


def default_rational_environment_lock() -> dict[str, Any]:
    """Historical v0.3 rational-equality lock retained for archival vectors."""
    return {
        "schemaVersion": "0.3.0",
        "leanVersion": "leanprover/lean4:v4.14.0",
        "lakeVersion": "lake",
        "mathlibRevision": "v4.14.0",
        "imports": list(RATIONAL_EQUALITY_DEFAULT_IMPORTS),
    }


def theorem_type_binding(identity: dict[str, Any]) -> dict[str, Any]:
    """Binding payload for theorem type digest (elaborated + binders + env lock).

    Version fields supplied by an archival payload are preserved exactly. The
    current constants are defaults only for newly constructed identities.
    """
    return {
        "schemaVersion": identity.get("schemaVersion", THEOREM_IDENTITY_SCHEMA_VERSION),
        "serializerVersion": identity.get(
            "serializerVersion", THEOREM_IDENTITY_SERIALIZER_VERSION
        ),
        "elaboratedSerialization": identity["elaboratedSerialization"],
        "universeParams": list(identity.get("universeParams") or []),
        "binders": [
            {
                "name": binder["name"],
                "kind": binder.get("kind", "default"),
                "typeSerialization": binder["typeSerialization"],
            }
            for binder in (identity.get("binders") or [])
        ],
        "constantNames": list(identity.get("constantNames") or []),
        "environmentLockDigest": identity["environmentLockDigest"],
    }


def theorem_type_digest(identity: dict[str, Any]) -> str:
    return sha256_digest(theorem_type_binding(identity))


def theorem_identity_payload(
    *,
    declaration_name: str,
    theorem_type_digest_value: str,
    proof_declaration_digest: str,
    environment_lock_digest_value: str,
    environment_lock: dict[str, Any] | None = None,
    elaborated_serialization: str | None = None,
    universe_params: list[str] | None = None,
    binders: list[dict[str, Any]] | None = None,
    constant_names: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schemaVersion": THEOREM_IDENTITY_SCHEMA_VERSION,
        "serializerVersion": THEOREM_IDENTITY_SERIALIZER_VERSION,
        "declarationName": declaration_name,
        "theoremTypeDigest": theorem_type_digest_value,
        "proofDeclarationDigest": proof_declaration_digest,
        "environmentLockDigest": environment_lock_digest_value,
    }
    if environment_lock is not None:
        out["environmentLock"] = dict(environment_lock)
    if elaborated_serialization is not None:
        out["elaboratedSerialization"] = elaborated_serialization
    if universe_params is not None:
        out["universeParams"] = list(universe_params)
    if binders is not None:
        out["binders"] = list(binders)
    if constant_names is not None:
        out["constantNames"] = list(constant_names)
    return out


def replay_target_binding(target: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schemaVersion": target.get("schemaVersion", REPLAY_TARGET_SCHEMA_VERSION),
        "moduleName": target["moduleName"],
        "declarationName": target["declarationName"],
        "theoremTypeCanonical": target["theoremTypeCanonical"],
        "theoremTypeDigest": target["theoremTypeDigest"],
        "sourceRevision": target["sourceRevision"],
        "sourceFile": target["sourceFile"],
        "sourceSpan": {
            "startLine": int((target.get("sourceSpan") or {}).get("startLine", 0)),
            "startCol": int((target.get("sourceSpan") or {}).get("startCol", 0)),
            "endLine": int((target.get("sourceSpan") or {}).get("endLine", 0)),
            "endCol": int((target.get("sourceSpan") or {}).get("endCol", 0)),
        },
        "environmentLockDigest": target["environmentLockDigest"],
        "capability": {
            "id": target["capability"]["id"],
            "version": target["capability"]["version"],
        },
        "requestDigest": target["requestDigest"],
    }
    candidate = target.get("candidateBundleDigest")
    if isinstance(candidate, str):
        out["candidateBundleDigest"] = candidate
    return out


def replay_target_digest(target: dict[str, Any]) -> str:
    return sha256_digest(replay_target_binding(target))


def build_replay_target(
    *,
    module_name: str,
    declaration_name: str,
    theorem_type_canonical: str,
    theorem_type_digest_value: str,
    source_revision: str,
    source_file: str,
    environment_lock_digest_value: str,
    request_digest: str,
    capability_id: str = "algebra.rational_equality",
    capability_version: str = "0.1.0",
    source_span: dict[str, int] | None = None,
    candidate_bundle_digest: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schemaVersion": REPLAY_TARGET_SCHEMA_VERSION,
        "moduleName": module_name,
        "declarationName": declaration_name,
        "theoremTypeCanonical": theorem_type_canonical,
        "theoremTypeDigest": theorem_type_digest_value,
        "sourceRevision": source_revision,
        "sourceFile": source_file,
        "sourceSpan": source_span
        or {"startLine": 0, "startCol": 0, "endLine": 0, "endCol": 0},
        "environmentLockDigest": environment_lock_digest_value,
        "capability": {"id": capability_id, "version": capability_version},
        "requestDigest": request_digest,
    }
    if candidate_bundle_digest is not None:
        out["candidateBundleDigest"] = candidate_bundle_digest
    return out
