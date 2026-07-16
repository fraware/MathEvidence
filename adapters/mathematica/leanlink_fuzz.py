"""Safe LeanLink fuzz stubs (native bridge never enabled).

These stubs exercise the scaffold surface that *will* front a native LeanLink
bridge later: path hygiene, binary corpus size, and hard disable of
``enabled``. They must not load native libraries or spawn Mathematica.

See ``docs/architecture/leanlink-adapter-review.md`` and
``benchmarks/adversarial/leanlink_fuzz/``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from adapters.mathematica.leanlink import LeanLinkConfig, load_leanlink_config

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "benchmarks" / "adversarial" / "leanlink_fuzz"

# Bound for CI: refuse to treat oversized blobs as bridge inputs.
MAX_FUZZ_BYTES = 64 * 1024

# Patterns that a future WXF/binary decoder must reject without native crash.
FORBIDDEN_PATH_FRAGMENTS = ("..", "\x00", "//", "\\\\")


@dataclass(frozen=True)
class FuzzCaseResult:
    name: str
    size: int
    digest_sha256: str
    accepted_as_bridge_input: bool
    reason: str


def assert_bridge_disabled(cfg: LeanLinkConfig) -> None:
    """Invariant: scaffold never reports an enabled native bridge."""
    if cfg.enabled:
        raise AssertionError(
            "LeanLink native bridge must stay disabled until review + fuzz close"
        )


def classify_fuzz_blob(data: bytes, *, name: str = "blob") -> FuzzCaseResult:
    """Classify a candidate binary without decoding via native LeanLink."""
    digest = hashlib.sha256(data).hexdigest()
    if len(data) > MAX_FUZZ_BYTES:
        return FuzzCaseResult(
            name=name,
            size=len(data),
            digest_sha256=digest,
            accepted_as_bridge_input=False,
            reason=f"oversized ({len(data)} > {MAX_FUZZ_BYTES})",
        )
    # Empty / all-zero / truncated "WXF-like" headers are never bridge inputs
    # while the native path is disabled.
    if not data:
        return FuzzCaseResult(
            name=name,
            size=0,
            digest_sha256=digest,
            accepted_as_bridge_input=False,
            reason="empty blob",
        )
    return FuzzCaseResult(
        name=name,
        size=len(data),
        digest_sha256=digest,
        accepted_as_bridge_input=False,
        reason="native bridge disabled; binary not decoded",
    )


def path_is_safe_for_leanlink(path: str | Path | None) -> tuple[bool, str]:
    """Reject path traversal / NUL before any future native load."""
    if path is None:
        return True, "unset"
    text = str(path)
    for frag in FORBIDDEN_PATH_FRAGMENTS:
        if frag in text:
            return False, f"forbidden fragment {frag!r}"
    return True, "ok"


def load_config_safely(path: str | None) -> LeanLinkConfig:
    """Load config and assert the bridge stays off."""
    safe, reason = path_is_safe_for_leanlink(path)
    if not safe:
        return LeanLinkConfig(
            root=Path(path) if path else None,
            enabled=False,
            notes=f"LeanLink path rejected: {reason}",
        )
    cfg = load_leanlink_config(path)
    assert_bridge_disabled(cfg)
    return cfg


def iter_corpus_files(corpus_dir: Path | None = None) -> Iterable[Path]:
    root = corpus_dir or CORPUS_DIR
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_file() and p.name != "README.md")


def run_corpus(corpus_dir: Path | None = None) -> list[FuzzCaseResult]:
    """Run all committed LeanLink fuzz stubs; none may enable the bridge."""
    results: list[FuzzCaseResult] = []
    # Config path cases (scaffold).
    for path in (None, "", "C:/does/not/exist/leanlink", "../escape/leanlink"):
        cfg = load_config_safely(path if path else None)
        assert_bridge_disabled(cfg)
    for path in iter_corpus_files(corpus_dir):
        data = path.read_bytes()
        case = classify_fuzz_blob(data, name=path.name)
        results.append(case)
        if case.accepted_as_bridge_input:
            raise AssertionError(f"fuzz stub accepted bridge input: {path.name}")
    return results
