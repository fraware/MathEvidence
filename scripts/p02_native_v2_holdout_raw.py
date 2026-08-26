#!/usr/bin/env python3
"""Collect raw native observations for the frozen P02 classifier-v2 holdout.

This holdout was defined after classifier v2 was frozen and before execution.
The collector performs no classification. Expected classes live only in the
sealed holdout specification for downstream comparison.
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

SCHEMA_VERSION = "p02_native_classifier_v2_holdout_raw_v1"
CLASSIFIER_V2_BLOB_SHA = "75d0599c277806007b1f31db451dbbe1bec3962e"
EXPECTED_HOLDOUT_SPEC_DIGEST = "sha256:a113c101250c346a89fc8c67b4147a1a6baaaf26df3111fbf05ef0be8f8a5416"


@dataclass(frozen=True)
class HoldoutCase:
    case_id: str
    role: str
    source: str
    theorem_name: str
    target: str
    expected_semantic_class: str
    rationale: str

    def as_base(self) -> base.Case:
        return base.Case(
            case_id=self.case_id,
            role=self.role,
            mechanisms=(),
            source=self.source,
            target_statement=self.target,
            theorem_name=self.theorem_name,
        )


def build_cases() -> tuple[HoldoutCase, ...]:
    cases = (
        HoldoutCase("HOLD-00-CLEAN-TRUE", "clean_control", "theorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "clean proposition control"),
        HoldoutCase("HOLD-01-DOC-SORRY", "lexical_comment", "/-- The word sorry is documentation only. -/\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "documentation comment must not create placeholder policy"),
        HoldoutCase("HOLD-02-NESTED-COMMENT-SORRY", "lexical_comment", "/- outer /- sorry -/ still comment -/\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "nested block-comment token must be inert"),
        HoldoutCase("HOLD-03-MULTILINE-COMMENT-AXIOM", "lexical_comment", "/-\naxiom HoldoutGhost : False\n-/\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "multiline commented axiom must be inert"),
        HoldoutCase("HOLD-04-STRING-MIXED-POLICY", "lexical_string", "def holdoutMessage : String := \"admit axiom sorry\"\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "policy words inside an ordinary string must be inert"),
        HoldoutCase("HOLD-05-ESCAPED-STRING-SORRY", "lexical_string", "def holdoutEscaped : String := \"quote: \\\" sorry after quote\"\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "escaped quote must not terminate policy string erasure"),
        HoldoutCase("HOLD-06-QUOTED-IDENT-SORRY", "quoted_identifier", "def «sorry» : Nat := 0\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "escaped identifier text equal to a policy keyword must be inert"),
        HoldoutCase("HOLD-07-LINE-COMMENT-AXIOM", "lexical_comment", "-- axiom HoldoutGhost : False\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "line-commented axiom must be inert"),
        HoldoutCase("HOLD-08-MIXED-NONCODE", "mixed_noncode", "/- admit -/\ndef holdoutS : String := \"sorry\"\n-- axiom HoldoutGhost : False\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "mixed non-code policy tokens must all be inert"),
        HoldoutCase("HOLD-09-ACTUAL-SORRY", "true_policy_violation", "theorem holdoutHelper : True := by\n  sorry\n\ntheorem holdoutProp (p : Prop) (hp : p) : p := by\n  exact hp\n", "holdoutProp", "∀ (p : Prop), p → p", "TOOLCHAIN_ACCEPT_POLICY_REJECT", "actual placeholder anywhere in artifact violates declared file policy"),
        HoldoutCase("HOLD-10-ACTUAL-AXIOM", "true_policy_violation", "axiom HoldoutAxiom : True\n\ntheorem holdoutTwo (a b : Nat) : a = a := by\n  rfl\n", "holdoutTwo", "∀ (a b : Nat), a = a", "TOOLCHAIN_ACCEPT_POLICY_REJECT", "actual custom axiom anywhere in artifact violates declared file policy"),
        HoldoutCase("HOLD-11-FRONTEND", "native_reject", "theorem holdoutSyntax (n : Nat : n = n := by\n  rfl\n", "holdoutSyntax", "∀ (n : Nat), n = n", "FRONTEND_REJECT", "malformed binder should be rejected in frontend"),
        HoldoutCase("HOLD-12-INVALID-PROOF", "native_reject", "theorem holdoutInvalid : True := by\n  exact 0\n", "holdoutInvalid", "True", "ENVIRONMENT_OR_ELAB_REJECT", "well-formed source with type-invalid proof should reject during elaboration"),
        HoldoutCase("HOLD-13-WRONG-TARGET", "target_mismatch", "theorem holdoutWrong : True := by\n  trivial\n", "holdoutWrong", "False", "TOOLCHAIN_ACCEPT_TARGET_MISMATCH", "accepted declaration proves a different target"),
        HoldoutCase("HOLD-14-AUTOIMPLICIT-OFF-UNKNOWN", "environment_sensitivity", "set_option autoImplicit false\ntheorem holdoutUnknownOff (x : HoldoutUnknownType) : x = x := by\n  rfl\n", "holdoutUnknownOff", "∀ (x : Nat), x = x", "ENVIRONMENT_OR_ELAB_REJECT", "explicitly disabling autoImplicit makes unknown type reject"),
        HoldoutCase("HOLD-15-UNKNOWN-DEFAULT", "environment_sensitivity", "theorem holdoutUnknownDefault (x : HoldoutUnknownType) : x = x := by\n  rfl\n", "holdoutUnknownDefault", "∀ (x : Nat), x = x", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "default autoImplicit can generalize the type parameter and instantiate it at Nat"),
        HoldoutCase("HOLD-16-COMMENT-PLUS-REAL-SORRY", "true_policy_violation", "-- sorry in this comment is inert\ntheorem holdoutRealSorry : True := by\n  sorry\n\ntheorem holdoutMain : True := by\n  trivial\n", "holdoutMain", "True", "TOOLCHAIN_ACCEPT_POLICY_REJECT", "scanner must ignore comment token while retaining the real placeholder"),
        HoldoutCase("HOLD-17-NESTED-MIXED-COMMENT", "lexical_comment", "/- outer\n  /- axiom Nested : False -/\n  \"sorry\"\n-/\ntheorem holdoutTrue : True := by\n  trivial\n", "holdoutTrue", "True", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "nested block comment containing string-like text remains inert"),
        HoldoutCase("HOLD-18-DOC-AXIOM", "lexical_comment", "/--\naxiom DocGhost : True\n-/\ntheorem holdoutProp (p : Prop) (hp : p) : p := by\n  exact hp\n", "holdoutProp", "∀ (p : Prop), p → p", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "documentation block containing axiom syntax must be inert"),
        HoldoutCase("HOLD-19-RENAMED-PAIR", "shape_control", "theorem holdoutPair (a b : Nat) : b = b := by\n  rfl\n", "holdoutPair", "∀ (a b : Nat), b = b", "TOOLCHAIN_ACCEPT_TARGET_MATCH", "different theorem name and two-argument shape should remain target-matching"),
    )
    if len(cases) != 20 or len({c.case_id for c in cases}) != 20:
        raise AssertionError("holdout cardinality/identity failure")
    return cases


def projection(cases: tuple[HoldoutCase, ...]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": c.case_id,
            "role": c.role,
            "source_sha256": base.sha256_bytes(c.source.encode("utf-8")),
            "target_sha256": base.sha256_bytes(c.target.encode("utf-8")),
            "theorem_name": c.theorem_name,
            "expected_semantic_class": c.expected_semantic_class,
            "rationale": c.rationale,
        }
        for c in cases
    ]


def write_case(root: Path, c: HoldoutCase, observations: dict[str, base.Observation | None]) -> None:
    d = root / "cases" / c.case_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "candidate.lean").write_text(c.source, encoding="utf-8")
    (d / "target.txt").write_text(c.target + "\n", encoding="utf-8")
    base.json_dump(d / "expectation.json", {
        "case_id": c.case_id,
        "role": c.role,
        "expected_semantic_class": c.expected_semantic_class,
        "rationale": c.rationale,
        "theorem_name": c.theorem_name,
        "source_sha256": base.sha256_bytes(c.source.encode("utf-8")),
        "target_sha256": base.sha256_bytes(c.target.encode("utf-8")),
    })
    record: dict[str, Any] = {"case_id": c.case_id, "source_empty": not c.source.strip()}
    for key, obs in observations.items():
        record[key] = None if obs is None else asdict(obs)
        if obs is not None:
            (d / f"{key}.stdout.txt").write_text(obs.stdout, encoding="utf-8")
            (d / f"{key}.stderr.txt").write_text(obs.stderr, encoding="utf-8")
    base.json_dump(d / "observations.json", record)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()
    project = args.pinned_project.resolve()
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"holdout output not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    cases = build_cases()
    rows = projection(cases)
    spec_payload = {"classifier_v2_blob_sha": CLASSIFIER_V2_BLOB_SHA, "cases": rows}
    spec_digest = base.canonical_digest(spec_payload)
    if spec_digest != EXPECTED_HOLDOUT_SPEC_DIGEST:
        raise RuntimeError(f"holdout spec digest mismatch: {spec_digest} != {EXPECTED_HOLDOUT_SPEC_DIGEST}")

    environment = base.environment_snapshot(project)
    errors = base.validate_environment(environment)
    base.json_dump(out / "ENVIRONMENT.json", environment)
    if errors:
        raise RuntimeError("holdout environment invalid: " + "; ".join(errors))
    base.json_dump(out / "HOLDOUT_SPEC.json", {
        "schema_version": SCHEMA_VERSION,
        "publication_claim_eligible": False,
        "classifier_v2_blob_sha": CLASSIFIER_V2_BLOB_SHA,
        "spec_digest": spec_digest,
        "n_cases": len(cases),
        "cases": rows,
    })

    with tempfile.TemporaryDirectory(prefix="p02-v2-holdout-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            observations = base.collect_case(
                case.as_base(), project=project, scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            write_case(out, case, observations)

    post = base.git_observation(project, "status", "--porcelain")
    status = base.successful_stdout(post)
    if status is None or status:
        raise RuntimeError(f"pinned project changed during holdout: {status!r}")

    run = {
        "schema_version": SCHEMA_VERSION,
        "status": "RAW_V2_HOLDOUT_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "classifier_v2_blob_sha": CLASSIFIER_V2_BLOB_SHA,
        "n_cases": len(cases),
        "spec_digest": spec_digest,
        "toolchain_transport": os.environ.get("P02_TOOLCHAIN_TRANSPORT"),
        "toolchain_archive_sha256": os.environ.get("P02_TOOLCHAIN_ARCHIVE_SHA256") or None,
        "toolchain_expected_identity": "Lean 4.14.0 commit 410fab728470",
        "non_claims": [
            "This bundle contains raw holdout observations only.",
            "The v2 classifier was frozen before holdout execution.",
            "Expected classes are not classifier outputs and are not consulted during collection."
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run)
    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_native_classifier_v2_holdout_raw_integrity_v1",
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
