#!/usr/bin/env python3
"""Validate federation metadata examples and exit-gate coverage.

Honesty: examples are fixture_only. Live external emit/consume requires
maintainer agreements — see evidence/federation/examples/UPGRADE_PATH.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.schema_validate import SchemaStore  # noqa: E402

EXAMPLES = ROOT / "evidence" / "federation" / "examples"

# Exit gate (fixture coverage): ≥2 distinct external projects emit or consume
# shared metadata. This does NOT claim live maintainer integration.
REQUIRED_PROJECT_ROLES: dict[str, set[str]] = {
    "lean-smt": {"emitter"},
    "cslib": {"consumer"},
}

INTEGRATION_MODE = "fixture_only"


def main() -> int:
    if not EXAMPLES.is_dir():
        print("evidence/federation/examples missing", file=sys.stderr)
        return 1

    store = SchemaStore()
    errors = 0
    projects: dict[str, set[str]] = {}
    digests: dict[str, dict[str, str | None]] = {}

    meta_files = sorted(EXAMPLES.glob("*.json"))
    if len(meta_files) < 2:
        print("expected ≥2 federation example JSON files", file=sys.stderr)
        return 1

    for path in meta_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            if "federationVersion" in data:
                store.validate("federation-metadata.schema.json", data)
                proj = data["project"]
                projects.setdefault(proj["id"], set()).add(proj["role"])
                digests[proj["id"]] = {
                    "role": proj["role"],
                    "requestDigest": (data.get("provenance") or {}).get("requestDigest"),
                    "payloadDigest": data.get("payloadDigest"),
                }
                print(f"ok metadata {path.name} ({proj['id']}/{proj['role']})")
            elif data.get("schemaVersion") == "0.1.0" and "opaqueIr" in data:
                store.validate("federation-request.schema.json", data)
                print(f"ok request {path.name}")
            elif data.get("schemaVersion") == "0.1.0" and "federation" in data:
                store.validate("federation-certificate.schema.json", data)
                print(f"ok certificate {path.name}")
            else:
                raise ValueError("unrecognized federation example shape")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path.name}: {exc}", file=sys.stderr)
            errors += 1

    for pid, roles in REQUIRED_PROJECT_ROLES.items():
        have = projects.get(pid, set())
        if not roles.issubset(have):
            print(
                f"FAIL exit gate: project {pid!r} missing roles {roles - have}",
                file=sys.stderr,
            )
            errors += 1

    emitters = {p for p, roles in projects.items() if "emitter" in roles}
    consumers = {p for p, roles in projects.items() if "consumer" in roles}
    if len(emitters) < 1 or len(consumers) < 1:
        print(
            "FAIL exit gate: need ≥1 emitter and ≥1 consumer project",
            file=sys.stderr,
        )
        errors += 1
    if len(projects) < 2:
        print(
            f"FAIL exit gate: need ≥2 distinct projects, found {sorted(projects)}",
            file=sys.stderr,
        )
        errors += 1

    # Live-pattern pairing on fixtures (emit digest consumed by peer).
    lean = digests.get("lean-smt") or {}
    cslib = digests.get("cslib") or {}
    if lean and cslib:
        if lean.get("requestDigest") != cslib.get("requestDigest"):
            print(
                "FAIL emit→consume requestDigest mismatch lean-smt↔cslib",
                file=sys.stderr,
            )
            errors += 1
        if lean.get("payloadDigest") != cslib.get("payloadDigest"):
            print(
                "FAIL emit→consume payloadDigest mismatch lean-smt↔cslib",
                file=sys.stderr,
            )
            errors += 1

    upgrade = EXAMPLES / "UPGRADE_PATH.md"
    if not upgrade.is_file():
        print(f"FAIL missing upgrade path doc: {upgrade}", file=sys.stderr)
        errors += 1

    if errors:
        return 1
    print(
        f"federation-validate ok "
        f"(integrationMode={INTEGRATION_MODE}; {len(meta_files)} files; "
        f"projects={sorted(projects)})"
    )
    print(
        "NOTE: fixture_only - live external emit/consume remains OPEN "
        "(see evidence/federation/examples/UPGRADE_PATH.md)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
