"""Cross-language digest parity: Python canonical == Lean vector digests."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.common.canonical import canonical_dumps, sha256_digest

ROOT = Path(__file__).resolve().parents[2]
VECTORS = ROOT / "evidence" / "conformance" / "vectors" / "canonical_json_vectors.json"


def test_canonical_json_vector_parity() -> None:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert data.get("profile") or data.get("version")
    cases = data["cases"]
    assert len(cases) >= 2
    for case in cases:
        canonical = canonical_dumps(case["input"])
        assert canonical == case["canonical"], case["id"]
        digest = sha256_digest(case["input"])
        assert digest == case["digest"], case["id"]


def test_empty_object_parity() -> None:
    assert canonical_dumps({}) == "{}"
    # Matches Lean JsonCanonicalTests.empty_object_canonical + sha256 of "{}"
    assert sha256_digest({}) == (
        "sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
    )


def test_negative_and_control_chars() -> None:
    payload = {"n": -1, "s": "a\nb\tc"}
    canonical = canonical_dumps(payload)
    assert canonical == '{"n":-1,"s":"a\\nb\\tc"}'
    assert sha256_digest(payload).startswith("sha256:")
