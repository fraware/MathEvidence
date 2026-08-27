"""Release-provenance regressions for canonical evidence binding."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import scripts.generate_release_provenance as release_provenance


def test_release_provenance_binds_canonical_cjson(
    tmp_path: Path, monkeypatch
) -> None:
    """Canonical Candidate Bundle bytes must appear in the provenance manifest."""

    root = tmp_path / "repo"
    evidence = root / "evidence" / "examples" / "example"
    benchmark = root / "benchmarks" / "suite"
    evidence.mkdir(parents=True)
    benchmark.mkdir(parents=True)

    canonical = evidence / "manifest.cjson"
    canonical.write_text('{"bundleVersion":"0.3.0"}\n', encoding="utf-8")
    (evidence / "README.md").write_text("example\n", encoding="utf-8")
    (benchmark / "manifest.json").write_text("{}\n", encoding="utf-8")
    # Unrelated formats must not silently expand the provenance surface.
    (evidence / "scratch.txt").write_text("not release evidence\n", encoding="utf-8")

    monkeypatch.setattr(release_provenance, "ROOT", root)
    monkeypatch.setattr(release_provenance, "_git_rev", lambda: "a" * 40)
    monkeypatch.setattr(release_provenance, "_git_tree", lambda: "b" * 40)
    monkeypatch.setattr(release_provenance, "_git_clean", lambda: True)
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    out_dir = tmp_path / "provenance"
    monkeypatch.setattr(sys, "argv", ["generate_release_provenance.py", str(out_dir)])

    assert release_provenance.main() == 0
    manifest = json.loads(
        (out_dir / "provenance-manifest.json").read_text(encoding="utf-8")
    )
    rows = {
        row["path"]: row["digest"]
        for row in manifest["evidenceAndBenchmarkFiles"]
    }

    canonical_path = "evidence/examples/example/manifest.cjson"
    assert canonical_path in rows
    assert rows[canonical_path] == release_provenance._sha256_file(canonical)
    assert "evidence/examples/example/README.md" in rows
    assert "benchmarks/suite/manifest.json" in rows
    assert "evidence/examples/example/scratch.txt" not in rows
