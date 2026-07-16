"""CLI: python -m agent.sdk …"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from agent.sdk import (  # noqa: E402
    AgentClient,
    check_support_local,
    list_capabilities_local,
    open_bundle_local,
    replay_bundle_local,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MathEvidence Agent SDK CLI")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Call in-process handlers (no HTTP server)",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8787")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")
    sub.add_parser("operations")
    p_caps = sub.add_parser("capabilities")
    p_caps.add_argument("--status")
    p_caps.add_argument("--domain")

    p_support = sub.add_parser("check-support")
    p_support.add_argument("--capability", required=True)
    p_support.add_argument("--backend")
    p_support.add_argument("--claim")

    p_open = sub.add_parser("open-bundle")
    p_open.add_argument("path")

    p_replay = sub.add_parser("replay-bundle")
    p_replay.add_argument("path")

    args = parser.parse_args(argv)
    client = AgentClient(base_url=args.base_url)

    if args.cmd == "health":
        if args.local:
            from agent.api.service import health

            out = health()
        else:
            out = client.health()
    elif args.cmd == "operations":
        if args.local:
            from agent.api.service import op_list_operations

            out = op_list_operations()
        else:
            out = client.list_operations()
    elif args.cmd == "capabilities":
        if args.local:
            out = list_capabilities_local(status=args.status, domain=args.domain)
        else:
            out = client.list_capabilities(status=args.status, domain=args.domain)
    elif args.cmd == "check-support":
        body = {"capability": args.capability}
        if args.backend:
            body["backend"] = args.backend
        if args.claim:
            body["requestedClaim"] = args.claim
        out = check_support_local(body) if args.local else client.check_support(
            capability=args.capability,
            backend=args.backend,
            requested_claim=args.claim,
        )
    elif args.cmd == "open-bundle":
        out = open_bundle_local(args.path) if args.local else client.open_bundle(args.path)
    elif args.cmd == "replay-bundle":
        out = (
            replay_bundle_local(args.path)
            if args.local
            else client.replay_bundle(args.path)
        )
    else:
        parser.error(f"unknown command {args.cmd}")
        return 2

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
