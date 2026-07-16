"""Foundry pipeline tests — acceptanceInfluence must stay false."""

from __future__ import annotations

from pathlib import Path

from foundry.pipelines.build_corpus import build_corpus
from foundry.pipelines.ingest_evidence import ingest_all_evidence_examples
from foundry.pipelines.negatives import synthetic_negatives
from foundry.pipelines.validate import validate_corpus_episode


def test_evidence_ingest_never_accepts(tmp_path: Path) -> None:
    episodes = ingest_all_evidence_examples()
    assert episodes, "expected evidence/examples bundles"
    for ep in episodes:
        assert ep["acceptanceInfluence"] is False
        validate_corpus_episode(ep)


def test_synthetic_negatives_labeled() -> None:
    negs = synthetic_negatives()
    assert len(negs) >= 3
    for ep in negs:
        assert ep["kind"] == "synthetic_negative"
        assert ep["outcome"]["negative"] is True
        assert ep["acceptanceInfluence"] is False
        validate_corpus_episode(ep)


def test_build_corpus_roundtrip(tmp_path: Path) -> None:
    out = tmp_path / "corpus"
    result = build_corpus(
        out_dir=out,
        include_captures=False,
        include_synthetic_negatives=True,
    )
    assert result["acceptanceInfluence"] is False
    assert result["episodeCount"] >= 3
    manifest = out / "manifest.json"
    assert manifest.is_file()
    splits = out / "splits.json"
    assert splits.is_file()
    assert (out / "contamination.json").is_file()
