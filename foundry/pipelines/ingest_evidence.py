"""Ingest committed evidence bundles into corpus episodes (post-acceptance only)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from foundry.pipelines.common import (
    EVIDENCE_EXAMPLES,
    KNOWN_CAPABILITIES,
    content_digest,
    load_json,
)

# Stable namespace so rebuilds are deterministic for the same source path.
_NS = UUID("6f756e64-7279-4d36-8c6f-727075732d76")  # "foundry-M6-corpus-v"


def _episode_id_for(source_path: str) -> str:
    return str(uuid5(_NS, source_path))


def ingest_evidence_bundle(bundle_dir: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    """Convert one evidence example directory into a corpus episode.

    Does not run Lean checkers. Replayability is inferred from presence of a
    complete offline bundle (request + certificate + manifest), not from
    acceptance.
    """
    manifest_path = bundle_dir / "manifest.json"
    request_path = bundle_dir / "request.json"
    if not manifest_path.is_file() or not request_path.is_file():
        raise FileNotFoundError(f"incomplete evidence bundle: {bundle_dir}")

    manifest = load_json(manifest_path)
    request = load_json(request_path)
    rel = str(bundle_dir.as_posix())
    if repo_root is not None:
        try:
            rel = str(bundle_dir.resolve().relative_to(repo_root.resolve()).as_posix())
        except ValueError:
            rel = str(bundle_dir.as_posix())

    capability = (manifest.get("capability") or {}).get("id") or request.get("capability") or ""
    backend = ((manifest.get("provenance") or {}).get("backend") or {})
    result_status = manifest.get("resultStatus") or "unknown"
    claim_class = manifest.get("claimClass") or request.get("requestedClaim")
    request_digest = manifest.get("requestDigest") or request.get("requestDigest")
    has_cert = (bundle_dir / "certificate.json").is_file()
    replayable = has_cert and bool(request_digest)

    # Committed offline examples that replay in CI are Q2; others stay Q1.
    quality = "Q2_formally_verified" if replayable else "Q1_schema_valid"

    core = {
        "capability": capability,
        "operation": request.get("operation"),
        "requestDigest": request_digest,
        "resultStatus": result_status,
        "claimClass": claim_class,
        "sourcePath": rel,
        "backendId": backend.get("backendId"),
    }
    digest = content_digest(core)

    negative = result_status in {"rejected", "failed", "unsupported", "error"}
    return {
        "schemaVersion": "0.1.0",
        "episodeId": _episode_id_for(rel),
        "kind": "evidence_bundle",
        "capturedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acceptanceInfluence": False,
        "qualityTier": quality,
        "provenance": {
            "sourceKind": "committed_evidence",
            "sourcePath": rel,
            "sourceDate": (backend.get("generatedAt") or "")[:64] or None,
            "license": "Apache-2.0",
            "publicationAllowed": True,
            "userConsent": "not_applicable",
            "backendId": backend.get("backendId"),
            "backendVersion": backend.get("backendVersion"),
            "adapterVersion": backend.get("adapterVersion"),
            "checkerPackage": ((manifest.get("capability") or {}).get("id")),
            "notes": "Ingested from committed evidence; never consulted by Lean acceptance.",
        },
        "contamination": {
            "inPublicLibrary": False,
            "publicLibraryRefs": [],
            "trainEvalSeparation": "unassigned",
            "duplicateOf": None,
            "contentDigest": digest,
            "benchmarkExclusion": False,
            "notes": "Split assignment applied by foundry.pipelines.split.",
        },
        "toolUse": {
            "capabilityCandidates": list(KNOWN_CAPABILITIES),
            "selectedCapability": capability,
            "selectedOperation": request.get("operation"),
            "requestedClaim": request.get("requestedClaim") or claim_class or "candidate",
            "backendId": backend.get("backendId"),
            "selectionRationale": f"Committed example for capability {capability}.",
        },
        "outcome": {
            "resultStatus": result_status,
            "claimClass": claim_class,
            "assuranceMode": manifest.get("assuranceMode"),
            "requestDigest": request_digest,
            "replayable": replayable,
            "negative": negative,
            "negativeKind": "none" if not negative else "rejected_certificate",
            "errorCodes": [],
            "humanReviewLabels": [],
        },
        "artifactRefs": [rel],
        "payload": {
            "manifestKeys": sorted(manifest.keys()) if isinstance(manifest, dict) else [],
            "hasCertificate": has_cert,
            "hasCandidate": (bundle_dir / "candidate.json").is_file(),
        },
        "notes": "Corpus episode built from evidence; acceptanceInfluence=false.",
    }


def _strip_optional_nones(obj: dict[str, Any]) -> dict[str, Any]:
    """Drop optional None leaves without removing required nullables (e.g. duplicateOf)."""
    keep_null = {"duplicateOf"}
    out: dict[str, Any] = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out[k] = _strip_optional_nones(v)
        elif v is None and k not in keep_null:
            continue
        else:
            out[k] = v
    return out


def ingest_all_evidence_examples(
    examples_dir: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    root = examples_dir or EVIDENCE_EXAMPLES
    episodes: list[dict[str, Any]] = []
    if not root.is_dir():
        return episodes
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "manifest.json").is_file():
            continue
        ep = ingest_evidence_bundle(child, repo_root=repo_root)
        episodes.append(_strip_optional_nones(ep))
    return episodes
