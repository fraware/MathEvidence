#!/usr/bin/env python3
"""Collect raw feasibility observations for the P02 MATH-AI cross-context extension.

This is a feasibility gate, not the compound replication experiment. It runs
exactly nine cases in each of three contexts selected before extension
execution: clean, one instance of each frozen active perturbation family, and
the exact inverse repair of each single perturbation. Before native execution
it also checks deterministic mutation locality, exact repair-to-clean identity,
and pairwise repair commutativity for the four frozen mechanisms.

The script performs no diagnostic-class assignment and does not alter the
transferred prediction from the original P02 native study.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import p02_native_v2_raw as base

SCHEMA_VERSION = "p02_mathai_cross_context_smoke_raw_v2"
CONTEXT_SET_VERSION = "p02_mathai_cross_context_contexts_v1"
CONFORMANCE_VERSION = "p02_mathai_cross_context_conformance_v1"
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
    repair_of: str | None = None


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
    """Render the already-frozen source construction for a mechanism subset."""
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


def _replace_exactly_once(source: str, old: str, new: str, *, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one source anchor, found {count}")
    return source.replace(old, new, 1)


def apply_mutation(context: Context, source: str, mechanism: str) -> str:
    """Apply one frozen mutation as an exact source transformation."""
    if mechanism == "SOURCE_CORRUPTION":
        binders = theorem_binders(context)
        return _replace_exactly_once(
            source,
            f"theorem p02Native{binders} :\n",
            f"theorem{binders} :\n",
            label=f"{context.context_id}:{mechanism}:mutate",
        )
    if mechanism == "INVALID_PROOF":
        return _replace_exactly_once(
            source,
            f"{context.proof_line}\n",
            f"{context.invalid_proof_line}\n",
            label=f"{context.context_id}:{mechanism}:mutate",
        )
    if mechanism == "PROHIBITED_PLACEHOLDER":
        anchor = "\n".join(context.open_lines) + "\n\n"
        helper = "theorem p02Placeholder : True := by\n  sorry\n\n"
        return _replace_exactly_once(
            source,
            anchor,
            anchor + helper,
            label=f"{context.context_id}:{mechanism}:mutate",
        )
    if mechanism == "WRONG_TARGET":
        return _replace_exactly_once(
            source,
            f"    {context.clean_target_local} := by\n",
            f"    {context.wrong_target_local} := by\n",
            label=f"{context.context_id}:{mechanism}:mutate",
        )
    raise ValueError(f"unknown mechanism: {mechanism}")


def apply_repair(context: Context, source: str, mechanism: str) -> str:
    """Apply the exact deterministic inverse of one frozen mutation."""
    if mechanism == "SOURCE_CORRUPTION":
        binders = theorem_binders(context)
        return _replace_exactly_once(
            source,
            f"theorem{binders} :\n",
            f"theorem p02Native{binders} :\n",
            label=f"{context.context_id}:{mechanism}:repair",
        )
    if mechanism == "INVALID_PROOF":
        return _replace_exactly_once(
            source,
            f"{context.invalid_proof_line}\n",
            f"{context.proof_line}\n",
            label=f"{context.context_id}:{mechanism}:repair",
        )
    if mechanism == "PROHIBITED_PLACEHOLDER":
        helper = "theorem p02Placeholder : True := by\n  sorry\n\n"
        return _replace_exactly_once(
            source,
            helper,
            "",
            label=f"{context.context_id}:{mechanism}:repair",
        )
    if mechanism == "WRONG_TARGET":
        return _replace_exactly_once(
            source,
            f"    {context.wrong_target_local} := by\n",
            f"    {context.clean_target_local} := by\n",
            label=f"{context.context_id}:{mechanism}:repair",
        )
    raise ValueError(f"unknown mechanism: {mechanism}")


def source_digest(source: str) -> str:
    return base.sha256_bytes(source.encode("utf-8"))


def build_conformance_report() -> dict[str, Any]:
    """Check frozen mutation/repair mechanics before any native observation is collected."""
    single_checks: list[dict[str, Any]] = []
    pair_checks: list[dict[str, Any]] = []

    for context in CONTEXTS:
        clean = render_source(context, ())
        for mechanism in MECHANISMS:
            rendered_single = render_source(context, (mechanism,))
            transformed_single = apply_mutation(context, clean, mechanism)
            if transformed_single != rendered_single:
                raise AssertionError(
                    f"{context.context_id}:{mechanism}: mutation transform differs "
                    "from frozen renderer"
                )
            repaired = apply_repair(context, transformed_single, mechanism)
            if repaired != clean:
                raise AssertionError(
                    f"{context.context_id}:{mechanism}: exact inverse repair did not "
                    "restore clean source"
                )
            single_checks.append(
                {
                    "context_id": context.context_id,
                    "mechanism": mechanism,
                    "mutation_matches_frozen_renderer": True,
                    "repair_restores_byte_identical_clean_source": True,
                    "clean_source_sha256": source_digest(clean),
                    "mutated_source_sha256": source_digest(transformed_single),
                    "repaired_source_sha256": source_digest(repaired),
                }
            )

        for i, first in enumerate(MECHANISMS):
            for second in MECHANISMS[i + 1 :]:
                rendered_pair = render_source(context, (first, second))
                first_then_second = apply_mutation(
                    context, apply_mutation(context, clean, first), second
                )
                second_then_first = apply_mutation(
                    context, apply_mutation(context, clean, second), first
                )
                if first_then_second != rendered_pair or second_then_first != rendered_pair:
                    raise AssertionError(
                        f"{context.context_id}:{first}+{second}: mutation construction "
                        "is not order-invariant or differs from frozen renderer"
                    )

                repair_first_then_second = apply_repair(
                    context, apply_repair(context, rendered_pair, first), second
                )
                repair_second_then_first = apply_repair(
                    context, apply_repair(context, rendered_pair, second), first
                )
                if (
                    repair_first_then_second != clean
                    or repair_second_then_first != clean
                    or repair_first_then_second != repair_second_then_first
                ):
                    raise AssertionError(
                        f"{context.context_id}:{first}+{second}: pairwise repair "
                        "commutativity failed"
                    )
                pair_checks.append(
                    {
                        "context_id": context.context_id,
                        "mechanisms": [first, second],
                        "mutation_order_invariant": True,
                        "repair_commutative": True,
                        "both_repair_orders_restore_byte_identical_clean_source": True,
                        "pair_source_sha256": source_digest(rendered_pair),
                        "repaired_source_sha256": source_digest(clean),
                    }
                )

    expected_single = len(CONTEXTS) * len(MECHANISMS)
    expected_pairs = len(CONTEXTS) * (len(MECHANISMS) * (len(MECHANISMS) - 1) // 2)
    if len(single_checks) != expected_single:
        raise AssertionError(
            f"single conformance cardinality mismatch: {len(single_checks)}"
        )
    if len(pair_checks) != expected_pairs:
        raise AssertionError(f"pair conformance cardinality mismatch: {len(pair_checks)}")

    report: dict[str, Any] = {
        "schema_version": CONFORMANCE_VERSION,
        "status": "STATIC_CONFORMANCE_CHECKS_PASSED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "compound_states_executed": False,
        "repair_campaign_executed": False,
        "n_contexts": len(CONTEXTS),
        "n_mechanisms": len(MECHANISMS),
        "n_single_mutation_inverse_checks": len(single_checks),
        "n_pairwise_commutativity_checks": len(pair_checks),
        "single_checks": single_checks,
        "pair_checks": pair_checks,
        "scope": [
            "Checks deterministic source transformations against the already-frozen renderer.",
            "Checks that each exact inverse repair restores the byte-identical clean source.",
            "Checks pairwise repair commutativity for all unordered mechanism pairs in each context.",
            "These are construction-conformance checks, not scientific outcome classifications.",
        ],
    }
    report["conformance_digest"] = base.canonical_digest(report)
    return report


def build_smoke_cases() -> tuple[SmokeCase, ...]:
    cases: list[SmokeCase] = []
    for context in CONTEXTS:
        clean = render_source(context, ())
        cases.append(
            SmokeCase(
                case_id=f"{context.context_id}__CLEAN",
                context_id=context.context_id,
                role="clean_control",
                mechanisms=(),
                source=clean,
                target_statement=context.target_statement,
                theorem_name=context.theorem_name,
            )
        )
        for mechanism in MECHANISMS:
            mutated = apply_mutation(context, clean, mechanism)
            repaired = apply_repair(context, mutated, mechanism)
            if repaired != clean:
                raise AssertionError(
                    f"{context.context_id}:{mechanism}: repaired source differs from clean"
                )
            cases.append(
                SmokeCase(
                    case_id=f"{context.context_id}__{mechanism}",
                    context_id=context.context_id,
                    role="single_perturbation_smoke",
                    mechanisms=(mechanism,),
                    source=mutated,
                    target_statement=context.target_statement,
                    theorem_name=context.theorem_name,
                )
            )
            cases.append(
                SmokeCase(
                    case_id=f"{context.context_id}__{mechanism}__REPAIRED",
                    context_id=context.context_id,
                    role="single_perturbation_inverse_repair",
                    mechanisms=(),
                    source=repaired,
                    target_statement=context.target_statement,
                    theorem_name=context.theorem_name,
                    repair_of=mechanism,
                )
            )

    if len(cases) != 27:
        raise AssertionError(f"feasibility cardinality mismatch: {len(cases)}")
    if len({case.case_id for case in cases}) != len(cases):
        raise AssertionError("duplicate feasibility case ids")

    for context in CONTEXTS:
        clean_source = render_source(context, ())
        context_cases = [case for case in cases if case.context_id == context.context_id]
        repaired_cases = [
            case
            for case in context_cases
            if case.role == "single_perturbation_inverse_repair"
        ]
        if len(repaired_cases) != len(MECHANISMS):
            raise AssertionError(
                f"{context.context_id}: inverse-repair case cardinality mismatch"
            )
        if any(case.source != clean_source for case in repaired_cases):
            raise AssertionError(
                f"{context.context_id}: inverse-repair execution source is not clean-identical"
            )

    return tuple(cases)


def smoke_projection(cases: Sequence[SmokeCase]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "context_id": case.context_id,
            "role": case.role,
            "mechanisms": list(case.mechanisms),
            "repair_of": case.repair_of,
            "source_sha256": source_digest(case.source),
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
        raise RuntimeError(
            "environment validation failed: " + "; ".join(environment_errors)
        )

    # These construction-conformance checks are evaluated before any native case
    # is executed. They inspect source transformations only and perform no
    # diagnostic classification.
    conformance = build_conformance_report()
    base.json_dump(out / "CONFORMANCE.json", conformance)

    cases = build_smoke_cases()
    projection = smoke_projection(cases)
    context_spec = {
        "schema_version": SCHEMA_VERSION,
        "context_set_version": CONTEXT_SET_VERSION,
        "conformance_version": CONFORMANCE_VERSION,
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "mechanisms": list(MECHANISMS),
        "contexts": [asdict(context) for context in CONTEXTS],
        "cases": projection,
        "conformance_digest": conformance["conformance_digest"],
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
                    "repair_of": case.repair_of,
                    "target_statement": case.target_statement,
                    "theorem_name": case.theorem_name,
                },
            )

    run_manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "FULL_FEASIBILITY_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "compound_states_executed": False,
        "repair_campaign_executed": False,
        "n_cases": len(cases),
        "n_contexts": len(CONTEXTS),
        "n_clean_cases": len(CONTEXTS),
        "n_single_perturbation_cases": len(CONTEXTS) * len(MECHANISMS),
        "n_inverse_repair_cases": len(CONTEXTS) * len(MECHANISMS),
        "n_pairwise_commutativity_checks": len(conformance["pair_checks"]),
        "context_smoke_digest": context_spec["context_smoke_digest"],
        "conformance_digest": conformance["conformance_digest"],
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "non_claims": [
            "Feasibility outcomes are not the cross-context compound replication result.",
            "The transferred observation ordering from the original P02 study is not modified by feasibility outcomes.",
            "No context may be dropped for an unfavorable single-perturbation signature.",
            "Construction metadata is not a diagnostic oracle and is stored separately from observations.",
            "Static repair-conformance checks do not establish scientific transfer or external validity.",
        ],
    }
    base.json_dump(out / "RUN_MANIFEST.json", run_manifest)

    files = base.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_smoke_integrity_v2",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": base.canonical_digest({"files": files}),
    }
    base.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(
        json.dumps(
            {"run": run_manifest, "conformance": conformance, "integrity": integrity},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
