#!/usr/bin/env python3
"""Classify the sealed P02 v2 raw observation bundle with frozen v1 rules.

This script does not read construction.json and does not use mechanism labels.
It implements the pre-run classifier decision rules frozen in LabTrust blob
681309212d1b045558277b167a99dc28c45bef71 (classifier version
p02_native_observation_classifier_v1), verifies the raw bundle integrity first,
and writes derived classes to a separate directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

CLASSIFICATION_SCHEMA = "p02_native_classification_v2_from_frozen_v1"
CLASSIFIER_VERSION = "p02_native_observation_classifier_v1"
FROZEN_CLASSIFIER_BLOB_SHA = "681309212d1b045558277b167a99dc28c45bef71"
EXPECTED_RAW_BUNDLE_DIGEST = (
    "sha256:482f21fe8bafd4e3784e7c3a7e0a5dc103820c087691fc0e66e5ff3dd61a63ea"
)
EXPECTED_CORPUS_DIGEST = (
    "sha256:fe356ed2f5d4bcf653c5cedaa37922e2248547434fe30b746fbcf10ca73bc199"
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

# Exact regex strings and ordering from frozen classifier blob.
_FRONTEND_PATTERN_STRINGS = (
    r"error:\s*expected token",
    r"error:\s*unexpected token",
    r"unexpected end of input",
    r"parser error",
    r"invalid.*syntax",
)
_ELAB_PATTERN_STRINGS = (
    r"unknown identifier",
    r"unknown constant",
    r"function expected at",
    r"application type mismatch",
    r"type mismatch",
    r"failed to synthesize",
    r"invalid field notation",
    r"declaration has metavariables",
)
_FRONTEND_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in _FRONTEND_PATTERN_STRINGS)
_ELAB_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in _ELAB_PATTERN_STRINGS)
_PLACEHOLDER_RE = re.compile(r"\b(sorry|admit)\b")
_AXIOM_RE = re.compile(r"(?m)^\s*axiom\s+[A-Za-z_][A-Za-z0-9_']*")


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


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_bytes(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    )


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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


def verify_raw_bundle(raw_root: Path) -> dict[str, Any]:
    manifest_path = raw_root / "INTEGRITY_MANIFEST.json"
    if not manifest_path.is_file():
        raise RuntimeError("missing raw INTEGRITY_MANIFEST.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observed_files = inventory(raw_root)
    if manifest.get("files") != observed_files:
        raise RuntimeError("raw bundle file inventory mismatch")
    observed_digest = canonical_digest({"files": observed_files})
    if manifest.get("bundle_digest") != observed_digest:
        raise RuntimeError("raw bundle digest does not reproduce")
    if observed_digest != EXPECTED_RAW_BUNDLE_DIGEST:
        raise RuntimeError(
            f"unexpected raw bundle: observed={observed_digest} expected={EXPECTED_RAW_BUNDLE_DIGEST}"
        )
    corpus = json.loads((raw_root / "CORPUS_MANIFEST.json").read_text(encoding="utf-8"))
    if corpus.get("observed_corpus_digest") != EXPECTED_CORPUS_DIGEST:
        raise RuntimeError("raw corpus digest mismatch")
    run = json.loads((raw_root / "RUN_MANIFEST.json").read_text(encoding="utf-8"))
    if run.get("classification_performed") is not False:
        raise RuntimeError("raw bundle unexpectedly reports prior classification")
    if run.get("n_cases") != 34:
        raise RuntimeError("raw bundle does not contain the declared 34-case run")
    return {
        "raw_bundle_digest": observed_digest,
        "corpus_digest": corpus.get("observed_corpus_digest"),
        "raw_run_status": run.get("status"),
    }


def observation_from_json(value: dict[str, Any] | None) -> ProcessObservation | None:
    if value is None:
        return None
    return ProcessObservation(
        command=tuple(value.get("command") or ()),
        returncode=value.get("returncode"),
        stdout=value.get("stdout") or "",
        stderr=value.get("stderr") or "",
        elapsed_seconds=float(value.get("elapsed_seconds") or 0.0),
        timed_out=bool(value.get("timed_out", False)),
        spawn_error=value.get("spawn_error"),
    )


def matches_any(patterns: Sequence[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) is not None for pattern in patterns)


def derive_native_class(observations: NativeObservations) -> str:
    """Frozen decision order from LabTrust classifier blob 681309... ."""
    if observations.source_empty:
        return "SOURCE_EMPTY"

    candidate = observations.candidate
    if candidate.timed_out or candidate.spawn_error is not None or candidate.returncode is None:
        return "UNKNOWN"

    if candidate.returncode != 0:
        text = candidate.combined_output
        if matches_any(_FRONTEND_PATTERNS, text):
            return "FRONTEND_REJECT"
        if matches_any(_ELAB_PATTERNS, text):
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


def self_test_frozen_rules() -> None:
    def obs(
        rc: int | None = 0,
        text: str = "",
        timed_out: bool = False,
        spawn_error: str | None = None,
    ) -> ProcessObservation:
        return ProcessObservation(
            command=("lake", "env", "lean", "x.lean"),
            returncode=rc,
            stdout="",
            stderr=text,
            elapsed_seconds=0.0,
            timed_out=timed_out,
            spawn_error=spawn_error,
        )

    checks = [
        (NativeObservations(True, obs(), None, None, False, False), "SOURCE_EMPTY"),
        (NativeObservations(False, obs(1, "error: expected token"), None, None, False, False), "FRONTEND_REJECT"),
        (NativeObservations(False, obs(1, "error: unknown identifier X"), None, None, False, False), "ENVIRONMENT_OR_ELAB_REJECT"),
        (NativeObservations(False, obs(1, "mystery failure"), None, None, False, False), "UNKNOWN"),
        (NativeObservations(False, obs(), obs(1, "unknown identifier"), None, False, False), "UNKNOWN"),
        (NativeObservations(False, obs(), obs(), obs(), True, False), "TOOLCHAIN_ACCEPT_POLICY_REJECT"),
        (NativeObservations(False, obs(), obs(), obs(), False, False), "TOOLCHAIN_ACCEPT_TARGET_MATCH"),
        (NativeObservations(False, obs(), obs(), obs(1, "type mismatch"), False, False), "TOOLCHAIN_ACCEPT_TARGET_MISMATCH"),
        (NativeObservations(False, obs(None, timed_out=True), None, None, False, False), "UNKNOWN"),
    ]
    for observations, expected in checks:
        observed = derive_native_class(observations)
        if observed != expected:
            raise AssertionError(f"classifier self-test failed: {observed} != {expected}")


def classify_case(case_dir: Path) -> dict[str, Any]:
    # Deliberately read only artifact source + observation record. Never open construction.json.
    source = (case_dir / "candidate.lean").read_text(encoding="utf-8")
    raw = json.loads((case_dir / "observations.json").read_text(encoding="utf-8"))
    source_empty = not source.strip()
    if bool(raw.get("source_empty")) != source_empty:
        raise RuntimeError(f"source_empty mismatch for {case_dir.name}")
    candidate = observation_from_json(raw.get("candidate"))
    if candidate is None:
        raise RuntimeError(f"missing candidate observation for {case_dir.name}")
    observations = NativeObservations(
        source_empty=source_empty,
        candidate=candidate,
        declaration_probe=observation_from_json(raw.get("declaration_probe")),
        target_probe=observation_from_json(raw.get("target_probe")),
        policy_has_placeholder=bool(_PLACEHOLDER_RE.search(source)),
        policy_has_custom_axiom=bool(_AXIOM_RE.search(source)),
    )
    derived = derive_native_class(observations)
    if derived not in NATIVE_CLASSES:
        raise AssertionError(f"invalid native class {derived}")
    return {
        "case_id": raw.get("case_id") or case_dir.name,
        "derived_native_class": derived,
        "classifier_version": CLASSIFIER_VERSION,
        "frozen_classifier_blob_sha": FROZEN_CLASSIFIER_BLOB_SHA,
        "policy_admissible": observations.policy_admissible,
        "policy_has_placeholder": observations.policy_has_placeholder,
        "policy_has_custom_axiom": observations.policy_has_custom_axiom,
        "source_sha256": sha256_bytes(source.encode("utf-8")),
        "observations_sha256": sha256_bytes((case_dir / "observations.json").read_bytes()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw_root = args.raw.resolve()
    out_root = args.out.resolve()
    if out_root.exists() and any(out_root.iterdir()):
        raise RuntimeError(f"classification output not empty: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    self_test_frozen_rules()
    raw_identity = verify_raw_bundle(raw_root)

    case_dirs = sorted(p for p in (raw_root / "cases").iterdir() if p.is_dir())
    if len(case_dirs) != 34:
        raise RuntimeError(f"expected 34 case directories, found {len(case_dirs)}")

    results = [classify_case(case_dir) for case_dir in case_dirs]
    counts = {name: 0 for name in sorted(NATIVE_CLASSES)}
    for row in results:
        counts[row["derived_native_class"]] += 1
        json_dump(out_root / "cases" / row["case_id"] / "classification.json", row)

    summary = {
        "schema_version": CLASSIFICATION_SCHEMA,
        "status": "CLASSIFIED_NOT_DIFFERENTIAL_ANALYZED",
        "publication_claim_eligible": False,
        "classifier_version": CLASSIFIER_VERSION,
        "frozen_classifier_blob_sha": FROZEN_CLASSIFIER_BLOB_SHA,
        "classifier_rules_modified_after_raw_run": False,
        "construction_metadata_read_during_classification": False,
        "n_cases": len(results),
        "derived_class_counts": counts,
        **raw_identity,
        "non_claims": [
            "This step assigns native classes only; it does not compare them to construction mechanisms.",
            "UNKNOWN remains a first-class outcome and is not reassigned.",
            "No native masking or repair claim is made by this classification step.",
            "Publication eligibility remains false pending differential analysis and review."
        ],
    }
    json_dump(out_root / "CLASSIFICATION_SUMMARY.json", summary)

    files = inventory(out_root)
    integrity = {
        "schema_version": "p02_native_classification_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": canonical_digest({"files": files}),
    }
    json_dump(out_root / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"summary": summary, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
