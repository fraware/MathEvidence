#!/usr/bin/env python3
"""Collect raw Lean observations for the preregistered P02 v2 adversarial suite.

The suite attacks lexical policy scanning, formatting/name dependence, diagnostic
keyword leakage, and autoImplicit environment sensitivity. This collector makes
no classifier assignments. Expected semantic outcomes are frozen in a separate
specification that downstream classification must not read.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import p02_native_v2_raw as base

SCHEMA_VERSION = "p02_native_adversarial_raw_v2"
EXPECTED_SPEC_DIGEST = "sha256:b3db906353bdb5c53a732c2fd3f924ab445b116f58afbdac104c24d5334465c4"
TARGET = base.TARGET_STATEMENT


@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    role: str
    source: str
    theorem_name: str
    expected_semantic_class: str
    rationale: str

    def as_base_case(self) -> base.Case:
        return base.Case(
            case_id=self.case_id,
            role=self.role,
            mechanisms=(),
            source=self.source,
            target_statement=TARGET,
            theorem_name=self.theorem_name,
        )


def build_cases() -> tuple[AdversarialCase, ...]:
    clean = "theorem p02Native (n : Nat) : n = n := by\n  rfl\n"
    unknown = "theorem p02Native (n : P02MissingType) : n = n := by\n  rfl\n"
    cases = (
        AdversarialCase("ADV-00-CLEAN", "clean_control", clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "policy-admissible clean control"),
        AdversarialCase("ADV-01-LINE-COMMENT-SORRY", "lexical_comment", "-- sorry is inert commentary\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "comment text must not create a proof placeholder"),
        AdversarialCase("ADV-02-BLOCK-COMMENT-AXIOM", "lexical_comment", "/-\naxiom P02CommentGhost : True\n-/\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "commented axiom text must not create an axiom declaration"),
        AdversarialCase("ADV-03-STRING-SORRY", "lexical_string", "def p02Note : String := \"sorry\"\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "string contents must not create a proof placeholder"),
        AdversarialCase("ADV-04-DIAGNOSTIC-WORDS-COMMENT", "diagnostic_comment", "-- error: expected token; unknown identifier; type mismatch\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "source comments must not be mistaken for process diagnostics"),
        AdversarialCase("ADV-05-WHITESPACE", "formatting", "\n\n" + clean.replace(" : n = n", "   : n = n"), "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "irrelevant formatting should preserve native outcome"),
        AdversarialCase("ADV-06-RENAMED-THEOREM", "renaming", clean.replace("p02Native", "p02NativeRenamed"), "p02NativeRenamed", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "identifier renaming with matched probe should preserve outcome"),
        AdversarialCase("ADV-07-ACTUAL-SORRY", "true_policy_violation", "theorem p02ActualPlaceholder : True := by\n  sorry\n\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_POLICY_REJECT", "actual sorry in artifact is a file-level policy violation"),
        AdversarialCase("ADV-08-ACTUAL-AXIOM", "true_policy_violation", "axiom P02ActualAxiom : True\n\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_POLICY_REJECT", "actual axiom in artifact is a file-level policy violation"),
        AdversarialCase("ADV-09-BLOCK-COMMENT-ADMIT", "lexical_comment", "/- admit -/\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "commented admit must not create a proof placeholder"),
        AdversarialCase("ADV-10-AUTOIMPLICIT-OFF-CLEAN", "environment_control", "set_option autoImplicit false\n" + clean, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "autoImplicit=false must leave well-declared control accepted"),
        AdversarialCase("ADV-11-AUTOIMPLICIT-OFF-UNKNOWN", "environment_sensitivity", "set_option autoImplicit false\n" + unknown, "p02Native", "ENVIRONMENT_OR_ELAB_REJECT", "unknown type must reject when autoImplicit is explicitly disabled"),
        AdversarialCase("ADV-12-UNKNOWN-DEFAULT", "environment_sensitivity", unknown, "p02Native", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "default autoImplicit permits this name to be generalized"),
    )
    if len(cases) != 13 or len({c.case_id for c in cases}) != 13:
        raise AssertionError("adversarial suite cardinality/identity failure")
    return cases


def spec_projection(cases: tuple[AdversarialCase, ...]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": c.case_id,
            "role": c.role,
            "source_sha256": base.sha256_bytes(c.source.encode("utf-8")),
            "target_sha256": base.sha256_bytes(TARGET.encode("utf-8")),
            "theorem_name": c.theorem_name,
            "expected_semantic_class": c.expected_semantic_class,
            "rationale": c.rationale,
        }
        for c in cases
    ]


def write_case(root: Path, case: AdversarialCase, observations: dict[str, base.Observation | None]) -> None:
    case_dir = root / "cases" / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "candidate.lean").write_text(case.source, encoding="utf-8")
    (case_dir / "target.txt").write_text(TARGET + "\n", encoding="utf-8")
    base.json_dump(
        case_dir / "expectation.json",
        {
            "case_id": case.case_id,
            "role": case.role,
            "expected_semantic_class": case.expected_semantic_class,
            "rationale": case.rationale,
            "theorem_name": case.theorem_name,
            "source_sha256": base.sha256_bytes(case.source.encode("utf-8")),
        },
    )
    record: dict[str, Any] = {"case_id": case.case_id, "source_empty": not case.source.strip()}
    for key, obs in observations.items():
        record[key] = None if obs is None else asdict(obs)
        if obs is not None:
            (case_dir / f"{key}.stdout.txt").write_text(obs.stdout, encoding="utf-8")
            (case_dir / f"{key}.stderr.txt").write_text(obs.stderr, encoding="utf-8")
    base.json_dump(case_dir / "observations.json", record)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()
    project = args.pinned_project.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"adversarial output is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    cases = build_cases()
    projection = spec_projection(cases)
    spec_digest = base.canonical_digest({"cases": projection})
    if spec_digest != EXPECTED_SPEC_DIGEST:
        raise RuntimeError(f"adversarial spec digest mismatch: {spec_digest} != {EXPECTED_SPEC_DIGEST}")

    environment = base.environment_snapshot(project)
    errors = base.validate_environment(environment)
    base.json_dump(out / "ENVIRONMENT.json", environment)
    if errors:
        raise RuntimeError("adversarial environment invalid: " + "; ".join(errors))
    base.json_dump(
        out / "ADVERSARIAL_SPEC.json",
        {
            "schema_version": SCHEMA_VERSION,
            "publication_claim_eligible": False,
            "spec_digest": spec_digest,
            "n_cases": len(cases),
            "cases": projection,
        },
    )

    with tempfile.TemporaryDirectory(prefix="p02-adversarial-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            observations = base.collect_case(
                case.as_base_case(),
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            write_case(out, case, observations)

    post_status = base.git_observation(project, "status", "--porcelain")
    status_text = base.successful_stdout(post_status)
    if status_text is None or status_text:
        raise RuntimeError(f"pinned project changed during adversarial run: {status_text!r}")

    run = {
        "schema_version": SCHEMA_VERSION,
        "status": "RAW_ADVERSARIAL_OBSERVATIONS_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "n_cases": len(cases),
        "spec_digest": spec_digest,
        "toolchain_transport": os.environ.get("P02_TOOLCHAIN_TRANSPORT"),
        "toolchain_archive_sha256": os.environ.get("P02_TOOLCHAIN_ARCHIVE_SHA256") or None,
        "toolchain_expected_identity": "Lean 4.14.0 commit 410fab728470",
        "non_claims": [
            "This bundle contains raw native observations only.",
            "Expected semantic classes are preregistered separately and are not classifier outputs.",
            "No adversarial pass/fail claim is assigned by this collection step."
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run)
    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_native_adversarial_raw_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
