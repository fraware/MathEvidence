"""Published cross-language digest vectors for Wave 2 theorem identity (ME-RV-020).

Serializer: mathevidence-theorem-identity-0.3
"""

from __future__ import annotations

from adapters.common.theorem_identity import (
    THEOREM_IDENTITY_SERIALIZER_VERSION,
    default_rational_environment_lock,
    environment_lock_digest,
    replay_target_digest,
    build_replay_target,
    theorem_type_digest,
)

# Fixed environment lock used by all vectors in this file.
_LOCK = default_rational_environment_lock()
_LOCK_DIGEST = environment_lock_digest(_LOCK)

# Vector A: simple elaborated equality with one binder.
_TYPE_A = {
    "schemaVersion": "0.3.0",
    "serializerVersion": THEOREM_IDENTITY_SERIALIZER_VERSION,
    "elaboratedSerialization": (
        "forall (x : Rat), x + 0 = x"
    ),
    "universeParams": [],
    "binders": [
        {
            "name": "x",
            "kind": "default",
            "typeSerialization": "Rat",
        }
    ],
    "constantNames": ["Rat", "HAdd.hAdd", "OfNat.ofNat", "Eq"],
    "environmentLockDigest": _LOCK_DIGEST,
}
_TYPE_A_DIGEST = theorem_type_digest(_TYPE_A)

_REQUEST_A = (
    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
)
_PROOF_A = (
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
)

_TARGET_A = build_replay_target(
    module_name="MathEvidence.Generated.Replay.VectorA",
    declaration_name="certified_vector_a",
    theorem_type_canonical=_TYPE_A["elaboratedSerialization"],
    theorem_type_digest_value=_TYPE_A_DIGEST,
    source_revision="wave2-vector",
    source_file="MathEvidence/Generated/Replay/VectorA.lean",
    environment_lock_digest_value=_LOCK_DIGEST,
    request_digest=_REQUEST_A,
    candidate_bundle_digest=(
        "sha256:3333333333333333333333333333333333333333333333333333333333333333"
    ),
)

# Vector B: Unicode binder name + two binders (ordering / UTF-16 key stress).
_TYPE_B = {
    "schemaVersion": "0.3.0",
    "serializerVersion": THEOREM_IDENTITY_SERIALIZER_VERSION,
    "elaboratedSerialization": (
        "forall (α : Type) (x : α), x = x"
    ),
    "universeParams": ["u"],
    "binders": [
        {
            "name": "α",
            "kind": "implicit",
            "typeSerialization": "Type u",
        },
        {
            "name": "x",
            "kind": "default",
            "typeSerialization": "α",
        },
    ],
    "constantNames": ["Eq"],
    "environmentLockDigest": _LOCK_DIGEST,
}
_TYPE_B_DIGEST = theorem_type_digest(_TYPE_B)

DIGEST_VECTORS: list[dict] = [
    {
        "id": "env_lock_rational_default",
        "kind": "environment_lock",
        "payload": _LOCK,
        "digest": _LOCK_DIGEST,
    },
    {
        "id": "theorem_type_add0",
        "kind": "theorem_type",
        "payload": _TYPE_A,
        "digest": _TYPE_A_DIGEST,
    },
    {
        "id": "theorem_identity_add0",
        "kind": "theorem_identity",
        "payload": {
            **_TYPE_A,
            "declarationName": "certified_vector_a",
            "theoremTypeDigest": _TYPE_A_DIGEST,
            "proofDeclarationDigest": _PROOF_A,
            "environmentLock": dict(_LOCK),
        },
        "digest": _TYPE_A_DIGEST,
    },
    {
        "id": "replay_target_add0",
        "kind": "replay_target",
        "payload": _TARGET_A,
        "digest": replay_target_digest(_TARGET_A),
    },
    {
        "id": "theorem_type_unicode_binders",
        "kind": "theorem_type",
        "payload": _TYPE_B,
        "digest": _TYPE_B_DIGEST,
    },
]


def published_digests() -> dict[str, str]:
    return {v["id"]: v["digest"] for v in DIGEST_VECTORS}
