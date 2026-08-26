from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from adapters.common.canonical import verify_request_digest

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts" / "ci" / "run_cr_exact_lean_e2e_production.py"
RUNNER_MODULE_NAME = "mathevidence_cr_exact_production_loader_test"
MATRIX_MODULE_NAME = "mathevidence_cr_exact_matrix"


def _restore_module(name: str, previous: ModuleType | None) -> None:
    if previous is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = previous


def _load_runner() -> tuple[ModuleType, ModuleType | None, ModuleType | None]:
    previous_runner = sys.modules.get(RUNNER_MODULE_NAME)
    previous_matrix = sys.modules.get(MATRIX_MODULE_NAME)

    spec = importlib.util.spec_from_file_location(RUNNER_MODULE_NAME, RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    sys.modules[RUNNER_MODULE_NAME] = runner
    spec.loader.exec_module(runner)
    return runner, previous_runner, previous_matrix


def test_production_runner_registers_dataclass_matrix_module_and_binds_requests() -> None:
    """The production runner must load and canonically bind its synthetic matrix.

    Python 3.12 dataclasses resolve postponed annotations through
    ``sys.modules[cls.__module__]`` while the class is created. Executing a
    module returned by ``module_from_spec`` without registering it first makes
    that lookup fail before the production Lean gate can run.

    The checked-in E2E cases also use readable placeholder request digests.
    Production execution must replace those placeholders with the canonical
    request binding used by real Candidate Bundles and synchronize the exact
    certificate before Lean compilation.
    """
    runner, previous_runner, previous_matrix = _load_runner()

    try:
        matrix = runner.matrix
        assert matrix.__name__ == MATRIX_MODULE_NAME
        assert sys.modules.get(MATRIX_MODULE_NAME) is matrix
        assert matrix.ExactCase.__module__ == MATRIX_MODULE_NAME

        cases = matrix._cases()
        assert cases
        for case in cases:
            request, certificate = runner._canonical_case_payload(case)
            digest = verify_request_digest(request)
            assert request["requestDigest"] == digest
            assert certificate["requestDigest"] == digest
    finally:
        _restore_module(RUNNER_MODULE_NAME, previous_runner)
        _restore_module(MATRIX_MODULE_NAME, previous_matrix)


def test_rational_failure_diagnostic_is_non_authoritative() -> None:
    """The failure companion may print bindings but must contain no proof authority."""
    runner, previous_runner, previous_matrix = _load_runner()

    try:
        case = next(
            item
            for item in runner.matrix._cases()
            if item.capability == "algebra.rational_equality"
        )
        request, certificate = runner._canonical_case_payload(case)
        module = runner.generate_module(
            capability_id=case.capability,
            request=request,
            certificate=certificate,
            candidate_bundle_digest=runner.BUNDLE_DIGEST,
            module_name=f"MathEvidence.Generated.Replay.release_{case.name}",
            declaration_name=f"release_{case.name}",
        )
        source = runner._rational_binding_diagnostic_source(case, module)
        assert source is not None
        assert "MATHEVIDENCE_DIAG_CANONICAL=" in source
        assert "MATHEVIDENCE_DIAG_DIGEST=" in source
        assert "\ntheorem " not in source
        assert "\n  native_decide\n" not in source
        assert "(by native_decide" not in source
        assert "#print axioms" not in source
        assert f"{module.declaration_name}_req.requestDigest.value" in source
    finally:
        _restore_module(RUNNER_MODULE_NAME, previous_runner)
        _restore_module(MATRIX_MODULE_NAME, previous_matrix)
