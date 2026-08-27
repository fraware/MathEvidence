#!/usr/bin/env python3
"""Diagnostic-only probe for staged rational native reduction.

This script never emits or accepts a Certification Record. It tests the exact
Lean 4.14 boundary required by ``Lean.reduceBool``: candidate-specific closed
Boolean computations are elaborated first as an imported module, then a second
theorem module consumes those imported constants through ``Lean.ofReduceBool``.
Production acceptance remains owned by ``run_cr_exact_lean_e2e_production.py``
and ``kernel_replay._compile_and_inspect``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import adapters.common.exact_replay.plugins  # noqa: F401
from adapters.common.exact_replay.pipeline import generate_module, verify
from adapters.common.kernel_replay import _run_process, find_lake

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "ci" / "run_cr_exact_lean_e2e_production.py"
RUNNER_MODULE = "mathevidence_native_compile_probe_runner"
BASE_MODULE = "MathEvidence.Generated.Replay.probe_rational_native_compile"
COMPUTE_MODULE = f"{BASE_MODULE}Compute"
THEOREM_MODULE = f"{BASE_MODULE}Theorem"
DECL = "probe_rational_native_compile"


def _load_runner():
    spec = importlib.util.spec_from_file_location(RUNNER_MODULE, RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production runner from {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(RUNNER_MODULE)
    sys.modules[RUNNER_MODULE] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(RUNNER_MODULE, None)
        else:
            sys.modules[RUNNER_MODULE] = previous
        raise
    return module, previous


def _staged_sources(source: str) -> tuple[str, str]:
    marker = "/-- Lean-side equality between reconstructed wire binding and submitted digest."
    if marker not in source:
        raise RuntimeError("expected rational request-binding marker not found")
    prefix = source.split(marker, 1)[0]
    compute = (
        prefix
        + f"""/-- Closed candidate-specific request-binding computation. -/\ndef {DECL}_binding_bool : Bool :=\n  decide ({DECL}_req.requestDigest = {DECL}_cert.requestDigest)\n\n/-- Closed candidate-specific checker proposition computation. -/\ndef {DECL}_checker_decide_bool : Bool :=\n  decide (checkBool {DECL}_req {DECL}_cert = true)\n"""
    )
    theorem = f"""/- Diagnostic theorem stage; never Certification Record authority. -/\nimport {COMPUTE_MODULE}\n\nopen MathEvidence.Core\nopen MathEvidence.IR.RationalExpr\nopen MathEvidence.Checkers.RationalEquality\n\n/-- Request digest is recomputed by Request.ofClaim! in the imported candidate module. -/\ntheorem {DECL}_request_binding :\n    {DECL}_req.requestDigest = {DECL}_cert.requestDigest :=\n  of_decide_eq_true\n    (Lean.ofReduceBool {DECL}_binding_bool true (Eq.refl true))\n\n/-- Candidate-specific semantic theorem from the independently evaluated checker. -/\ntheorem {DECL} : Claim.proposition {DECL}_req.claim {DECL}_cert.denomFactors := by\n  have hcheck : checkBool {DECL}_req {DECL}_cert = true :=\n    of_decide_eq_true\n      (Lean.ofReduceBool {DECL}_checker_decide_bool true (Eq.refl true))\n  exact replaySound {DECL}_req {DECL}_cert hcheck\n\n#print axioms {DECL}_request_binding\n#print axioms {DECL}\n"""
    return compute, theorem


def _path_for(module_name: str, suffix: str) -> Path:
    return ROOT.joinpath(*module_name.split(".")).with_suffix(suffix)


def _build_path(module_name: str, suffix: str) -> Path:
    return (ROOT / ".lake" / "build" / "lib").joinpath(*module_name.split(".")).with_suffix(suffix)


def main() -> int:
    runner, previous = _load_runner()
    try:
        case = next(
            item
            for item in runner.matrix._cases()
            if item.capability == "algebra.rational_equality"
        )
        request, certificate = runner._canonical_case_payload(case)
        module = generate_module(
            capability_id=case.capability,
            request=request,
            certificate=certificate,
            candidate_bundle_digest=runner.BUNDLE_DIGEST,
            module_name=BASE_MODULE,
            declaration_name=DECL,
        )
        metadata = verify(module)
        if not metadata.ok:
            raise RuntimeError(f"generated module metadata failed: {metadata.detail}")
        if f"Request.ofClaim! {DECL}_claim" not in module.source_text:
            raise RuntimeError("probe source is not candidate-bound through Request.ofClaim!")
        if "OfflineFixtures" in module.source_text:
            raise RuntimeError("probe source unexpectedly references OfflineFixtures")

        compute_source, theorem_source = _staged_sources(module.source_text)
        if "Request.ofClaim!" not in compute_source:
            raise RuntimeError("compute stage lost Lean-side request digest reconstruction")
        if f"decide (checkBool {DECL}_req {DECL}_cert = true)" not in compute_source:
            raise RuntimeError("compute stage does not decide the exact checker proposition")
        if "Lean.ofReduceBool" not in theorem_source:
            raise RuntimeError("theorem stage does not consume compiled Boolean constants")
        if "native_decide" in theorem_source:
            raise RuntimeError("theorem stage unexpectedly creates a fresh native_decide auxiliary")

        lake = find_lake(ROOT)
        if lake is None:
            raise RuntimeError("lake unavailable")

        compute_source_path = _path_for(COMPUTE_MODULE, ".lean")
        theorem_source_path = _path_for(THEOREM_MODULE, ".lean")
        compute_olean = _build_path(COMPUTE_MODULE, ".olean")
        theorem_olean = _build_path(THEOREM_MODULE, ".olean")
        compute_c = (ROOT / ".lake" / "build" / "ir").joinpath(
            *COMPUTE_MODULE.split(".")
        ).with_suffix(".c")
        for path in (compute_source_path, theorem_source_path, compute_olean, theorem_olean, compute_c):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.unlink(missing_ok=True)

        compute_source_path.write_text(compute_source, encoding="utf-8", newline="\n")
        theorem_source_path.write_text(theorem_source, encoding="utf-8", newline="\n")
        compute_proc = None
        theorem_proc = None
        try:
            compute_proc = _run_process(
                [
                    str(lake),
                    "env",
                    "lean",
                    "-o",
                    str(compute_olean),
                    "-c",
                    str(compute_c),
                    str(compute_source_path),
                ],
                root=ROOT,
            )
            if compute_proc.returncode == 0:
                theorem_proc = _run_process(
                    [
                        str(lake),
                        "env",
                        "lean",
                        "-o",
                        str(theorem_olean),
                        str(theorem_source_path),
                    ],
                    root=ROOT,
                )

            report = {
                "schemaVersion": "0.4.0",
                "status": "diagnostic_only_non_authoritative",
                "capability": case.capability,
                "requestDigest": request["requestDigest"],
                "generatedSourceHash": module.source_hash,
                "probeTransformation": "precompile_decided_binding_and_checker_propositions_then_ofReduceBool",
                "computeReturnCode": compute_proc.returncode,
                "theoremReturnCode": None if theorem_proc is None else theorem_proc.returncode,
                "computeOleanExists": compute_olean.is_file(),
                "computeCExists": compute_c.is_file(),
                "theoremOleanExists": theorem_olean.is_file(),
                "computeStdoutTail": (compute_proc.stdout or "")[-2500:],
                "computeStderrTail": (compute_proc.stderr or "")[-2500:],
                "theoremStdoutTail": "" if theorem_proc is None else (theorem_proc.stdout or "")[-2500:],
                "theoremStderrTail": "" if theorem_proc is None else (theorem_proc.stderr or "")[-2500:],
            }
            print(json.dumps(report, sort_keys=True))
            if compute_proc.returncode != 0 or theorem_proc is None or theorem_proc.returncode != 0:
                return 1
            if not compute_olean.is_file() or not theorem_olean.is_file():
                raise RuntimeError("staged probe reported success without both .olean files")
            return 0
        finally:
            for path in (
                compute_source_path,
                theorem_source_path,
                compute_olean,
                theorem_olean,
                compute_c,
            ):
                path.unlink(missing_ok=True)
    finally:
        if previous is None:
            sys.modules.pop(RUNNER_MODULE, None)
        else:
            sys.modules[RUNNER_MODULE] = previous


if __name__ == "__main__":
    raise SystemExit(main())
