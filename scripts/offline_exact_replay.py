#!/usr/bin/env python3
"""Offline exact-replay driver.

Builds or replays an exact-certification release bundle with network disabled.
Default replay verifies integrity + regenerability (``theorem_pending``).
Pass ``--require-lean`` / set ``MATHEVIDENCE_OFFLINE_LEAN=1`` to attempt Lake
declaration-identity inspect (``theorem_proved``). Missing dependencies are
setup/integrity failures, not theorem failures.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.exact_replay.offline_bundle import (  # noqa: E402
    DRIVER_VERSION,
    both_modes_agree,
    build_offline_exact_bundle,
    mutate_bundle_for_tamper,
    replay_offline_exact_bundle,
)
from adapters.common.exact_replay.plugins.ideal_membership import (  # noqa: E402
    CAPABILITY as IDEAL_CAPABILITY,
)


def _ideal_reference_payload() -> tuple[dict[str, Any], dict[str, Any], str]:
    """Canonical exact ideal membership candidate (xy ∈ ⟨x, y⟩)."""
    from adapters.common.canonical import bind_request_digest

    def poly(m: int, coefficient: int, exponents: list[int]) -> dict[str, Any]:
        return {
            "varCount": m,
            "terms": [{"coefficient": coefficient, "exponents": exponents}],
        }

    request = bind_request_digest(
        {
            "schemaVersion": "0.1.0",
            "capability": IDEAL_CAPABILITY,
            "capabilityVersion": "0.1.0",
            "target": poly(2, 1, [1, 1]),
            "generators": [poly(2, 1, [1, 0]), poly(2, 1, [0, 1])],
            "requestedClaim": "witness",
        }
    )
    certificate = {
        "schemaVersion": "0.1.0",
        "capability": IDEAL_CAPABILITY,
        "capabilityVersion": "0.1.0",
        "requestDigest": request["requestDigest"],
        "target": request["target"],
        "generators": request["generators"],
        "multipliers": [poly(2, 1, [0, 1]), {"varCount": 2, "terms": []}],
        "claimClass": "witness",
    }
    candidate_digest = "sha256:" + ("3" * 64)
    return request, certificate, candidate_digest


def cmd_build(args: argparse.Namespace) -> int:
    os.environ.setdefault("MATHEVIDENCE_OFFLINE", "1")
    request, certificate, cand = _ideal_reference_payload()
    out = Path(args.out)
    result = build_offline_exact_bundle(
        out,
        capability_id=IDEAL_CAPABILITY,
        request=request,
        certificate=certificate,
        candidate_bundle_digest=cand,
        module_name="MathEvidence.Generated.Replay.exact_offline_xy",
        declaration_name="exact_offline_xy",
        repo_root=ROOT,
    )
    print(json.dumps({"status": "ok", "driverVersion": DRIVER_VERSION, **result}, indent=2))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    os.environ.setdefault("MATHEVIDENCE_OFFLINE", "1")
    if args.both_modes:
        a, b = both_modes_agree(
            args.bundle,
            repo_root=ROOT,
            check_live_toolchain=not args.skip_live_toolchain,
            require_lean=args.require_lean,
        )
        payload = {
            "regenerate-and-verify": a.__dict__,
            "artifact-replay": b.__dict__,
            "modesAgree": a.ok == b.ok
            and a.logical_outcome == b.logical_outcome
            and a.generated_source_hash == b.generated_source_hash,
        }
        print(json.dumps(payload, indent=2))
        return 0 if a.ok and b.ok and payload["modesAgree"] else 1
    result = replay_offline_exact_bundle(
        args.bundle,
        mode=args.mode,
        repo_root=ROOT,
        check_live_toolchain=not args.skip_live_toolchain,
        require_lean=args.require_lean,
    )
    print(json.dumps(result.__dict__, indent=2))
    return 0 if result.ok else 1


def cmd_tamper_selftest(args: argparse.Namespace) -> int:
    """Build a fresh bundle, apply each tamper case, assert failure."""
    import tempfile

    os.environ.setdefault("MATHEVIDENCE_OFFLINE", "1")
    cases = [
        "candidate",
        "generated_source",
        "artifact_delete",
        "artifact_mutate",
        "manifest",
        "generator_version",
        "declaration_identity",
        "toolchain_lock",
        "capability_id",
        "capability_version",
    ]
    request, certificate, cand = _ideal_reference_payload()
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "good"
        build_offline_exact_bundle(
            base,
            capability_id=IDEAL_CAPABILITY,
            request=request,
            certificate=certificate,
            candidate_bundle_digest=cand,
            module_name="MathEvidence.Generated.Replay.exact_offline_xy",
            declaration_name="exact_offline_xy",
            repo_root=ROOT,
        )
        good = replay_offline_exact_bundle(
            base, repo_root=ROOT, check_live_toolchain=not args.skip_live_toolchain
        )
        if not good.ok:
            print(json.dumps({"status": "fail", "reason": "clean bundle failed", **good.__dict__}))
            return 1
        for case in cases:
            clone = Path(tmp) / f"tamper_{case}"
            # Shallow file copy.
            clone.mkdir()
            for src in base.iterdir():
                if src.is_file():
                    (clone / src.name).write_bytes(src.read_bytes())
            mutate_bundle_for_tamper(clone, case=case)
            bad = replay_offline_exact_bundle(
                clone,
                repo_root=ROOT,
                check_live_toolchain=not args.skip_live_toolchain,
            )
            if bad.ok:
                failures.append(case)
            print(
                json.dumps(
                    {
                        "case": case,
                        "ok": bad.ok,
                        "logical_outcome": bad.logical_outcome,
                        "error_kind": bad.error_kind,
                    }
                )
            )
    status = "ok" if not failures else "fail"
    print(json.dumps({"status": status, "failures": failures, "cases": cases}))
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build ideal-membership reference offline bundle")
    p_build.add_argument("--out", required=True, help="Output bundle directory")
    p_build.set_defaults(func=cmd_build)

    p_replay = sub.add_parser("replay", help="Replay an offline exact bundle")
    p_replay.add_argument("--bundle", required=True)
    p_replay.add_argument(
        "--mode",
        choices=["regenerate-and-verify", "artifact-replay"],
        default="regenerate-and-verify",
    )
    p_replay.add_argument("--both-modes", action="store_true")
    p_replay.add_argument(
        "--skip-live-toolchain",
        action="store_true",
        help="Skip live lake-manifest lock compare (structure-only)",
    )
    p_replay.add_argument(
        "--require-lean",
        action="store_true",
        help="Attempt Lake declaration-identity inspect (theorem_proved)",
    )
    p_replay.set_defaults(func=cmd_replay)

    p_tamper = sub.add_parser("tamper-selftest", help="Run offline-bundle tamper matrix")
    p_tamper.add_argument("--skip-live-toolchain", action="store_true")
    p_tamper.set_defaults(func=cmd_tamper_selftest)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
