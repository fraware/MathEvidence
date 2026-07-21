"""Schema and invariant validation for corpus episodes."""

from __future__ import annotations

from typing import Any

from adapters.common.schema_validate import SchemaStore
from foundry.pipelines.common import SCHEMA_DIR
from foundry.pipelines.quality import enforce_tier_claims, refuse_q1_as_verified_positive


def schema_store() -> SchemaStore:
    return SchemaStore(SCHEMA_DIR)


def validate_tier_enforcement(episode: dict[str, Any]) -> dict[str, Any]:
    """Apply Q2/Q3 tier rules; refuse Q1 as a positive verified example.

    Raises ValueError when an episode *claims* Q2 without replayable evidence.
    Unlabeled Q3/Q4 claims are demoted (not hard-failed) via ``enforce_tier_claims``.
    """
    claimed = episode.get("qualityTier") or "Q0_raw"
    outcome = episode.get("outcome") or {}

    if claimed == "Q2_formally_verified":
        if outcome.get("negative"):
            raise ValueError(
                f"{episode.get('episodeId', '<missing>')}: Q2_formally_verified refused for negatives"
            )
        if not outcome.get("replayable"):
            raise ValueError(
                f"{episode.get('episodeId', '<missing>')}: Q2_formally_verified requires replayable=true"
            )

    ep = enforce_tier_claims(episode)
    refuse_q1_as_verified_positive(ep)

    tier = ep.get("qualityTier") or "Q0_raw"
    out = ep.get("outcome") or {}

    if tier == "Q2_formally_verified":
        if out.get("negative") or not out.get("replayable"):
            raise ValueError(
                f"{ep.get('episodeId', '<missing>')}: Q2_formally_verified requires replayable=true"
            )

    return ep


def validate_corpus_episode(episode: dict[str, Any], store: SchemaStore | None = None) -> None:
    s = store or schema_store()
    if episode.get("acceptanceInfluence") is not False:
        raise ValueError("acceptanceInfluence must be false")
    validate_tier_enforcement(episode)
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
