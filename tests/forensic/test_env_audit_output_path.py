from __future__ import annotations

from pathlib import Path

import scripts.scaffold_env_audits as env_audits


def test_environment_audit_output_can_be_redirected_outside_repo(
    monkeypatch,
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "release-env-audits"
    monkeypatch.setenv("MATHEVIDENCE_ENV_AUDIT_OUT_DIR", str(out_dir))
    assert env_audits._resolve_out_dir() == out_dir
    assert env_audits._display_path(out_dir / "report.json") == str(out_dir / "report.json")


def test_environment_audit_relative_override_is_repo_relative(monkeypatch) -> None:
    monkeypatch.setenv("MATHEVIDENCE_ENV_AUDIT_OUT_DIR", "_tmp_release_env_audits")
    assert env_audits._resolve_out_dir() == env_audits.ROOT / "_tmp_release_env_audits"
