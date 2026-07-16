"""Schema and invariant validation for corpus episodes."""

from __future__ import annotations

from typing import Any

from adapters.common.schema_validate import SchemaStore
from foundry.pipelines.common import SCHEMA_DIR


def schema_store() -> SchemaStore:
    return SchemaStore(SCHEMA_DIR)


def validate_corpus_episode(episode: dict[str, Any], store: SchemaStore | None = None) -> None:
    s = store or schema_store()
    if episode.get("acceptanceInfluence") is not False:
        raise ValueError("acceptanceInfluence must be false")
    s.validate("corpus-episode.schema.json", episode)


def validate_corpus_release(release: dict[str, Any], store: SchemaStore | None = None) -> None:
    s = store or schema_store()
    if release.get("acceptanceInfluence") is not False:
        raise ValueError("acceptanceInfluence must be false")
    if release.get("splits", {}).get("immutable") is not True:
        raise ValueError("corpus release splits must be immutable")
    s.validate("corpus-release.schema.json", release)


def validate_all_episodes(
    episodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    store = schema_store()
    ok: list[dict[str, Any]] = []
    errors: list[str] = []
    for ep in episodes:
        eid = ep.get("episodeId", "<missing>")
        try:
            validate_corpus_episode(ep, store)
            ok.append(ep)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{eid}: {exc}")
    return ok, errors
