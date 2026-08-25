#!/usr/bin/env python3
"""Emit release provenance binding the exact release tree and trust surface."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _git_output(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _git_rev() -> str:
    return _git_output("rev-parse", "HEAD")


def _git_tree() -> str:
    return _git_output("rev-parse", "HEAD^{tree}")


def _git_clean() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return not bool(result.stdout.strip())


def _lean_toolchain() -> str:
    path = ROOT / "lean-toolchain"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return "unknown"


def _lake_pins() -> dict[str, Any]:
    path = ROOT / "lake-manifest.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    packages = []
    for pkg in data.get("packages") or []:
        packages.append(
            {
                "name": pkg.get("name"),
                "rev": pkg.get("rev"),
                "url": pkg.get("url"),
                "inputRev": pkg.get("inputRev"),
            }
        )
    packages.sort(key=lambda item: str(item.get("name") or ""))
    return {"manifestVersion": data.get("version"), "packages": packages}


def _hashed_files(
    root: Path,
    *,
    suffixes: frozenset[str] | None = None,
) -> list[dict[str, str]]:
    if not root.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "digest": _sha256_file(path),
            }
        )
    return rows


def _hashed_paths(paths: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rel in paths:
        path = ROOT / rel
        if path.is_file():
            rows.append({"path": rel, "digest": _sha256_file(path)})
    return rows


def _maturity_binding() -> dict[str, Any]:
    path = ROOT / "registry" / "maturity-inventory.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "digest": _sha256_file(path),
        "schemaVersion": data.get("schemaVersion"),
        "auditedBaselineCommit": data.get("statusAsOfCommit"),
        "program": data.get("program"),
    }


def _workflow_context() -> dict[str, str]:
    names = {
        "repository": "GITHUB_REPOSITORY",
        "runId": "GITHUB_RUN_ID",
        "runAttempt": "GITHUB_RUN_ATTEMPT",
        "workflow": "GITHUB_WORKFLOW",
        "eventName": "GITHUB_EVENT_NAME",
        "ref": "GITHUB_REF",
        "refName": "GITHUB_REF_NAME",
        "refType": "GITHUB_REF_TYPE",
        "sha": "GITHUB_SHA",
        "actor": "GITHUB_ACTOR",
    }
    return {
        key: os.environ[value]
        for key, value in names.items()
        if os.environ.get(value)
    }


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "provenance"
    out_dir.mkdir(parents=True, exist_ok=True)

    commit = _git_rev()
    tree = _git_tree()
    workflow = _workflow_context()
    workflow_sha = workflow.get("sha")
    if workflow_sha and commit != "unknown" and workflow_sha != commit:
        raise SystemExit(
            f"release provenance SHA mismatch: GITHUB_SHA={workflow_sha} HEAD={commit}"
        )

    evidence_files: list[dict[str, str]] = []
    for root_name in ("evidence", "benchmarks"):
        evidence_files.extend(
            _hashed_files(ROOT / root_name, suffixes=frozenset({".json", ".md"}))
        )
    evidence_files.sort(key=lambda item: item["path"])

    lock_files = _hashed_paths(
        [
            "lean-toolchain",
            "lake-manifest.json",
            "uv.lock",
            "pyproject.toml",
            "requirements-freeze.txt",
        ]
    )
    trust_documents = _hashed_paths(
        [
            "README.md",
            "docs/STATUS.md",
            "docs/security/KNOWN_TRUST_GAPS.md",
            "docs/adr/0005-exact-candidate-binding.md",
            "GOVERNANCE.md",
            "SECURITY.md",
        ]
    )
    registry_files = _hashed_files(
        ROOT / "registry",
        suffixes=frozenset({".json"}),
    )
    schema_files = _hashed_files(
        ROOT / "schemas",
        suffixes=frozenset({".json"}),
    )
    workflow_files = _hashed_files(
        ROOT / ".github" / "workflows",
        suffixes=frozenset({".yml", ".yaml"}),
    )

    manifest = {
        "schemaVersion": "0.2.0",
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # Compatibility fields retained for existing release consumers.
        "gitCommit": commit,
        "leanToolchain": _lean_toolchain(),
        "lake": _lake_pins(),
        "evidenceAndBenchmarkFiles": evidence_files,
        # Release-grade bindings.
        "gitTree": tree,
        "gitWorkingTreeCleanAtGeneration": _git_clean(),
        "workflowRun": workflow,
        "maturityInventory": _maturity_binding(),
        "lockFiles": lock_files,
        "registryFiles": registry_files,
        "schemaFiles": schema_files,
        "workflowFiles": workflow_files,
        "trustDocuments": trust_documents,
        "notes": [
            "The release commit/tree bind the complete checked-out source state.",
            "The maturity inventory names an audited baseline commit; its digest is "
            "bound here to the actual release commit/tree.",
            "Lean is pinned by lean-toolchain plus lake-manifest package revisions.",
            "Python dependency state is bound by uv.lock and requirements-freeze.txt.",
            "Evidence and benchmark hashes are release evidence, not a substitute "
            "for capability-specific checker soundness.",
            "Stable promotion and human/external review gates are not implied by "
            "this experimental-release provenance record.",
        ],
    }
    out_path = out_dir / "provenance-manifest.json"
    out_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {out_path} "
        f"(evidence={len(evidence_files)}, registry={len(registry_files)}, "
        f"schemas={len(schema_files)}, workflows={len(workflow_files)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
