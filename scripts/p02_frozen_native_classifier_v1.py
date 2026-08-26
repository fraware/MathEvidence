"""Native Lean differential harness for P02.

This module is intentionally independent of ``p02_kce.stages``. It executes a
pinned Lean project through ``lake env lean``, preserves raw diagnostics, and
classifies only observations supported by the native process. It never treats
constructed fault labels as native gold.

No result produced by this harness is publication-eligible until a full run is
completed under the frozen environment and the resulting bundle is reviewed
and promoted explicitly.
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
from typing import Any, Iterable, Sequence

SCHEMA_VERSION = "p02_native_differential_v1"
CLASSIFIER_VERSION = "p02_native_observation_classifier_v1"
EXPECTED_MATHEVIDENCE_SHA = "946d2f7b14840837a5b641150c9df9008c4be9eb"
EXPECTED_LEAN_TOOLCHAIN = "leanprover/lean4:v4.14.0"
THEOREM_NAME = "p02Native"
TARGET_STATEMENT = "∀ (n : Nat), n = n"

FAULT_MECHANISMS: tuple[str, ...] = (
    "SOURCE_CORRUPTION",
    "UNKNOWN_TYPE",
    "PROHIBITED_PLACEHOLDER",
    "INVALID_PROOF",
    "WRONG_TARGET",
)

NATIVE_CLASSES = frozenset(
    {
        "SOURCE_EMPTY",
        "FRONTEND_REJECT",
        "ENVIRONMENT_OR_ELAB_REJECT",
        "TOOLCHAIN_ACCEPT_POLICY_REJECT",
        "TOOLCHAIN_ACCEPT_TARGET_MISMATCH",
        "TOOLCHAIN_ACCEPT_TARGET_MATCH",
        "UNKNOWN",
    }
)

# Conservative patterns only. Unrecognized failures remain UNKNOWN.
_FRONTEND_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"error:\s*expected token",
        r"error:\s*unexpected token",
        r"unexpected end of input",
        r"parser error",
        r"invalid.*syntax",
    )
)
_ELAB_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"unknown identifier",
        r"unknown constant",
        r"function expected at",
        r"application type mismatch",
        r"type mismatch",
        r"failed to synthesize",
        r"invalid field notation",
        r"declaration has metavariables",
    )
)
_PLACEHOLDER_RE = re.compile(r"\b(sorry|admit)\b")
_AXIOM_RE = re.compile(r"(?m)^\s*axiom\s+[A-Za-z_][A-Za-z0-9_']*")


@dataclass(frozen=True)
class NativeCase:
    case_id: str
    role: str
    mechanisms: tuple[str, ...]
    source: str
    target_statement: str = TARGET_STATEMENT
    theorem_name: str = THEOREM_NAME


@dataclass(frozen=True)
class ProcessObservation:
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool = False
    spawn_error: str | None = None

    @property
    def combined_output(self) -> str:
        return f"{self.stdout}\n{self.stderr}".strip()


@dataclass(frozen=True)
class NativeObservations:
    source_empty: bool
    candidate: ProcessObservation
    declaration_probe: ProcessObservation | None
    target_probe: ProcessObservation | None
    policy_has_placeholder: bool
    policy_has_custom_axiom: bool

    @property
    def policy_admissible(self) -> bool:
        return not self.policy_has_placeholder and not self.policy_has_custom_axiom


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mechanism_subsets() -> Iterable[tuple[str, ...]]:
    for r in range(len(FAULT_MECHANISMS) + 1):
        for combo in itertools.combinations(FAULT_MECHANISMS, r):
            yield combo


def render_case_source(mechanisms: Sequence[str]) -> str:
    """Render one deterministic source from independent fault mechanisms.

    Mechanism definitions are independent of the surrogate diagnoser. The
    five mechanisms touch distinct source aspects so every subset is defined.
    """
    m = frozenset(mechanisms)
    unknown = m.difference(FAULT_MECHANISMS)
    if unknown:
        raise ValueError(f"unknown native fault mechanisms: {sorted(unknown)}")

    type_name = "P02MissingType" if "UNKNOWN_TYPE" in m else "Nat"
    statement = "True" if "WRONG_TARGET" in m else "n = n"
    if "INVALID_PROOF" in m:
        proof = "exact n"
    elif "WRONG_TARGET" in m:
        proof = "exact True.intro"
    else:
        proof = "rfl"

    policy_helper = ""
    if "PROHIBITED_PLACEHOLDER" in m:
        policy_helper = "theorem p02Placeholder : True := by\n  sorry\n\n"

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
    return policy_helper + main


def build_native_corpus() -> tuple[NativeCase, ...]:
    """Build the full 32-subset construction plus two outside-domain controls."""
    cases: list[NativeCase] = []
    for index, mechanisms in enumerate(_mechanism_subsets()):
        if not mechanisms:
            role = "clean_control"
        elif len(mechanisms) == 1:
            role = "single_fault"
        else:
            role = "compound_fault"
        suffix = "CLEAN" if not mechanisms else "+".join(mechanisms)
        cases.append(
            NativeCase(
                case_id=f"ND-{index:02d}-{suffix}",
                role=role,
                mechanisms=tuple(mechanisms),
                source=render_case_source(mechanisms),
            )
        )

    cases.append(
        NativeCase(
            case_id="ND-OUTSIDE-NO-DECLARATION",
            role="outside_domain_control",
            mechanisms=(),
            source="#eval 1\n",
        )
    )
    cases.append(
        NativeCase(
            case_id="ND-OUTSIDE-EMPTY",
            role="outside_domain_control",
            mechanisms=(),
            source="",
        )
    )

    if len(cases) != 34:
        raise AssertionError(f"native corpus cardinality mismatch: {len(cases)}")
    if len({c.case_id for c in cases}) != len(cases):
        raise AssertionError("duplicate native case ids")
    return tuple(cases)


def _run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
) -> ProcessObservation:
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
        return ProcessObservation(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.monotonic() - started,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return ProcessObservation(
            command=tuple(command),
            returncode=None,
            stdout=stdout,
            stderr=stderr,
            elapsed_seconds=time.monotonic() - started,
            timed_out=True,
        )
    except OSError as exc:
        return ProcessObservation(
            command=tuple(command),
            returncode=None,
            stdout="",
            stderr="",
            elapsed_seconds=time.monotonic() - started,
            spawn_error=f"{type(exc).__name__}: {exc}",
        )


def _run_lean_source(
    source: str,
    *,
    lean_project: Path,
    scratch_dir: Path,
    stem: str,
    timeout_seconds: float,
) -> ProcessObservation:
    path = scratch_dir / f"{stem}.lean"
    path.write_text(source, encoding="utf-8")
    return _run_process(
        ("lake", "env", "lean", str(path.resolve())),
        cwd=lean_project,
        timeout_seconds=timeout_seconds,
    )


def collect_native_observations(
    source: str,
    target_statement: str,
    theorem_name: str,
    *,
    lean_project: Path,
    scratch_dir: Path,
    stem: str,
    timeout_seconds: float,
) -> NativeObservations:
    """Execute native candidate/probes without consulting construction labels."""
    candidate = _run_lean_source(
        source,
        lean_project=lean_project,
        scratch_dir=scratch_dir,
        stem=f"{stem}-candidate",
        timeout_seconds=timeout_seconds,
    )
    policy_has_placeholder = bool(_PLACEHOLDER_RE.search(source))
    policy_has_custom_axiom = bool(_AXIOM_RE.search(source))

    declaration_probe: ProcessObservation | None = None
    target_probe: ProcessObservation | None = None
    if candidate.returncode == 0 and not candidate.timed_out and candidate.spawn_error is None:
        declaration_probe = _run_lean_source(
            source + f"\n#check {theorem_name}\n",
            lean_project=lean_project,
            scratch_dir=scratch_dir,
            stem=f"{stem}-decl-probe",
            timeout_seconds=timeout_seconds,
        )
        if declaration_probe.returncode == 0:
            target_probe = _run_lean_source(
                source + f"\nexample : {target_statement} := {theorem_name}\n",
                lean_project=lean_project,
                scratch_dir=scratch_dir,
                stem=f"{stem}-target-probe",
                timeout_seconds=timeout_seconds,
            )

    return NativeObservations(
        source_empty=not source.strip(),
        candidate=candidate,
        declaration_probe=declaration_probe,
        target_probe=target_probe,
        policy_has_placeholder=policy_has_placeholder,
        policy_has_custom_axiom=policy_has_custom_axiom,
    )


def _matches_any(patterns: Sequence[re.Pattern[str]], text: str) -> bool:
    return any(p.search(text) is not None for p in patterns)


def derive_native_class(observations: NativeObservations) -> str:
    """Derive a conservative native class from raw observations only.

    This function intentionally accepts no case id, mechanism set, planted
    stage, or surrogate output. Ambiguous or unrecognized diagnostics map to
    ``UNKNOWN`` rather than being forced into a convenient class.
    """
    if observations.source_empty:
        return "SOURCE_EMPTY"

    candidate = observations.candidate
    if candidate.timed_out or candidate.spawn_error is not None or candidate.returncode is None:
        return "UNKNOWN"

    if candidate.returncode != 0:
        text = candidate.combined_output
        if _matches_any(_FRONTEND_PATTERNS, text):
            return "FRONTEND_REJECT"
        if _matches_any(_ELAB_PATTERNS, text):
            return "ENVIRONMENT_OR_ELAB_REJECT"
        return "UNKNOWN"

    decl = observations.declaration_probe
    if decl is None or decl.returncode is None or decl.timed_out or decl.spawn_error is not None:
        return "UNKNOWN"
    if decl.returncode != 0:
        return "UNKNOWN"

    if not observations.policy_admissible:
        return "TOOLCHAIN_ACCEPT_POLICY_REJECT"

    target = observations.target_probe
    if target is None or target.returncode is None or target.timed_out or target.spawn_error is not None:
        return "UNKNOWN"
    if target.returncode == 0:
        return "TOOLCHAIN_ACCEPT_TARGET_MATCH"
    return "TOOLCHAIN_ACCEPT_TARGET_MISMATCH"


def _observation_to_json(obs: ProcessObservation | None) -> dict[str, Any] | None:
    return None if obs is None else asdict(obs)


def _environment_snapshot(lean_project: Path, timeout_seconds: float) -> dict[str, Any]:
    toolchain_file = lean_project / "lean-toolchain"
    toolchain_text = toolchain_file.read_text(encoding="utf-8").strip() if toolchain_file.is_file() else None
    commands = {
        "git_head": ("git", "rev-parse", "HEAD"),
        "git_status": ("git", "status", "--porcelain"),
        "lean_version": ("lake", "env", "lean", "--version"),
        "lake_version": ("lake", "--version"),
    }
    observed = {
        name: _observation_to_json(
            _run_process(command, cwd=lean_project, timeout_seconds=timeout_seconds)
        )
        for name, command in commands.items()
    }
    return {
        "lean_project": str(lean_project.resolve()),
        "lean_toolchain_file": toolchain_text,
        "commands": observed,
    }


def _stdout_str(snapshot: dict[str, Any], name: str) -> str | None:
    row = snapshot.get("commands", {}).get(name)
    if not isinstance(row, dict) or row.get("returncode") != 0:
        return None
    return (row.get("stdout") or "").strip()


def validate_environment(
    snapshot: dict[str, Any],
    *,
    expected_project_sha: str,
    expected_toolchain: str,
) -> list[str]:
    errors: list[str] = []
    if snapshot.get("lean_toolchain_file") != expected_toolchain:
        errors.append(
            "lean-toolchain mismatch: "
            f"observed={snapshot.get('lean_toolchain_file')!r} expected={expected_toolchain!r}"
        )
    head = _stdout_str(snapshot, "git_head")
    if head != expected_project_sha:
        errors.append(
            f"project SHA mismatch: observed={head!r} expected={expected_project_sha!r}"
        )
    status = _stdout_str(snapshot, "git_status")
    if status is None:
        errors.append("unable to read git status")
    elif status:
        errors.append("Lean project checkout is dirty; scientific run requires a clean pin")
    if _stdout_str(snapshot, "lean_version") is None:
        errors.append("unable to execute `lake env lean --version`")
    if _stdout_str(snapshot, "lake_version") is None:
        errors.append("unable to execute `lake --version`")
    return errors


def run_case(
    case: NativeCase,
    *,
    lean_project: Path,
    scratch_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    observations = collect_native_observations(
        case.source,
        case.target_statement,
        case.theorem_name,
        lean_project=lean_project,
        scratch_dir=scratch_dir,
        stem=case.case_id.replace("+", "_").replace("/", "_"),
        timeout_seconds=timeout_seconds,
    )
    derived = derive_native_class(observations)
    if derived not in NATIVE_CLASSES:
        raise AssertionError(f"unexpected derived native class: {derived}")
    return {
        "case_id": case.case_id,
        "role": case.role,
        "construction_mechanisms": list(case.mechanisms),
        "source_sha256": _sha256_bytes(case.source.encode("utf-8")),
        "target_sha256": _sha256_bytes(case.target_statement.encode("utf-8")),
        "theorem_name": case.theorem_name,
        "derived_native_class": derived,
        "classifier_version": CLASSIFIER_VERSION,
        "policy_admissible": observations.policy_admissible,
        "policy_has_placeholder": observations.policy_has_placeholder,
        "policy_has_custom_axiom": observations.policy_has_custom_axiom,
        "candidate": _observation_to_json(observations.candidate),
        "declaration_probe": _observation_to_json(observations.declaration_probe),
        "target_probe": _observation_to_json(observations.target_probe),
    }


def _write_case_material(case_dir: Path, case: NativeCase, result: dict[str, Any]) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "candidate.lean").write_text(case.source, encoding="utf-8")
    (case_dir / "target.txt").write_text(case.target_statement + "\n", encoding="utf-8")
    _json_dump(case_dir / "result.json", result)
    for key in ("candidate", "declaration_probe", "target_probe"):
        obs = result.get(key)
        if not isinstance(obs, dict):
            continue
        (case_dir / f"{key}.stdout.txt").write_text(obs.get("stdout") or "", encoding="utf-8")
        (case_dir / f"{key}.stderr.txt").write_text(obs.get("stderr") or "", encoding="utf-8")


def run_native_differential(
    *,
    lean_project: Path,
    output_dir: Path,
    timeout_seconds: float = 30.0,
    expected_project_sha: str = EXPECTED_MATHEVIDENCE_SHA,
    expected_toolchain: str = EXPECTED_LEAN_TOOLCHAIN,
    case_ids: frozenset[str] | None = None,
) -> dict[str, Any]:
    lean_project = lean_project.resolve()
    output_dir = output_dir.resolve()
    if not lean_project.is_dir():
        raise FileNotFoundError(f"Lean project does not exist: {lean_project}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"output directory must be empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    environment = _environment_snapshot(lean_project, timeout_seconds)
    environment_errors = validate_environment(
        environment,
        expected_project_sha=expected_project_sha,
        expected_toolchain=expected_toolchain,
    )
    _json_dump(output_dir / "environment.json", environment)
    if environment_errors:
        _json_dump(
            output_dir / "STATUS.json",
            {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCKED_ENVIRONMENT_MISMATCH",
                "publication_claim_eligible": False,
                "errors": environment_errors,
            },
        )
        raise RuntimeError("environment validation failed: " + "; ".join(environment_errors))

    corpus = build_native_corpus()
    selected = tuple(c for c in corpus if case_ids is None or c.case_id in case_ids)
    if case_ids is not None:
        missing = case_ids.difference(c.case_id for c in selected)
        if missing:
            raise ValueError(f"unknown case ids: {sorted(missing)}")
    run_scope = "full" if len(selected) == len(corpus) else "smoke_subset"

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="p02-native-differential-") as tmp:
        scratch_dir = Path(tmp)
        for case in selected:
            result = run_case(
                case,
                lean_project=lean_project,
                scratch_dir=scratch_dir,
                timeout_seconds=timeout_seconds,
            )
            results.append(result)
            _write_case_material(output_dir / "cases" / case.case_id, case, result)

    counts: dict[str, int] = {name: 0 for name in sorted(NATIVE_CLASSES)}
    for row in results:
        counts[row["derived_native_class"]] += 1

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "classifier_version": CLASSIFIER_VERSION,
        "status": "EXECUTED_NOT_PROMOTED",
        "run_scope": run_scope,
        "publication_claim_eligible": False,
        "expected_project_sha": expected_project_sha,
        "expected_toolchain": expected_toolchain,
        "n_cases": len(results),
        "n_full_corpus": len(corpus),
        "derived_class_counts": counts,
        "case_ids": [row["case_id"] for row in results],
        "environment_path": "environment.json",
        "non_claims": [
            "Native classes are derived from preserved tool observations, not planted surrogate labels.",
            "UNKNOWN is retained and never folded into success or failure classes.",
            "This run is not publication-eligible without review, freeze, and explicit promotion.",
            "Toolchain acceptance, policy admissibility, target correspondence, and semantic fidelity are distinct.",
        ],
    }
    _json_dump(output_dir / "RUN_MANIFEST.json", manifest)
    return {"manifest": manifest, "results": results}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--expected-project-sha", default=EXPECTED_MATHEVIDENCE_SHA)
    parser.add_argument("--expected-toolchain", default=EXPECTED_LEAN_TOOLCHAIN)
    parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        help="Run only named case(s); any subset is marked smoke_subset.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = run_native_differential(
            lean_project=args.lean_project,
            output_dir=args.out,
            timeout_seconds=args.timeout_seconds,
            expected_project_sha=args.expected_project_sha,
            expected_toolchain=args.expected_toolchain,
            case_ids=frozenset(args.case_id) if args.case_id else None,
        )
    except Exception as exc:
        print(f"P02 native differential failed closed: {type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(result["manifest"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
