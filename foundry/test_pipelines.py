"""Foundry pipeline tests — acceptanceInfluence must stay false."""

from __future__ import annotations

from pathlib import Path

import pytest

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
        # Offline bundles without Certification Record are preview, not Q2.
        assert ep["qualityTier"] in {
            "Q0_raw",
            "Q1_schema_valid",
            "Q1_checker_preview",
        }


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
        include_conformance=False,
        include_finite_graph=False,
        review_queue_target=3,
    )
    assert result["acceptanceInfluence"] is False
    assert result["episodeCount"] >= 3
    manifest = out / "manifest.json"
    assert manifest.is_file()
    splits = out / "splits.json"
    assert splits.is_file()
    assert (out / "contamination.json").is_file()
    assert (out / "review_queue" / "index.json").is_file()
    assert result["reviewQueue"]["q3AssignedInCorpus"] == 0


def test_source_family_splits_not_random() -> None:
    from foundry.pipelines.split import FAMILY_SPLITS, assign_splits, infer_source_family

    assert FAMILY_SPLITS["finite_graph_conjecture"] == "train"
    assert FAMILY_SPLITS["conformance_linear_algebra"] == "eval"
    eps = [
        {
            "episodeId": "a",
            "kind": "evidence_bundle",
            "provenance": {"sourceFamily": "finite_graph_conjecture", "sourcePath": "x"},
            "contamination": {},
        },
        {
            "episodeId": "b",
            "kind": "evidence_bundle",
            "provenance": {"sourceFamily": "conformance_linear_algebra", "sourcePath": "y"},
            "contamination": {},
        },
    ]
    splits = assign_splits(eps)
    assert splits["policy"] == "source_family"
    assert "a" in splits["train"]
    assert "b" in splits["eval"]
    assert infer_source_family(eps[0]) == "finite_graph_conjecture"


def test_quality_q3_requires_human_labels() -> None:
    from foundry.pipelines.quality import enforce_tier_claims, score_episode

    ep = score_episode(
        {
            "qualityTier": "Q3_semantically_reviewed",
            "outcome": {"replayable": True, "humanReviewLabels": []},
        }
    )
    assert ep["qualityTier"] != "Q3_semantically_reviewed"
    stripped = enforce_tier_claims(
        {
            "qualityTier": "Q3_semantically_reviewed",
            "outcome": {"replayable": True, "humanReviewLabels": []},
            "claims": [{"kind": "q3_auto"}],
        }
    )
    assert stripped["qualityTier"] == "Q1_checker_preview"
    assert all(c.get("kind") != "q3_auto" for c in stripped["claims"])


def test_quality_q2_requires_certification_record() -> None:
    from foundry.pipelines.quality import score_episode

    preview = score_episode(
        {
            "outcome": {
                "replayable": True,
                "negative": False,
                "humanReviewLabels": ["formally_verified"],
            }
        }
    )
    assert preview["qualityTier"] == "Q1_checker_preview"

    q2 = score_episode(
        {
            "outcome": {
                "replayable": True,
                "negative": False,
                "certificationRecordId": "sha256:" + "a" * 64,
                "theoremDeclaration": "MathEvidence.Example.thm",
                "environmentLockDigest": "sha256:" + "b" * 64,
                "humanReviewLabels": [],
            }
        }
    )
    assert q2["qualityTier"] == "Q2_formally_verified"


def test_quality_q2_requires_cert_in_validate() -> None:
    from foundry.pipelines.validate import validate_tier_enforcement

    with pytest.raises(ValueError, match="certificationRecordId"):
        validate_tier_enforcement(
            {
                "episodeId": "bad-q2",
                "qualityTier": "Q2_formally_verified",
                "outcome": {"replayable": True, "negative": False, "humanReviewLabels": []},
                "acceptanceInfluence": False,
            }
        )


def test_refuse_q1_as_positive_verified() -> None:
    from foundry.pipelines.quality import refuse_q1_as_verified_positive
    from foundry.pipelines.validate import validate_tier_enforcement

    with pytest.raises(ValueError, match="refuse Q1"):
        refuse_q1_as_verified_positive(
            {
                "episodeId": "q1-claim",
                "qualityTier": "Q1_schema_valid",
                "outcome": {"replayable": False, "negative": False, "resultStatus": "ok"},
                "claims": [{"kind": "verified_positive"}],
            }
        )

    with pytest.raises(ValueError, match="refuse Q1"):
        validate_tier_enforcement(
            {
                "episodeId": "q1-soundness",
                "schemaVersion": "0.1.0",
                "qualityTier": "Q1_schema_valid",
                "outcome": {
                    "replayable": False,
                    "negative": False,
                    "resultStatus": "soundness_verified",
                    "humanReviewLabels": [],
                },
                "acceptanceInfluence": False,
            }
        )


def test_quality_q3_validate_requires_labels() -> None:
    from foundry.pipelines.validate import validate_tier_enforcement

    # enforce_tier_claims demotes unlabeled Q3 → Q1_checker_preview when replayable.
    demoted = validate_tier_enforcement(
        {
            "episodeId": "q3-demote",
            "qualityTier": "Q3_semantically_reviewed",
            "outcome": {"replayable": True, "negative": False, "humanReviewLabels": []},
            "acceptanceInfluence": False,
        }
    )
    assert demoted["qualityTier"] == "Q1_checker_preview"

    ok = validate_tier_enforcement(
        {
            "episodeId": "q3-ok",
            "qualityTier": "Q3_semantically_reviewed",
            "outcome": {
                "replayable": True,
                "negative": False,
                "humanReviewLabels": ["semantically_reviewed"],
            },
            "acceptanceInfluence": False,
        }
    )
    assert ok["qualityTier"] == "Q3_semantically_reviewed"


def test_release_rejects_workspace_source_commit() -> None:
    from foundry.pipelines.validate import validate_corpus_release

    with pytest.raises(ValueError, match="sourceCommit"):
        validate_corpus_release(
            {
                "schemaVersion": "0.1.0",
                "releaseId": "x",
                "version": "0.1.0",
                "license": "Apache-2.0",
                "acceptanceInfluence": False,
                "sourceCommit": "workspace",
                "tierComposition": {
                    "Q0_raw": 0,
                    "Q1_schema_valid": 0,
                    "Q1_checker_preview": 1,
                    "Q2_formally_verified": 0,
                    "Q3_semantically_reviewed": 0,
                    "Q4_library_grade": 0,
                },
                "splits": {
                    "immutable": True,
                    "train": [],
                    "eval": [],
                    "held_out": [],
                },
                "episodes": ["episodes/a.json"],
                "datasheet": "DATASHEET.md",
                "knownBiases": ["bias"],
            }
        )
