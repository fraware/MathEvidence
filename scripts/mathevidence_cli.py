#!/usr/bin/env python3
"""Thin orchestration CLI: JSON-RPC/direct compute → EvidenceBundle write.

Does not implement the Lean tactic trust path (sibling owns Lean Core/IR/Checkers).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.bundle import write_bundle  # noqa: E402
from adapters.common.canonical import bind_request_digest  # noqa: E402
from adapters.common.discovery import discover  # noqa: E402
from adapters.common.limits import ResourceTracker, ResourceLimits  # noqa: E402
from adapters.common.schema_validate import SchemaStore  # noqa: E402


def _load_request(path: Path | None, *, stdin: bool) -> dict:
    if stdin:
        data = json.load(sys.stdin)
    else:
        assert path is not None
        data = json.loads(path.read_text(encoding="utf-8"))
    if "requestDigest" not in data or data.get("requestDigest") in ("", None):
        data = bind_request_digest(data)
    return data


def cmd_compute(args: argparse.Namespace) -> int:
    request = _load_request(Path(args.request) if args.request else None, stdin=args.stdin)
    schemas = SchemaStore()
    tracker = ResourceTracker(ResourceLimits.from_policy(request.get("resourcePolicy")))

    if args.backend == "sympy":
        from adapters.sympy.adapter import compute_rational_equality

        result = compute_rational_equality(request, tracker, schemas=schemas)
    elif args.backend == "mathematica":
        from adapters.mathematica.adapter import compute_rational_equality

        result = compute_rational_equality(request, tracker, schemas=schemas)
    else:
        print(f"unknown backend: {args.backend}", file=sys.stderr)
        return 2

    out = result.result
    if args.bundle_dir:
        write_bundle(
            Path(args.bundle_dir),
            request=request,
            candidate=out["candidate"],
            certificate=out["certificate"],
            result_status="computed",
            claim_class="candidate",
            schemas=schemas,
        )
        print(f"wrote bundle: {args.bundle_dir}")
    else:
        print(json.dumps(out, indent=2))
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    """Spawn/in-process discovery → optional bundle → emit certificate JSON."""
    request = _load_request(Path(args.request) if args.request else None, stdin=args.stdin)
    use_rpc = None
    if args.rpc:
        use_rpc = True
    elif args.direct:
        use_rpc = False
    result = discover(
        request,
        backend=args.backend,
        bundle_dir=Path(args.bundle_dir) if args.bundle_dir else None,
        use_rpc=use_rpc,
    )
    for w in result.warnings:
        print(f"warning: {w}", file=sys.stderr)
    if args.emit_certificate:
        # Single-line JSON for Lean / tooling consumers (last stdout line).
        print(json.dumps(result.certificate, ensure_ascii=False, separators=(",", ":")))
    elif result.bundle_dir is not None:
        print(f"wrote bundle: {result.bundle_dir}")
        print(f"via_rpc={result.via_rpc}")
    else:
        print(
            json.dumps(
                {
                    "backend": result.backend,
                    "viaRpc": result.via_rpc,
                    "certificate": result.certificate,
                    "candidate": result.candidate,
                },
                indent=2,
            )
        )
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    bound = bind_request_digest(request)
    print(bound["requestDigest"])
    if args.write:
        Path(args.request).write_text(
            json.dumps(bound, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="mathevidence-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_compute = sub.add_parser("compute", help="Run adapter compute and optional bundle write")
    p_compute.add_argument("--backend", choices=["sympy", "mathematica"], default="sympy")
    src = p_compute.add_mutually_exclusive_group(required=True)
    src.add_argument("--request", help="Path to request JSON")
    src.add_argument("--stdin", action="store_true", help="Read request JSON from stdin")
    p_compute.add_argument("--bundle-dir", help="Write EvidenceBundle directory")
    p_compute.set_defaults(func=cmd_compute)

    p_discover = sub.add_parser(
        "discover",
        help=(
            "Discovery orchestration (adapter → bundle); capability from request "
            "(SymPy: rational / LA / CEX / calculus); CI-safe when backends fixture"
        ),
    )
    p_discover.add_argument(
        "--backend", choices=["sympy", "mathematica", "sage"], default="sympy"
    )
    src_d = p_discover.add_mutually_exclusive_group(required=True)
    src_d.add_argument("--request", help="Path to request JSON")
    src_d.add_argument("--stdin", action="store_true", help="Read request JSON from stdin")
    p_discover.add_argument("--bundle-dir", help="Write EvidenceBundle directory")
    p_discover.add_argument(
        "--emit-certificate",
        action="store_true",
        help="Print certificate JSON on stdout (for Lean discovery)",
    )
    p_discover.add_argument(
        "--rpc",
        action="store_true",
        help="Force JSON-RPC subprocess path (also MATHEVIDENCE_DISCOVERY_RPC=1)",
    )
    p_discover.add_argument(
        "--direct",
        action="store_true",
        help="Force in-process compute (default when RPC unset)",
    )
    p_discover.set_defaults(func=cmd_discover)

    p_digest = sub.add_parser("digest", help="Compute requestDigest for a request JSON")
    p_digest.add_argument("--request", required=True)
    p_digest.add_argument("--write", action="store_true")
    p_digest.set_defaults(func=cmd_digest)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
