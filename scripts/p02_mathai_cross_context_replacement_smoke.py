#!/usr/bin/env python3
"""Run the predeclared MATH-AI cross-context replacement feasibility smoke.

Design provenance: the context-selection and replication design were frozen in
fraware/labtrust-portfolio on 2026-08-27, before MATH-AI review outcomes. This
script executes only the preregistered feasibility stage: clean, four singleton
mutations, and the exact inverse repair of each singleton in each selected
context. It does not execute compound states.

The initial three-context smoke is retained unchanged in branch ancestry. All
three selected contexts failed the feasibility gate because the frozen
WRONG_TARGET source edit remained target-matching. The August 27 protocol
predeclared the ordered replacement list IdealMembership, Counterexample,
Level. This script applies those three replacements one-for-one and fixes
their exact clean and wrong targets before any replacement execution. No
fallback target is attempted after execution.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import p02_native_v2_raw as frozen

SCHEMA_VERSION = "p02_mathai_cross_context_replacement_smoke_raw_v1"
EXPECTED_PROJECT_SHA = frozen.EXPECTED_PROJECT_SHA
EXPECTED_TOOLCHAIN = frozen.EXPECTED_TOOLCHAIN
EXPECTED_LEAN_VERSION = frozen.EXPECTED_LEAN_VERSION

MECHANISMS: tuple[str, ...] = (
    "SOURCE_CORRUPTION",
    "INVALID_PROOF",
    "PROHIBITED_PLACEHOLDER",
    "WRONG_TARGET",
)


@dataclass(frozen=True)
class Context:
    context_id: str
    label: str
    import_line: str
    open_lines: tuple[str, ...]
    namespace: str
    binders: str
    clean_statement: str
    wrong_statement: str
    clean_proof: str
    target_statement: str


CONTEXTS: tuple[Context, ...] = (
    Context(
        context_id="RX1",
        label="IdealMembership",
        import_line="import MathEvidence.Assurance.IdealMembership",
        open_lines=("open MathEvidence.Assurance.IdealMembership",),
        namespace="P02CrossContext.IdealMembership",
        binders="",
        clean_statement="contract.claimsCompleteness = false",
        wrong_statement="contract.linksDecls = true",
        clean_proof="native_decide",
        target_statement="contract.claimsCompleteness = false",
    ),
    Context(
        context_id="RX2",
        label="Counterexample",
        import_line="import MathEvidence.Assurance.Counterexample",
        open_lines=("open MathEvidence.Assurance.Counterexample",),
        namespace="P02CrossContext.Counterexample",
        binders="",
        clean_statement="contract.claimsCompleteness = false",
        wrong_statement="contract.assuranceLevel = .verifiedReferenceAlgorithm",
        clean_proof="native_decide",
        target_statement="contract.claimsCompleteness = false",
    ),
    Context(
        context_id="RX3",
        label="Level",
        import_line="import MathEvidence.Assurance.Level",
        open_lines=("open MathEvidence.Assurance",),
        namespace="P02CrossContext.Level",
        binders="",
        clean_statement='AssuranceLevel.toWire .outputVerification = "output_verification"',
        wrong_statement='AssuranceLevel.toWire .checkerSoundness = "checker_soundness"',
        clean_proof="rfl",
        target_statement='AssuranceLevel.toWire .outputVerification = "output_verification"',
    ),
)


def theorem_name(ctx: Context) -> str:
    return f"{ctx.namespace}.p02Native"


def render_source(ctx: Context, mechanisms: Iterable[str]) -> str:
    active = frozenset(mechanisms)
    unknown = active.difference(MECHANISMS)
    if unknown:
        raise ValueError(f"unknown mechanisms: {sorted(unknown)}")

    lines = [ctx.import_line, *ctx.open_lines, "", f"namespace {ctx.namespace}", ""]

    if "PROHIBITED_PLACEHOLDER" in active:
        lines.extend(
            [
                "theorem p02Placeholder : True := by",
                "  sorry",
                "",
            ]
        )

    statement = (
        ctx.wrong_statement if "WRONG_TARGET" in active else ctx.clean_statement
    )
    proof = "exact True.intro" if "INVALID_PROOF" in active else ctx.clean_proof

    binder_text = f" {ctx.binders}" if ctx.binders else ""
    if "SOURCE_CORRUPTION" in active:
        lines.append(f"theorem p02Native{binder_text} ( : {statement} := by")
    else:
        lines.append(f"theorem p02Native{binder_text} : {statement} := by")
    lines.append(f"  {proof}")
    lines.extend(["", f"end {ctx.namespace}", ""])
    return "\n".join(lines)


def construction_checks() -> dict[str, Any]:
    contexts: list[dict[str, Any]] = []
    for ctx in CONTEXTS:
        clean = render_source(ctx, ())
        singleton_checks: list[dict[str, Any]] = []
        for mechanism in MECHANISMS:
            mutated = render_source(ctx, (mechanism,))
            repaired = render_source(ctx, ())
            singleton_checks.append(
                {
                    "mechanism": mechanism,
                    "mutated_differs_from_clean": mutated != clean,
                    "inverse_repair_equals_clean": repaired == clean,
                }
            )

        pairwise: list[dict[str, Any]] = []
        for subset_size in range(2, len(MECHANISMS) + 1):
            for subset_tuple in itertools.combinations(MECHANISMS, subset_size):
                subset = frozenset(subset_tuple)
                for first, second in itertools.combinations(sorted(subset), 2):
                    left = render_source(ctx, subset.difference((first, second)))
                    right = render_source(ctx, subset.difference((second, first)))
                    pairwise.append(
                        {
                            "subset": sorted(subset),
                            "first": first,
                            "second": second,
                            "commutes": left == right,
                        }
                    )

        contexts.append(
            {
                "context_id": ctx.context_id,
                "label": ctx.label,
                "clean_source_sha256": frozen.sha256_bytes(clean.encode("utf-8")),
                "singleton_checks": singleton_checks,
                "pairwise_repair_checks": pairwise,
            }
        )

    all_singleton_local = all(
        row["mutated_differs_from_clean"] and row["inverse_repair_equals_clean"]
        for ctx in contexts
        for row in ctx["singleton_checks"]
    )
    all_pairwise_commute = all(
        row["commutes"]
        for ctx in contexts
        for row in ctx["pairwise_repair_checks"]
    )
    return {
        "schema_version": "p02_mathai_cross_context_replacement_construction_checks_v1",
        "all_singleton_local": all_singleton_local,
        "all_pairwise_repairs_commute": all_pairwise_commute,
        "contexts": contexts,
    }


def smoke_cases() -> tuple[frozen.Case, ...]:
    cases: list[frozen.Case] = []
    for ctx in CONTEXTS:
        clean_source = render_source(ctx, ())
        cases.append(
            frozen.Case(
                case_id=f"{ctx.context_id}-SMOKE-CLEAN",
                role="cross_context_smoke_clean",
                mechanisms=(),
                source=clean_source,
                target_statement=ctx.target_statement,
                theorem_name=theorem_name(ctx),
            )
        )
        for mechanism in MECHANISMS:
            cases.append(
                frozen.Case(
                    case_id=f"{ctx.context_id}-SMOKE-{mechanism}",
                    role="cross_context_smoke_singleton",
                    mechanisms=(mechanism,),
                    source=render_source(ctx, (mechanism,)),
                    target_statement=ctx.target_statement,
                    theorem_name=theorem_name(ctx),
                )
            )
            cases.append(
                frozen.Case(
                    case_id=f"{ctx.context_id}-SMOKE-{mechanism}__REPAIR",
                    role="cross_context_smoke_inverse_repair",
                    mechanisms=(),
                    source=clean_source,
                    target_statement=ctx.target_statement,
                    theorem_name=theorem_name(ctx),
                )
            )
    if len(cases) != 27:
        raise AssertionError(f"expected 27 smoke executions, found {len(cases)}")
    return tuple(cases)


def case_projection(cases: tuple[frozen.Case, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        rows.append(
            {
                "case_id": case.case_id,
                "role": case.role,
                "mechanisms": list(case.mechanisms),
                "source_sha256": frozen.sha256_bytes(case.source.encode("utf-8")),
                "target_sha256": frozen.sha256_bytes(
                    case.target_statement.encode("utf-8")
                ),
                "theorem_name": case.theorem_name,
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

    checks = construction_checks()
    frozen.json_dump(out / "CONSTRUCTION_CHECKS.json", checks)
    if not checks["all_singleton_local"]:
        raise RuntimeError("singleton locality/inverse-repair construction check failed")
    if not checks["all_pairwise_repairs_commute"]:
        raise RuntimeError("pairwise repair commutativity construction check failed")

    environment = frozen.environment_snapshot(project)
    frozen.json_dump(out / "ENVIRONMENT.json", environment)
    errors = frozen.validate_environment(environment)
    if errors:
        frozen.json_dump(
            out / "STATUS.json",
            {
                "schema_version": SCHEMA_VERSION,
                "status": "BLOCKED_ENVIRONMENT",
                "publication_claim_eligible": False,
                "errors": errors,
            },
        )
        raise RuntimeError("; ".join(errors))

    cases = smoke_cases()
    projection = case_projection(cases)
    smoke_spec = {
        "schema_version": "p02_mathai_cross_context_replacement_smoke_spec_v1",
        "design_frozen_date": "2026-08-27",
        "publication_claim_eligible": False,
        "pinned_project_sha": EXPECTED_PROJECT_SHA,
        "pinned_toolchain": EXPECTED_TOOLCHAIN,
        "contexts": [asdict(ctx) for ctx in CONTEXTS],
        "mechanisms": list(MECHANISMS),
        "replacement_mapping": {
            "CX1": "RX1:IdealMembership",
            "CX2": "RX2:Counterexample",
            "CX3": "RX3:Level",
        },
        "n_executions": len(cases),
        "cases": projection,
        "full_compound_lattice_executed": False,
    }
    smoke_spec["spec_digest"] = frozen.canonical_digest(
        {k: v for k, v in smoke_spec.items() if k != "spec_digest"}
    )
    frozen.json_dump(out / "SMOKE_SPEC.json", smoke_spec)

    with tempfile.TemporaryDirectory(prefix="p02-mathai-xc-smoke-") as tmp:
        scratch = Path(tmp)
        for case in cases:
            observations = frozen.collect_case(
                case,
                project=project,
                scratch=scratch,
                timeout_seconds=args.timeout_seconds,
            )
            frozen.write_case_bundle(out, case, observations)

    post_status = frozen.git_observation(project, "status", "--porcelain")
    post_text = frozen.successful_stdout(post_status)
    if post_text is None:
        raise RuntimeError("unable to read pinned worktree status after smoke")
    if post_text:
        raise RuntimeError(f"pinned worktree changed during smoke: {post_text!r}")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "SMOKE_RAW_EXECUTED_NOT_CLASSIFIED",
        "publication_claim_eligible": False,
        "classification_performed": False,
        "full_compound_lattice_executed": False,
        "expected_project_sha": EXPECTED_PROJECT_SHA,
        "expected_toolchain": EXPECTED_TOOLCHAIN,
        "expected_lean_version": EXPECTED_LEAN_VERSION,
        "n_cases": len(cases),
        "smoke_spec_digest": smoke_spec["spec_digest"],
        "harness_branch_sha": os.environ.get("GITHUB_SHA"),
        "non_claims": [
            "This bundle is replacement feasibility-smoke evidence only; the failed initial smoke remains unchanged.",
            "No compound cross-context state or intervention result exists in this bundle.",
            "Smoke outcomes may not be used to rewrite the transferred precedence prediction.",
            "Publication promotion remains blocked pending full replication and independent review.",
        ],
    }
    frozen.json_dump(out / "RUN_MANIFEST.json", manifest)

    files = frozen.inventory(out)
    integrity = {
        "schema_version": "p02_mathai_cross_context_replacement_smoke_integrity_v1",
        "publication_claim_eligible": False,
        "n_files": len(files),
        "files": files,
        "bundle_digest": frozen.canonical_digest({"files": files}),
    }
    frozen.json_dump(out / "INTEGRITY_MANIFEST.json", integrity)
    print(json.dumps({"run": manifest, "integrity": integrity}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
