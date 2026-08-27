"""Release-provenance regressions for complete evidence binding."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import scripts.generate_release_provenance as release_provenance


def test_release_provenance_binds_complete_evidence_and_benchmark_trees(
    tmp_path: Path, monkeypatch
) -> None:
    """Every committed file in evidence/ and benchmarks/ must be digest-bound."""

    root = tmp_path / "repo"
    evidence = root / "evidence" / "examples" / "example"
    benchmark = root / "benchmarks" / "suite"
    evidence.mkdir(parents=True)
    benchmark.mkdir(parents=True)

    canonical = evidence / "manifest.cjson"
    canonical.write_text('{"bundleVersion":"0.3.0"}\n', encoding="utf-8")
    readme = evidence / "README.md"
    readme.write_text("example\n", encoding="utf-8")
    theorem = evidence / "theorem.lean"
    theorem.write_text("theorem example : True := by trivial\n", encoding="utf-8")
    benchmark_manifest = benchmark / "manifest.json"
    benchmark_manifest.write_text("{}\n", encoding="utf-8")

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

    expected = {
        "evidence/examples/example/manifest.cjson": canonical,
        "evidence/examples/example/README.md": readme,
        "evidence/examples/example/theorem.lean": theorem,
        "benchmarks/suite/manifest.json": benchmark_manifest,
    }
    assert set(rows) == set(expected)
    for relative_path, path in expected.items():
        assert rows[relative_path] == release_provenance._sha256_file(path)
