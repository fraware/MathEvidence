#!/usr/bin/env python3
"""Collect raw smoke observations for the P02 MATH-AI cross-context extension.

This is a feasibility gate, not the compound replication experiment. It runs
exactly five cases in each of three contexts selected before extension
execution: clean plus one instance of each frozen active perturbation family.
It performs no diagnostic-class assignment and does not alter the transferred
prediction from the original P02 native study.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import p02_native_v2_raw as base

SCHEMA_VERSION = "p02_mathai_cross_context_smoke_raw_v1"
CONTEXT_SET_VERSION = "p02_mathai_cross_context_contexts_v1"
EXPECTED_PROJECT_SHA = base.EXPECTED_PROJECT_SHA
EXPECTED_TOOLCHAIN = base.EXPECTED_TOOLCHAIN
EXPECTED_LEAN_VERSION = base.EXPECTED_LEAN_VERSION

MECHANISMS: tuple[str, ...] = (
    "SOURCE_CORRUPTION",
    "INVALID_PROOF",
    "PROHIBITED_PLACEHOLDER",
    "WRONG_TARGET",
)


@dataclass(frozen=True)
class Context:
    context_id: str
    import_line: str
    namespace: str
    open_lines: tuple[str, ...]
    clean_target_local: str
    wrong_target_local: str
    proof_line: str
    invalid_proof_line: str
    target_statement: str
    theorem_name: str


@dataclass(frozen=True)
class SmokeCase:
    case_id: str
    context_id: str
    role: str
    mechanisms: tuple[str, ...]
    source: str
    target_statement: str
    theorem_name: str


CONTEXTS: tuple[Context, ...] = (
    Context(
        context_id="CX1_RATIONAL_EQUALITY_CONTRACT",
        import_line="import MathEvidence.Assurance.RationalEquality",
        namespace="P02CrossContext.RationalEquality",
        open_lines=("open MathEvidence.Assurance.RationalEquality",),
        clean_target_local="contract.claimsCompleteness = false",
        wrong_target_local="contract.assuranceLevel = .verifiedReferenceAlgorithm",
        proof_line="  native_decide",
        invalid_proof_line="  exact True.intro",
        target_statement=(
            "MathEvidence.Assurance.RationalEquality.contract.claimsCompleteness = false"
        ),
        theorem_name="P02CrossContext.RationalEquality.p02Native",
    ),
    Context(
        context_id="CX2_CALCULUS_REFERENCE_EQUALITY",
        import_line="import MathEvidence.Assurance.Calculus",
        namespace="P02CrossContext.Calculus",
        open_lines=(
            "open MathEvidence.Checkers.Calculus",
            "open MathEvidence.Assurance.Calculus",
        ),
        clean_target_local="referenceCheck req cert = checkBool req cert",
        wrong_target_local="referenceCheck req cert = referenceCheck req cert",
        proof_line="  rfl",
        invalid_proof_line="  exact req",
        target_statement=(
            "∀ (req : MathEvidence.Checkers.Calculus.Request) "
            "(cert : MathEvidence.Checkers.Calculus.Certificate), "
            "MathEvidence.Assurance.Calculus.referenceCheck req cert = "
            "MathEvidence.Checkers.Calculus.checkBool req cert"
        ),
        theorem_name="P02CrossContext.Calculus.p02Native",
    ),
    Context(
        context_id="CX3_LINEAR_ALGEBRA_INVERSE",
        import_line="import MathEvidence.Assurance.LinearAlgebra",
        namespace="P02CrossContext.LinearAlgebra",
        open_lines=(
            "open MathEvidence.Checkers.LinearAlgebra",
            "open MathEvidence.IR.MatrixExpr",
        ),
        clean_target_local=(
            "isInverseWitness A B = (isRightInverse A B && isLeftInverse A B)"
        ),
        wrong_target_local="isInverseWitness A B = isInverseWitness A B",
        proof_line="  rfl",
        invalid_proof_line="  exact A",
        target_statement=(
            "∀ (A B : MathEvidence.IR.MatrixExpr.Matrix), "
            "MathEvidence.Checkers.LinearAlgebra.isInverseWitness A B = "
            "(MathEvidence.Checkers.LinearAlgebra.isRightInverse A B && "
            "MathEvidence.Checkers.LinearAlgebra.isLeftInverse A B)"
        ),
        theorem_name="P02CrossContext.LinearAlgebra.p02Native",
    ),
)


def theorem_binders(context: Context) -> str:
    if context.context_id == "CX1_RATIONAL_EQUALITY_CONTRACT":
        return ""
    if context.context_id == "CX2_CALCULUS_REFERENCE_EQUALITY":
        return " (req : Request) (cert : Certificate)"
    if context.context_id == "CX3_LINEAR_ALGEBRA_INVERSE":
        return " (A B : Matrix)"
    raise AssertionError(context.context_id)


def render_source(context: Context, mechanisms: Sequence[str]) -> str:
    m = frozenset(mechanisms)
    unknown = m.difference(MECHANISMS)
    if unknown:
        raise ValueError(f"unknown mechanisms: {sorted(unknown)}")

    target = (
        context.wrong_target_local
        if "WRONG_TARGET" in m
        else context.clean_target_local
    )
    proof = (
        context.invalid_proof_line
        if "INVALID_PROOF" in m
        else context.proof_line
    )
    helper = (
        "theorem p02Placeholder : True := by\n  sorry\n\n"
        if "PROHIBITED_PLACEHOLDER" in m
        else ""
    )
    declaration_name = "" if "SOURCE_CORRUPTION" in m else " p02Native"
    declaration = (
        f"theorem{declaration_name}{theorem_binders(context)} :\n"
        f"    {target} := by\n"
        f"{proof}\n"
    )

    parts = [context.import_line, "", f"namespace {context.namespace}", ""]
    parts.extend(context.open_lines)
    parts.append("")
    if helper:
        parts.append(helper.rstrip("\n"))
        parts.append("")
    parts.append(declaration.rstrip("\n"))
    parts.extend(("", f"end {context.namespace}", ""))
    return "\n".join(parts)


def build_smoke_cases() -> tuple[SmokeCase, ...]:
    cases: list[SmokeCase] = []
    for context in CONTEXTS:
        specs: list[tuple[str, tuple[str, ...]]] = [("CLEAN", ())]
        specs.extend((mechanism, (mechanism,)) for mechanism in MECHANISMS)
        for suffix, mechanisms in specs:
            cases.append(
                SmokeCase(
                    case_id=f"{context.context_id}__{suffix}",
                    context_id=context.context_id,
                    role="clean_control" if not mechanisms else "single_perturbation_smoke",
                    mechanisms=mechanisms,
                    source=render_source(context, mechanisms),
                    target_statement=context.target_statement,
                    theorem_name=context.theorem_name,
                )
            )
    if len(cases) != 15:
        raise AssertionError(f"smoke cardinality mismatch: {len(cases)}")
    if len({case.case_id for case in cases}) != len(cases):
        raise AssertionError("duplicate smoke case ids")
    if len({case.source for case in cases}) != len(cases):
        raise AssertionError("smoke sources are not unique")
    return tuple(cases)


def smoke_projection(cases: Sequence[SmokeCase]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "context_id": case.context_id,
            "role": case.role,
            "mechanisms": list(case.mechanisms),
            "source_sha256": base.sha256_bytes(case.source.encode("utf-8")),
            "target_sha256": base.sha256_bytes(case.target_statement.encode("utf-8")),
            "theorem_name": case.theorem_name,
        }
        for case in cases
    ]


def collect_case(
    case: SmokeCase,
    *,
    project: Path,
    scratch: Path,
    timeout_seconds: float,
) -> dict[str, base.Observation | None]:
    native_case = base.Case(
        case_id=case.case_id,
        role=case.role,
        mechanisms=case.mechanisms,
        source=case.source,
        target_statement=case.target_statement,
        theorem_name=case.theorem_name,
    )
    return base.collect_case(
        native_case,
        project=project,
        scratch=scratch,
        timeout_seconds=timeout_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    project = args.pinned_project.resolve()
    out = args.out.resolve()
    if not project.is_dir():
        raise FileNotFoundError(project)
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"output must be empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    environment = base.environment_snapshot(project)
    environment_errors = base.validate_environment(environment)
    base.json_dump(out / "environment.json", environment)
    if environment_errors:
        base.json_dump(
            out / "STATUS.json",
            {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCKED_ENVIRONMENT_MISMATCH",
                "publication_claim_eligible": False,
                "errors": environment_errors,
            },
        )
        raise RuntimeError("environment validation failed: " + "; ".join(environment_errors))

    cases = build_smoke_cases()
    projection = smoke_projection(cases)
    context_spec = {
        "schema_version": SCHEMA_VERSION,
        "context_set_version": CONTEXT_SET_VERSION,
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "mechanisms": list(MECHANISMS),
        "contexts": [asdict(context) for context in CONTEXTS],
        "cases": projection,
    }
    context_spec["context_smoke_digest"] = base.canonical_digest(context_spec)
    base.json_dump(out / "SMOKE_SPEC.json", context_spec)

    with tempfile.TemporaryDirectory(prefix="p02-mathai-xcontext-smoke-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            observations = collect_case(
                case,
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            case_dir = out / "cases" / case.case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "candidate.lean").write_text(case.source, encoding="utf-8")
            base.json_dump(
                case_dir / "observations.json",
                {
                    "case_id": case.case_id,
                    "source_empty": not case.source.strip(),
                    "candidate": asdict(observations["candidate"]),
                    "declaration_probe": (
                        asdict(observations["declaration_probe"])
                        if observations["declaration_probe"] is not None
                        else None
                    ),
                    "target_probe": (
                        asdict(observations["target_probe"])
                        if observations["target_probe"] is not None
                        else None
                    ),
                },
            )
            # Construction metadata is physically separate from raw observations.
            base.json_dump(
                case_dir / "construction.json",
                {
                    "case_id": case.case_id,
                    "context_id": case.context_id,
                    "role": case.role,
                    "mechanisms": list(case.mechanisms),
                    "target_statement": case.target_statement,
                    "theorem_name": case.theorem_name,
                },
            )

    run_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "SMOKE_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "compound_states_executed": False,
        "repair_campaign_executed": False,
        "n_cases": len(cases),
        "n_contexts": len(CONTEXTS),
        "context_smoke_digest": context_spec["context_smoke_digest"],
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "non_claims": [
            "Smoke outcomes determine feasibility only; they are not the cross-context compound replication result.",
            "The transferred observation ordering from the original P02 study is not modified by smoke outcomes.",
            "No context may be dropped for an unfavorable single-perturbation signature.",
            "Construction metadata is not a diagnostic oracle and is stored separately from observations.",
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run_manifest)

    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_smoke_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": run_manifest, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
