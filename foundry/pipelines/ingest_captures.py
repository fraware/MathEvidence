"""Promote capture-hook episodes into corpus episodes (post-acceptance only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foundry.pipelines.common import CAPTURE_DIR, KNOWN_CAPABILITIES, content_digest, load_json


def promote_capture(capture: dict[str, Any], *, source_path: str) -> dict[str, Any]:
    if capture.get("acceptanceInfluence") is not False:
        raise ValueError("capture episode must have acceptanceInfluence=false")

    payload = capture.get("payload") if isinstance(capture.get("payload"), dict) else {}
    capability = capture.get("capability") or payload.get("capability") or "unknown"
    digest = content_digest(
        {
            "episodeId": capture.get("episodeId"),
            "kind": capture.get("kind"),
            "capability": capability,
            "payload": payload,
        }
    )
    kind = capture.get("kind") or "negative_failure"
    is_negative = kind in {"negative_failure", "synthetic_negative", "certified_refutation"}

    return {
        "schemaVersion": "0.1.0",
        "episodeId": capture["episodeId"],
        "kind": kind if kind in {
            "hypothesis_lattice",
            "hypothesis_deletion",
            "conjecture_campaign",
            "certified_refutation",
            "bounded_verification",
            "evidence_bundle",
            "tool_selection",
            "negative_failure",
            "synthetic_negative",
        } else "negative_failure",
        "capturedAt": capture.get("capturedAt") or "",
        "acceptanceInfluence": False,
        "qualityTier": "Q1_schema_valid",
        "provenance": {
            "sourceKind": "capture_hook",
            "sourcePath": source_path,
            "license": "Apache-2.0",
            "publicationAllowed": True,
            "userConsent": "not_applicable",
            "notes": "Promoted from Foundry capture hook; never on acceptance path.",
        },
        "contamination": {
            "inPublicLibrary": False,
            "publicLibraryRefs": [],
            "trainEvalSeparation": "unassigned",
            "duplicateOf": None,
            "contentDigest": digest,
            "benchmarkExclusion": False,
        },
        "toolUse": {
            "capabilityCandidates": list(KNOWN_CAPABILITIES),
            "selectedCapability": capability,
            "selectedOperation": payload.get("operation"),
            "requestedClaim": payload.get("requestedClaim") or "candidate",
            "selectionRationale": capture.get("notes") or "Capture-hook episode.",
        },
        "outcome": {
            "resultStatus": payload.get("resultStatus") or "recorded",
            "replayable": False,
            "negative": is_negative,
            "negativeKind": "synthetic" if kind == "synthetic_negative" else (
                "none" if not is_negative else "tool_selection_error"
            ),
            "errorCodes": [],
            "humanReviewLabels": [],
        },
        "artifactRefs": list(capture.get("artifactRefs") or []),
        "payload": payload,
        "notes": "Corpus promotion of capture episode; acceptanceInfluence=false.",
    }


def ingest_capture_dir(capture_dir: Path | None = None) -> list[dict[str, Any]]:
    root = capture_dir or CAPTURE_DIR
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        capture = load_json(path)
        if not isinstance(capture, dict):
            continue
        out.append(promote_capture(capture, source_path=str(path.as_posix())))
    return out
