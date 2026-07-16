"""Foundry training-episode capture hooks.

HARD INVARIANT: capture never influences theorem acceptance, checker results,
or ResultStatus. Callers must not feed episodes into acceptance paths.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from adapters.common.schema_validate import SchemaStore

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EPISODE_DIR = REPO_ROOT / "foundry" / "episodes"


def capture_episode(
    *,
    kind: str,
    payload: dict[str, Any],
    capability: str | None = None,
    artifact_refs: list[str] | None = None,
    notes: str = "",
    episode_dir: Path | None = None,
) -> dict[str, Any]:
    """Write a training episode. `acceptanceInfluence` is always false."""
    episode = {
        "schemaVersion": "0.1.0",
        "episodeId": str(uuid4()),
        "kind": kind,
        "capturedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acceptanceInfluence": False,
        "payload": payload,
        "notes": notes
        or "Capture-only Foundry episode; never consulted by Lean checkers.",
    }
    if capability:
        episode["capability"] = capability
    if artifact_refs:
        episode["artifactRefs"] = artifact_refs

    store = SchemaStore(REPO_ROOT / "foundry" / "schema")
    # Also allow loading from filename when SchemaStore points at foundry/schema.
    try:
        store.validate("training-episode.schema.json", episode)
    except Exception:
        # Fallback: validate via schemas path alias if store only has foundry dir.
        root_store = SchemaStore(REPO_ROOT / "foundry" / "schema")
        root_store.validate("training-episode.schema.json", episode)

    out_dir = episode_dir or DEFAULT_EPISODE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{episode['episodeId']}.json"
    path.write_text(json.dumps(episode, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    episode["_path"] = str(path)
    return episode
