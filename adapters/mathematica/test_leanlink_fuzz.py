"""LeanLink fuzz stub tests — native bridge never enables."""

from __future__ import annotations

from pathlib import Path

from adapters.mathematica.leanlink_fuzz import (
    MAX_FUZZ_BYTES,
    classify_fuzz_blob,
    load_config_safely,
    path_is_safe_for_leanlink,
    run_corpus,
)


def test_bridge_always_disabled_when_path_missing() -> None:
    cfg = load_config_safely(None)
    assert cfg.enabled is False


def test_bridge_always_disabled_when_path_exists(tmp_path: Path) -> None:
    root = tmp_path / "leanlink-fake"
    root.mkdir()
    cfg = load_config_safely(str(root))
    assert cfg.enabled is False
    assert "disabled" in cfg.notes.lower() or "pending" in cfg.notes.lower()


def test_path_traversal_rejected() -> None:
    ok, reason = path_is_safe_for_leanlink("../escape")
    assert ok is False
    assert "forbidden" in reason
    cfg = load_config_safely("../escape/leanlink")
    assert cfg.enabled is False


def test_classify_empty_and_oversized() -> None:
    empty = classify_fuzz_blob(b"", name="empty")
    assert empty.accepted_as_bridge_input is False
    big = classify_fuzz_blob(b"\x00" * (MAX_FUZZ_BYTES + 1), name="big")
    assert big.accepted_as_bridge_input is False
    assert "oversized" in big.reason


def test_corpus_never_accepts_bridge_input() -> None:
    results = run_corpus()
    assert len(results) >= 3
    assert all(not r.accepted_as_bridge_input for r in results)
