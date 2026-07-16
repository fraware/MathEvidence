#!/usr/bin/env python3
"""Validate committed JSON Schema files under schemas/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    if not SCHEMAS.is_dir():
        print("schemas/ missing", file=sys.stderr)
        return 1
    files = sorted(SCHEMAS.glob("*.schema.json"))
    if not files:
        print("no schema files found", file=sys.stderr)
        return 1
    errors = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"{path.name}: invalid JSON: {exc}", file=sys.stderr)
            errors += 1
            continue
        if not isinstance(data, dict) or "$schema" not in data:
            print(f"{path.name}: expected JSON Schema object with $schema", file=sys.stderr)
            errors += 1
            continue
        print(f"ok {path.name}")

    # Smoke-load SchemaStore (resolves $ref graph)
    try:
        from adapters.common.schema_validate import SchemaStore

        store = SchemaStore()
        for name in (
            "rational-equality-request.schema.json",
            "rational-equality-certificate.schema.json",
            "evidence-bundle.schema.json",
            "capability.schema.json",
            "backend.schema.json",
            "matrix-expr.schema.json",
            "linear-algebra-request.schema.json",
            "linear-algebra-certificate.schema.json",
            "finite-predicate.schema.json",
            "finite-counterexample-request.schema.json",
            "finite-counterexample-certificate.schema.json",
            "calculus-expr.schema.json",
            "symbolic-calculus-request.schema.json",
            "symbolic-calculus-certificate.schema.json",
            "condition-lattice.schema.json",
            "federation-metadata.schema.json",
            "federation-opaque-ir.schema.json",
            "federation-request.schema.json",
            "federation-certificate.schema.json",
            "trace-item.schema.json",
            "proof-plan.schema.json",
            "algorithm-contract.schema.json",
        ):
            store.validator(name)
        print("ok schema $ref registry")

        agent_store = SchemaStore(ROOT / "agent" / "api" / "schemas")
        for name in (
            "agent-result.schema.json",
            "list-capabilities.input.schema.json",
            "list-capabilities.output.schema.json",
            "check-support.input.schema.json",
            "compute-evidence.input.schema.json",
            "open-bundle.input.schema.json",
            "replay-bundle.input.schema.json",
            "hypothesis.input.schema.json",
        ):
            agent_store.validator(name)
        print("ok agent schema $ref registry")

        foundry_store = SchemaStore(ROOT / "foundry" / "schema")
        for name in (
            "training-episode.schema.json",
            "corpus-episode.schema.json",
            "corpus-release.schema.json",
        ):
            foundry_store.validator(name)
        print("ok foundry schema registry")
    except Exception as exc:  # noqa: BLE001
        print(f"schema store failed: {exc}", file=sys.stderr)
        errors += 1

    if errors:
        return 1
    print(f"schema-validate ok ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
