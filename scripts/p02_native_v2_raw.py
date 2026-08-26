#!/usr/bin/env python3
"""Collect raw Lean observations for the frozen P02 native differential v2.

This script deliberately performs no native-class assignment. It renders the
predeclared 34-case corpus, verifies its frozen digest, executes candidate,
declaration, and target probes under a pinned MathEvidence checkout, and writes
an integrity-sealed raw evidence bundle for later classification by the frozen
P02 classifier.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

SCHEMA_VERSION = "p02_native_raw_observations_v2"
EXPECTED_PROJECT_SHA = "946d2f7b14840837a5b641150c9df9008c4be9eb"
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.14.0"
EXPECTED_LEAN_VERSION = "4.14.0"
EXPECTED_CORPUS_DIGEST = (
    "sha256:fe356ed2f5d4bcf653c5cedaa37922e2248547434fe30b746fbcf10ca73bc199"
)
THEOREM_NAME = "p02Native"
TARGET_STATEMENT = "∀ (n : Nat), n = n"
FAULT_MECHANISMS: tuple[str, ...] = (
    "SOURCE_CORRUPTION",
    "UNKNOWN_TYPE",
    "PROHIBITED_PLACEHOLDER",
    "INVALID_PROOF",
    "WRONG_TARGET",
)
LEAN_VERSION_RE = re.compile(r"\bversion\s+([0-9]+\.[0-9]+\.[0-9]+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Case:
    case_id: str
    role: str
    mechanisms: tuple[str, ...]
    source: str
    target_statement: str = TARGET_STATEMENT
    theorem_name: str = THEOREM_NAME


@dataclass(frozen=True)
class Observation:
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool = False
    spawn_error: str | None = None


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(payload)


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def render_case_source(mechanisms: Sequence[str]) -> str:
    m = frozenset(mechanisms)
    unknown = m.difference(FAULT_MECHANISMS)
    if unknown:
        raise ValueError(f"unknown mechanisms: {sorted(unknown)}")
    type_name = "P02MissingType" if "UNKNOWN_TYPE" in m else "Nat"
    statement = "0 = 0" if "WRONG_TARGET" in m else "n = n"
    proof = "exact n" if "INVALID_PROOF" in m else "rfl"
    helper = (
        "theorem p02Placeholder : True := by\n  sorry\n\n"
        if "PROHIBITED_PLACEHOLDER" in m
        else ""
    )
    if "SOURCE_CORRUPTION" in m:
        main = (
            f"theorem {THEOREM_NAME} (n : {type_name} : {statement} := by\n"
            f"  {proof}\n"
        )
    else:
        main = (
            f"theorem {THEOREM_NAME} (n : {type_name}) : {statement} := by\n"
            f"  {proof}\n"
        )
    return helper + main


def build_corpus() -> tuple[Case, ...]:
    cases: list[Case] = []
    index = 0
    for r in range(len(FAULT_MECHANISMS) + 1):
        for mechanisms in itertools.combinations(FAULT_MECHANISMS, r):
            role = (
                "clean_control"
                if not mechanisms
                else "single_fault"
                if len(mechanisms) == 1
                else "compound_fault"
            )
            suffix = "CLEAN" if not mechanisms else "+".join(mechanisms)
            cases.append(
                Case(
                    case_id=f"ND2-{index:02d}-{suffix}",
                    role=role,
                    mechanisms=tuple(mechanisms),
                    source=render_case_source(mechanisms),
                )
            )
            index += 1
    cases.extend(
        (
            Case(
                case_id="ND2-OUTSIDE-NO-DECLARATION",
                role="outside_domain_control",
                mechanisms=(),
                source="#eval 1\n",
            ),
            Case(
                case_id="ND2-OUTSIDE-EMPTY",
                role="outside_domain_control",
                mechanisms=(),
                source="",
            ),
        )
    )
    if len(cases) != 34:
        raise AssertionError(f"corpus cardinality mismatch: {len(cases)}")
    if len({case.case_id for case in cases}) != 34:
        raise AssertionError("duplicate case ids")
    if len({case.source for case in cases[:32]}) != 32:
        raise AssertionError("lattice sources are not unique")
    return tuple(cases)


def corpus_projection(cases: Sequence[Case]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "role": case.role,
            "mechanisms": list(case.mechanisms),
            "source_sha256": sha256_bytes(case.source.encode("utf-8")),
            "target_sha256": sha256_bytes(case.target_statement.encode("utf-8")),
        }
        for case in cases
    ]


def run_process(
    command: Sequence[str], *, cwd: Path, timeout_seconds: float
) -> Observation:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env=os.environ.copy(),
        )
        return Observation(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.monotonic() - started,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        return Observation(
            command=tuple(command),
            returncode=None,
            stdout=stdout,
            stderr=stderr,
            elapsed_seconds=time.monotonic() - started,
            timed_out=True,
        )
    except OSError as exc:
        return Observation(
            command=tuple(command),
            returncode=None,
            stdout="",
            stderr="",
            elapsed_seconds=time.monotonic() - started,
            spawn_error=f"{type(exc).__name__}: {exc}",
        )


def successful_stdout(obs: Observation) -> str | None:
    if obs.returncode != 0 or obs.spawn_error is not None or obs.timed_out:
        return None
    return obs.stdout.strip()


def git_observation(project: Path, *args: str) -> Observation:
    return run_process(("git", *args), cwd=project, timeout_seconds=30.0)


def environment_snapshot(project: Path) -> dict[str, Any]:
    head = git_observation(project, "rev-parse", "HEAD")
    status = git_observation(project, "status", "--porcelain")
    lean = run_process(
        ("lake", "env", "lean", "--version"), cwd=project, timeout_seconds=60.0
    )
    lake = run_process(("lake", "--version"), cwd=project, timeout_seconds=60.0)
    toolchain_path = project / "lean-toolchain"
    toolchain = (
        toolchain_path.read_text(encoding="utf-8").strip()
        if toolchain_path.is_file()
        else None
    )
    lean_text = successful_stdout(lean) or ""
    match = LEAN_VERSION_RE.search(lean_text)
    observed_lean_version = match.group(1) if match else None
    return {
        "project_path": str(project.resolve()),
        "git_head": asdict(head),
        "git_status": asdict(status),
        "lean_version": asdict(lean),
        "lake_version": asdict(lake),
        "lean_toolchain_file": toolchain,
        "observed_git_head": successful_stdout(head),
        "observed_git_status": successful_stdout(status),
        "observed_lean_version": observed_lean_version,
    }


def validate_environment(snapshot: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if snapshot.get("observed_git_head") != EXPECTED_PROJECT_SHA:
        errors.append(
            f"project SHA mismatch: {snapshot.get('observed_git_head')!r}"
        )
    status = snapshot.get("observed_git_status")
    if status is None:
        errors.append("unable to read git status")
    elif status:
        errors.append(f"pinned worktree is dirty before run: {status!r}")
    if snapshot.get("lean_toolchain_file") != EXPECTED_TOOLCHAIN:
        errors.append(
            f"lean-toolchain mismatch: {snapshot.get('lean_toolchain_file')!r}"
        )
    if snapshot.get("observed_lean_version") != EXPECTED_LEAN_VERSION:
        errors.append(
            f"actual Lean version mismatch: {snapshot.get('observed_lean_version')!r}"
        )
    lake = snapshot.get("lake_version") or {}
    if lake.get("returncode") != 0 or lake.get("spawn_error"):
        errors.append("lake executable unavailable")
    return errors


def run_lean_file(
    source: str,
    *,
    project: Path,
    scratch: Path,
    stem: str,
    timeout_seconds: float,
) -> Observation:
    path = scratch / f"{stem}.lean"
    path.write_text(source, encoding="utf-8")
    return run_process(
        ("lake", "env", "lean", str(path.resolve())),
        cwd=project,
        timeout_seconds=timeout_seconds,
    )


def collect_case(
    case: Case,
    *,
    project: Path,
    scratch: Path,
    timeout_seconds: float,
) -> dict[str, Observation | None]:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", case.case_id)
    candidate = run_lean_file(
        case.source,
        project=project,
        scratch=scratch,
        stem=f"{stem}-candidate",
        timeout_seconds=timeout_seconds,
    )
    declaration: Observation | None = None
    target: Observation | None = None
    if candidate.returncode == 0 and not candidate.timed_out and candidate.spawn_error is None:
        declaration = run_lean_file(
            case.source + f"\n#check {case.theorem_name}\n",
            project=project,
            scratch=scratch,
            stem=f"{stem}-declaration",
            timeout_seconds=timeout_seconds,
        )
        if (
            declaration.returncode == 0
            and not declaration.timed_out
            and declaration.spawn_error is None
        ):
            target = run_lean_file(
                case.source
                + f"\nexample : {case.target_statement} := {case.theorem_name}\n",
                project=project,
                scratch=scratch,
                stem=f"{stem}-target",
                timeout_seconds=timeout_seconds,
            )
    return {"candidate": candidate, "declaration_probe": declaration, "target_probe": target}


def write_case_bundle(
    root: Path,
    case: Case,
    observations: dict[str, Observation | None],
) -> None:
    case_dir = root / "cases" / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "candidate.lean").write_text(case.source, encoding="utf-8")
    (case_dir / "target.txt").write_text(
        case.target_statement + "\n", encoding="utf-8"
    )
    json_dump(
        case_dir / "construction.json",
        {
            "case_id": case.case_id,
            "role": case.role,
            "mechanisms": list(case.mechanisms),
            "source_sha256": sha256_bytes(case.source.encode("utf-8")),
            "target_sha256": sha256_bytes(case.target_statement.encode("utf-8")),
            "theorem_name": case.theorem_name,
        },
    )
    observation_json: dict[str, Any] = {
        "case_id": case.case_id,
        "source_empty": not case.source.strip(),
    }
    for key, obs in observations.items():
        observation_json[key] = None if obs is None else asdict(obs)
        if obs is not None:
            (case_dir / f"{key}.stdout.txt").write_text(
                obs.stdout, encoding="utf-8"
            )
            (case_dir / f"{key}.stderr.txt").write_text(
                obs.stderr, encoding="utf-8"
            )
    json_dump(case_dir / "observations.json", observation_json)


def inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == "INTEGRITY_MANIFEST.json":
            continue
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": len(data),
                "sha256": sha256_bytes(data),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    project = args.pinned_project.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    cases = build_corpus()
    projection = corpus_projection(cases)
    observed_digest = canonical_digest({"cases": projection})
    if observed_digest != EXPECTED_CORPUS_DIGEST:
        raise RuntimeError(
            f"corpus digest mismatch: observed={observed_digest} expected={EXPECTED_CORPUS_DIGEST}"
        )

    environment = environment_snapshot(project)
    json_dump(out / "ENVIRONMENT.json", environment)
    env_errors = validate_environment(environment)
    if env_errors:
        json_dump(
            out / "STATUS.json",
            {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCKED_ENVIRONMENT",
                "publication_claim_eligible": False,
                "errors": env_errors,
            },
        )
        raise RuntimeError("; ".join(env_errors))

    json_dump(
        out / "CORPUS_MANIFEST.json",
        {
            "schema_version": SCHEMA_VERSION,
            "publication_claim_eligible": False,
            "expected_corpus_digest": EXPECTED_CORPUS_DIGEST,
            "observed_corpus_digest": observed_digest,
            "n_cases": len(cases),
            "cases": projection,
        },
    )

    with tempfile.TemporaryDirectory(prefix="p02-native-v2-raw-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            observations = collect_case(
                case,
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            write_case_bundle(out, case, observations)

    post_status = git_observation(project, "status", "--porcelain")
    post_status_text = successful_stdout(post_status)
    if post_status_text is None:
        raise RuntimeError("unable to read pinned worktree status after run")
    if post_status_text:
        raise RuntimeError(
            f"pinned worktree changed during observation collection: {post_status_text!r}"
        )

    runner_path = Path(__file__).resolve()
    run_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "RAW_OBSERVATIONS_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "expected_lean_version": EXPECTED_LEAN_VERSION,
        "corpus_digest": EXPECTED_CORPUS_DIGEST,
        "n_cases": len(cases),
        "timeout_seconds": args.timeout_seconds,
        "harness_branch_sha": os.environ.get("GITHUB_SHA"),
        "runner_sha256": sha256_bytes(runner_path.read_bytes()),
        "classification_performed": False,
        "post_run_git_status": asdict(post_status),
        "non_claims": [
            "This bundle contains raw Lean observations only.",
            "Construction metadata is stored separately from observations.",
            "No native class, agreement rate, masking rate, or repair result is assigned here.",
            "Publication promotion requires classification with the frozen P02 classifier and independent review.",
        ],
    }
    json_dump(out / "RUN_MANIFEST.json", run_manifest)

    files = inventory(out)
    integrity = {
        "schema_version": "p02_native_raw_bundle_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": canonical_digest({"files": files}),
    }
    json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run_manifest, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
