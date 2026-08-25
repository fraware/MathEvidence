"""SPEC-11 generated-replay adversarial security coverage (no Lake required)."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from adapters.common.bounded_process import (
    EXECUTION_POLICY_ID,
    confine_under_workspace,
    filter_environ,
    run_bounded,
)
from adapters.common.errors import AdapterError
from adapters.common.exact_replay.pipeline import generate_module
from adapters.common.limits import ResourceLimits
from adapters.common.security_bounds import (
    enforce_integer_digits,
    enforce_nesting_depth,
    reject_path_traversal,
    reject_symlink_escape,
    walk_enforce_integer_digits,
)

ROOT = Path(__file__).resolve().parents[2]


def _poly(m: int, coefficient: int, exponents: list[int]) -> dict:
    return {
        "varCount": m,
        "terms": [{"coefficient": coefficient, "exponents": exponents}],
    }


def test_execution_policy_id_stable() -> None:
    assert EXECUTION_POLICY_ID == "mathevidence.kernel_replay.argv_only.v1"


@pytest.mark.parametrize(
    "path",
    [
        "../escape.lean",
        "..\\escape.lean",
        "/etc/passwd",
        "C:/Windows/System32/cmd.exe",
        "MathEvidence/Generated/Replay/../../secrets",
    ],
)
def test_reject_dotdot_and_absolute_paths(path: str) -> None:
    with pytest.raises(AdapterError) as exc:
        reject_path_traversal(path)
    assert exc.value.code == "malformed_evidence"


def test_confine_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(AdapterError):
        confine_under_workspace("../outside", root=tmp_path)


def test_shell_metacharacters_never_reach_shell(tmp_path: Path) -> None:
    # Argv with metacharacters must not be interpreted by a shell.
    marker = tmp_path / "should_not_exist"
    evil = f"echo hi > {marker}; echo"
    result = run_bounded(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", evil],
        cwd=tmp_path,
        limits=ResourceLimits(max_wall_time_ms=10_000, max_output_bytes=65536),
        use_env_allowlist=True,
    )
    assert result.returncode == 0
    assert evil in result.stdout
    assert not marker.exists()


def test_lean_looking_strings_in_data_fields_are_escaped() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.ideal_membership_witness",
        "capabilityVersion": "0.1.0",
        "target": _poly(2, 1, [1, 1]),
        "generators": [_poly(2, 1, [1, 0]), _poly(2, 1, [0, 1])],
        "requestedClaim": "witness",
        "requestDigest": "sha256:" + ("12" * 32),
        "notes": ["theorem evil : False := sorry", '"; import System'],
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    module = generate_module(
        capability_id="algebra.ideal_membership_witness",
        request=request,
        certificate=certificate,
        candidate_bundle_digest="sha256:" + ("3" * 64),
        module_name="MathEvidence.Generated.Replay.sec_notes",
        declaration_name="sec_notes",
    )
    # Notes must appear only as Lean string literals (JSON-escaped), not raw syntax.
    assert "theorem evil" in module.source_text
    assert '"; import System' not in module.source_text or '\\"' in module.source_text
    assert "sorry" in module.source_text  # inside a string literal
    # The payload string is quoted via json.dumps — not free Lean.
    assert 'some ["theorem evil' in module.source_text or 'some ["theorem evil : False := sorry"' in module.source_text


def test_extreme_nesting_rejected() -> None:
    node: dict = {"tag": "int", "value": "1"}
    for _ in range(80):
        node = {"tag": "neg", "arg": node}
    with pytest.raises(AdapterError) as exc:
        enforce_nesting_depth(node, limits=ResourceLimits(max_nesting_depth=64))
    assert exc.value.code == "resource_limit_exceeded"


def test_extreme_integer_rejected() -> None:
    with pytest.raises(AdapterError):
        enforce_integer_digits("9" * 5000, max_digits=4096)
    with pytest.raises(AdapterError):
        walk_enforce_integer_digits({"tag": "int", "value": "9" * 5000})


def test_leading_zero_padding_counts_toward_digit_limit() -> None:
    """Padded numerals must not bypass max_digits via lstrip('0')."""
    from adapters.common.security_bounds import integer_digit_count

    assert integer_digit_count("0001") == 4
    with pytest.raises(AdapterError):
        enforce_integer_digits("0" * 5000 + "1", max_digits=4096)


def test_extreme_matrix_dimensions_rejected_by_plugin() -> None:
    # Linear algebra plugin rejects oversized dimensions before render.
    from adapters.common.exact_replay.plugins.linear_algebra import (
        generate_exact_linear_algebra_module,
    )

    huge = 10_000
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "operation": "det_identity",
        "matrix": {
            "tag": "matrix",
            "rows": huge,
            "cols": huge,
            "entries": [],
        },
        "requestedClaim": "soundResult",
        "requestDigest": "sha256:" + ("ab" * 32),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.linear_algebra",
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "operation": "det_identity",
        "claimClass": "soundResult",
        "result": {"tag": "rat", "num": "0", "den": "1"},
    }
    with pytest.raises((AdapterError, ValueError)):
        generate_exact_linear_algebra_module(
            module_name="MathEvidence.Generated.Replay.huge_det",
            declaration_name="huge_det",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("cd" * 32),
        )


def test_output_flood_capped(tmp_path: Path) -> None:
    with pytest.raises(AdapterError) as exc:
        run_bounded(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.write('x' * 200000)",
            ],
            cwd=tmp_path,
            limits=ResourceLimits(max_wall_time_ms=10_000, max_output_bytes=1024),
            use_env_allowlist=True,
        )
    assert exc.value.code == "resource_limit_exceeded"
    assert (exc.value.details or {}).get("kind") == "output_bytes"


def test_hanging_child_group_kill(tmp_path: Path) -> None:
    t0 = time.monotonic()
    with pytest.raises(AdapterError) as exc:
        run_bounded(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tmp_path,
            limits=ResourceLimits(max_wall_time_ms=500, max_output_bytes=65536),
            use_env_allowlist=True,
        )
    elapsed = time.monotonic() - t0
    assert exc.value.code == "resource_limit_exceeded"
    assert (exc.value.details or {}).get("kind") == "wall_time"
    assert (exc.value.details or {}).get("killedProcessGroup") is True
    assert elapsed < 10.0


@pytest.mark.skipif(sys.platform == "win32" and not hasattr(os, "symlink"), reason="symlink")
def test_symlink_escape_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("nope", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    link = workspace / "escape"
    try:
        link.symlink_to(secret)
    except OSError:
        pytest.skip("symlink creation not permitted")
    with pytest.raises(AdapterError) as exc:
        reject_symlink_escape(link, root=workspace)
    assert exc.value.code == "malformed_evidence"
    assert (exc.value.details or {}).get("kind") == "symlink_escape"


def test_env_poisoning_stripped() -> None:
    poisoned = {
        "PATH": os.environ.get("PATH", ""),
        "HTTP_PROXY": "http://evil.example",
        "HTTPS_PROXY": "http://evil.example",
        "GIT_CONFIG_GLOBAL": "/tmp/evil.gitconfig",
        "EVIL_INJECT": "1",
        "MATHEVIDENCE_OFFLINE": "1",
    }
    filtered = filter_environ(poisoned)
    assert "HTTP_PROXY" not in filtered
    assert "HTTPS_PROXY" not in filtered
    assert "GIT_CONFIG_GLOBAL" not in filtered
    assert "EVIL_INJECT" not in filtered
    assert filtered.get("MATHEVIDENCE_OFFLINE") == "1"


def test_unsafe_module_name_rejected() -> None:
    request = {
        "schemaVersion": "0.1.0",
        "capability": "algebra.ideal_membership_witness",
        "capabilityVersion": "0.1.0",
        "target": _poly(2, 1, [1, 1]),
        "generators": [_poly(2, 1, [1, 0]), _poly(2, 1, [0, 1])],
        "requestedClaim": "witness",
        "requestDigest": "sha256:" + ("12" * 32),
    }
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": request["capability"],
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [_poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    with pytest.raises(ValueError):
        generate_module(
            capability_id="algebra.ideal_membership_witness",
            request=request,
            certificate=certificate,
            candidate_bundle_digest="sha256:" + ("3" * 64),
            module_name="MathEvidence.Generated.Replay../Escape",
            declaration_name="ok",
        )
