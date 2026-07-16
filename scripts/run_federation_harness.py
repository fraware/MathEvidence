#!/usr/bin/env python3
"""Federation emit/consume harness (fixture_only until agreements).

Strengthens live-pattern coverage (digest pairing, role coverage, schema) while
remaining honest that external peers are not live without maintainer agreement.
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

from adapters.common.schema_validate import SchemaStore  # noqa: E402

EXAMPLES = ROOT / "evidence" / "federation" / "examples"
AGREEMENTS = ROOT / "docs" / "architecture" / "federation-agreements.md"

INTEGRATION_MODE = "fixture_only"


def _load_metadata() -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(EXAMPLES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "federationVersion" in data:
            out.append((path, data))
    return out


def _agreements_have_live() -> bool:
    if not AGREEMENTS.is_file():
        return False
    text = AGREEMENTS.read_text(encoding="utf-8")
    # Live requires at least one non-OPEN agreed/live_smoke row in the table.
    for line in text.splitlines():
        if "|" not in line or line.strip().startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0] in {"project_id", "Field"}:
            continue
        status = cells[2].replace("*", "").strip().lower()
        if status in {"agreed", "live_smoke"}:
            return True
    return False


def run_fixture_patterns(store: SchemaStore) -> list[str]:
    """Validate emit→consume patterns that mirror a future live path."""
    errors: list[str] = []
    metas = _load_metadata()
    if len(metas) < 2:
        return ["need ≥2 federation metadata examples"]

    emitters: dict[str, dict[str, Any]] = {}
    consumers: dict[str, dict[str, Any]] = {}
    for path, data in metas:
        try:
            store.validate("federation-metadata.schema.json", data)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.name}: schema {exc}")
            continue
        proj = data["project"]
        pid = proj["id"]
        role = proj["role"]
        if role in {"emitter", "bidirectional"}:
            emitters[pid] = data
        if role in {"consumer", "bidirectional"}:
            consumers[pid] = data

    # Required pairing: lean-smt emit digest consumed by cslib.
    lean_emit = emitters.get("lean-smt")
    cslib_cons = consumers.get("cslib")
    if not lean_emit or not cslib_cons:
        errors.append("missing lean-smt emitter or cslib consumer metadata")
    else:
        emit_digest = (lean_emit.get("provenance") or {}).get("requestDigest")
        cons_digest = (cslib_cons.get("provenance") or {}).get("requestDigest")
        emit_payload = lean_emit.get("payloadDigest")
        cons_payload = cslib_cons.get("payloadDigest")
        if not emit_digest or emit_digest != cons_digest:
            errors.append(
                "emit→consume requestDigest mismatch "
                f"(lean-smt={emit_digest!r}, cslib={cons_digest!r})"
            )
        if not emit_payload or emit_payload != cons_payload:
            errors.append(
                "emit→consume payloadDigest mismatch "
                f"(lean-smt={emit_payload!r}, cslib={cons_payload!r})"
            )
        # Authority must stay external for federated SMT.
        for label, blob in (("lean-smt", lean_emit), ("cslib", cslib_cons)):
            auth = blob.get("authority") or {}
            if auth.get("checkerOwner") != "external":
                errors.append(f"{label}: authority.checkerOwner must be external")
            role = auth.get("mathEvidenceRole")
            if role not in {"metadata_interop", "consumer"}:
                errors.append(f"{label}: unexpected mathEvidenceRole {role!r}")

    print(
        f"federation-harness mode={INTEGRATION_MODE} "
        f"emitters={sorted(emitters)} consumers={sorted(consumers)}"
    )
    return errors


def run_live_check() -> list[str]:
    """Fail closed: live opt-in requires recorded agreements (never invent)."""
    errors: list[str] = []
    if os.environ.get("MATHEVIDENCE_FEDERATION_LIVE", "").strip() != "1":
        errors.append(
            "live check requires MATHEVIDENCE_FEDERATION_LIVE=1 "
            "(and maintainer agreements)"
        )
        return errors
    if not _agreements_have_live():
        errors.append(
            "no agreed/live_smoke rows in docs/architecture/federation-agreements.md; "
            "keeping fixture_only (do not invent agreements)"
        )
    else:
        print(
            "federation-harness live-check: agreements present; "
            "external process adapters still required for true live emit/consume"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-check",
        action="store_true",
        help="Opt-in live gate (fails closed without agreements)",
    )
    args = parser.parse_args()

    if not EXAMPLES.is_dir():
        print("evidence/federation/examples missing", file=sys.stderr)
        return 1

    store = SchemaStore()
    errors = run_fixture_patterns(store)
    if args.live_check:
        errors.extend(run_live_check())

    if errors:
        for e in errors:
            print(f"FAIL {e}", file=sys.stderr)
        return 1

    print(
        "federation-harness ok "
        f"(integrationMode={INTEGRATION_MODE}; "
        "upgrade path: evidence/federation/examples/UPGRADE_PATH.md)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
