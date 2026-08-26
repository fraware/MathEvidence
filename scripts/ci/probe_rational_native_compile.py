#!/usr/bin/env python3
"""Diagnostic-only probe for generated rational native_decide elaboration.

This script never emits or accepts a Certification Record. It tests whether
unfolding current-module candidate aliases before ``native_decide`` removes the
Lean 4.14 current-module native-evaluation dependency while preserving the
exact candidate-bound proposition. Production acceptance remains owned by
``run_cr_exact_lean_e2e_production.py`` and ``kernel_replay._compile_and_inspect``.
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


def _unfold_before_native_decide(source: str, decl: str) -> str:
    binding_old = " := by\n  native_decide\n\n/-- Exact Candidate Bundle semantic claim."
    binding_new = (
        " := by\n"
        f"  simp only [{decl}_req, {decl}_claim]\n"
        "  native_decide\n\n"
        "/-- Exact Candidate Bundle semantic claim."
    )
    if binding_old not in source:
        raise RuntimeError("expected request-binding native_decide proof not found")
    source = source.replace(binding_old, binding_new, 1)

    check_old = f"(by native_decide : checkBool {decl}_req {decl}_cert = true)"
    check_new = (
        "(by\n"
        f"      simp only [{decl}_req, {decl}_claim, {decl}_cert]\n"
        f"      native_decide : checkBool {decl}_req {decl}_cert = true)"
    )
    if check_old not in source:
        raise RuntimeError("expected checker native_decide proof not found")
    return source.replace(check_old, check_new, 1)


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
            module_name="MathEvidence.Generated.Replay.probe_rational_native_compile",
            declaration_name="probe_rational_native_compile",
        )
        metadata = verify(module)
        if not metadata.ok:
            raise RuntimeError(f"generated module metadata failed: {metadata.detail}")
        if "Request.ofClaim! probe_rational_native_compile_claim" not in module.source_text:
            raise RuntimeError("probe source is not candidate-bound through Request.ofClaim!")
        if "native_decide" not in module.source_text:
            raise RuntimeError("probe source does not exercise native_decide")
        if "OfflineFixtures" in module.source_text:
            raise RuntimeError("probe source unexpectedly references OfflineFixtures")

        source = _unfold_before_native_decide(
            module.source_text, module.declaration_name
        )
        if "simp only [probe_rational_native_compile_req, probe_rational_native_compile_claim]" not in source:
            raise RuntimeError("request-binding alias unfolding was not injected")
        if "simp only [probe_rational_native_compile_req, probe_rational_native_compile_claim, probe_rational_native_compile_cert]" not in source:
            raise RuntimeError("checker alias unfolding was not injected")

        lake = find_lake(ROOT)
        if lake is None:
            raise RuntimeError("lake unavailable")

        source_path = ROOT / "MathEvidence" / "Generated" / "Replay" / "probe_rational_native_compile.lean"
        build_root = ROOT / ".lake" / "build" / "mathevidence-native-probe"
        olean_path = build_root / "probe_rational_native_compile.olean"
        c_path = build_root / "probe_rational_native_compile.c"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        build_root.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8", newline="\n")
        try:
            proc = _run_process(
                [
                    str(lake),
                    "env",
                    "lean",
                    "-o",
                    str(olean_path),
                    "-c",
                    str(c_path),
                    str(source_path),
                ],
                root=ROOT,
            )
            report = {
                "schemaVersion": "0.2.0",
                "status": "diagnostic_only_non_authoritative",
                "capability": case.capability,
                "requestDigest": request["requestDigest"],
                "generatedSourceHash": module.source_hash,
                "probeTransformation": "unfold_current_module_aliases_before_native_decide",
                "returnCode": proc.returncode,
                "oleanExists": olean_path.is_file(),
                "cExists": c_path.is_file(),
                "stdoutTail": (proc.stdout or "")[-3000:],
                "stderrTail": (proc.stderr or "")[-3000:],
            }
            print(json.dumps(report, sort_keys=True))
            if proc.returncode != 0:
                return 1
            if not olean_path.is_file() or not c_path.is_file():
                raise RuntimeError("probe reported success without both .olean and C outputs")
            return 0
        finally:
            source_path.unlink(missing_ok=True)
            olean_path.unlink(missing_ok=True)
            c_path.unlink(missing_ok=True)
    finally:
        if previous is None:
            sys.modules.pop(RUNNER_MODULE, None)
        else:
            sys.modules[RUNNER_MODULE] = previous


if __name__ == "__main__":
    raise SystemExit(main())
