#!/usr/bin/env python3
"""Validate the SPEC-00 assurance maturity inventory against catalog and docs.

Fails when:

- catalog capabilities are missing from the inventory, or inventory has extras;
- duplicate capability/version keys appear;
- ``cr_eligible=true`` without exact-binding generator/verifier metadata;
- exact binding is claimed without generator metadata / generator path;
- federated capabilities are marked CR-eligible;
- ``docs/STATUS.md`` claims CR eligibility the inventory denies, or its
  machine-readable maturity table drifts from the inventory.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.common.schema_validate import SchemaStore  # noqa: E402

INVENTORY_PATH = ROOT / "registry" / "maturity-inventory.json"
CATALOG_PATH = ROOT / "registry" / "catalog.json"
CAP_DIR = ROOT / "registry" / "capabilities"
STATUS_PATH = ROOT / "docs" / "STATUS.md"
SCHEMA_NAME = "maturity-inventory.schema.json"

MATURITY_BOOLS = (
    "adapter_exists",
    "checker_exists",
    "lean_soundness_exists",
    "bridge_replay_exists",
    "exact_candidate_binding_exists",
    "offline_replay_exists",
    "cr_eligible",
)

TABLE_BEGIN = "<!-- maturity-inventory-table:begin -->"
TABLE_END = "<!-- maturity-inventory-table:end -->"
ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|" + r"\s*(true|false)\s*\|" * 7 + r"\s*$")
CR_ELIGIBLE_TRUE_RE = re.compile(r"(?i)(?:cr_eligible|crEligible)\s*[:=]\s*true\b")
TABLE_HEADER = (
    "| Capability | adapter_exists | checker_exists | lean_soundness_exists | "
    "bridge_replay_exists | exact_candidate_binding_exists | "
    "offline_replay_exists | cr_eligible |"
)

_EXACT_META_KEYS = (
    "generatorId",
    "generatorVersion",
    "grammarVersion",
    "generatorPath",
    "verifier",
)


def load_inventory(path: Path = INVENTORY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_capability_ids(catalog_path: Path = CATALOG_PATH) -> list[str]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    ids: list[str] = []
    for rel in catalog.get("capabilities") or []:
        cap_path = ROOT / "registry" / str(rel)
        data = json.loads(cap_path.read_text(encoding="utf-8"))
        ids.append(str(data["id"]))
    return ids


def _binding(entry: dict[str, Any]) -> dict[str, Any]:
    value = entry.get("exactBinding")
    return value if isinstance(value, dict) else {}


def validate_entry_policy(entry: dict[str, Any], *, repo_root: Path = ROOT) -> list[str]:
    """Return policy errors for one inventory row (schema is checked separately)."""
    errors: list[str] = []
    cap_id = str(entry.get("id") or "<missing-id>")
    binding = _binding(entry)
    supported = binding.get("supported") is True
    exact_exists = entry.get("exact_candidate_binding_exists") is True
    cr_eligible = entry.get("cr_eligible") is True

    if exact_exists != supported:
        errors.append(
            f"{cap_id}: exact_candidate_binding_exists={exact_exists} disagrees "
            f"with exactBinding.supported={supported}"
        )

    if supported or cr_eligible or exact_exists:
        missing = [key for key in _EXACT_META_KEYS if not binding.get(key)]
        if missing:
            errors.append(
                f"{cap_id}: exact binding / cr_eligible requires exactBinding fields {missing}"
            )
        gen_path = binding.get("generatorPath")
        if isinstance(gen_path, str) and gen_path:
            target = repo_root / gen_path
            if not target.is_file():
                errors.append(f"{cap_id}: exactBinding.generatorPath missing: {gen_path}")

    if cr_eligible and not exact_exists:
        errors.append(f"{cap_id}: cr_eligible=true requires exact_candidate_binding_exists")

    cap_file = CAP_DIR / f"{cap_id}.json"
    if cap_file.is_file():
        cap = json.loads(cap_file.read_text(encoding="utf-8"))
        if cap.get("ownership") == "federated" and cr_eligible:
            errors.append(f"{cap_id}: federated capabilities cannot be cr_eligible")
        inv_ver = str(entry.get("version") or "")
        cap_ver = str(cap.get("version") or "")
        if inv_ver and cap_ver and inv_ver != cap_ver:
            errors.append(f"{cap_id}: inventory version {inv_ver} != capability registry {cap_ver}")
        policy = cap.get("assurancePolicy") if isinstance(cap.get("assurancePolicy"), dict) else {}
        cert = policy.get("certification") if isinstance(policy.get("certification"), dict) else {}
        live_cr = cert.get("crEligible") is True
        if live_cr != cr_eligible:
            errors.append(
                f"{cap_id}: inventory cr_eligible={cr_eligible} disagrees with "
                f"capability assurancePolicy.certification.crEligible={live_cr}"
            )
        live_exact = False
        binding = policy.get("exactBinding") if isinstance(policy.get("exactBinding"), dict) else {}
        live_exact = binding.get("supported") is True
        inv_exact = entry.get("exact_candidate_binding_exists") is True
        if live_exact != inv_exact:
            errors.append(
                f"{cap_id}: inventory exact_candidate_binding_exists={inv_exact} disagrees "
                f"with capability exactBinding.supported={live_exact}"
            )
    return errors


def validate_inventory_document(
    inventory: dict[str, Any],
    *,
    catalog_ids: list[str],
    repo_root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    caps = inventory.get("capabilities")
    if not isinstance(caps, list):
        return ["inventory capabilities must be an array"]

    seen: set[tuple[str, str]] = set()
    inventory_ids: list[str] = []
    for entry in caps:
        if not isinstance(entry, dict):
            errors.append("inventory capability entry must be an object")
            continue
        cap_id = str(entry.get("id") or "")
        version = str(entry.get("version") or "")
        key = (cap_id, version)
        if key in seen:
            errors.append(f"duplicate capability/version key: {cap_id}@{version}")
        seen.add(key)
        inventory_ids.append(cap_id)
        errors.extend(validate_entry_policy(entry, repo_root=repo_root))

    catalog_set = set(catalog_ids)
    inv_set = set(inventory_ids)
    missing = sorted(catalog_set - inv_set)
    extra = sorted(inv_set - catalog_set)
    if missing:
        errors.append(f"inventory missing catalog capabilities: {missing}")
    if extra:
        errors.append(f"inventory has capabilities not in catalog: {extra}")
    if len(inventory_ids) != len(set(inventory_ids)):
        errors.append("inventory contains duplicate capability ids")
    return errors


def _bool_cell(value: bool) -> str:
    return "true" if value else "false"


def format_status_table(inventory: dict[str, Any]) -> str:
    lines = [
        TABLE_BEGIN,
        TABLE_HEADER,
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in inventory.get("capabilities") or []:
        if not isinstance(entry, dict):
            continue
        cells = " | ".join(_bool_cell(bool(entry[name])) for name in MATURITY_BOOLS)
        lines.append(f"| `{entry['id']}` | {cells} |")
    lines.append(TABLE_END)
    return "\n".join(lines)


def parse_status_table(status_text: str) -> dict[str, dict[str, bool]]:
    if TABLE_BEGIN not in status_text or TABLE_END not in status_text:
        raise ValueError(
            "docs/STATUS.md must contain a maturity table delimited by "
            f"{TABLE_BEGIN} ... {TABLE_END}"
        )
    block = status_text.split(TABLE_BEGIN, 1)[1].split(TABLE_END, 1)[0]
    rows: dict[str, dict[str, bool]] = {}
    for raw in block.splitlines():
        line = raw.strip()
        match = ROW_RE.match(line)
        if match is None:
            continue
        cap_id = match.group(1)
        values = match.groups()[1:]
        rows[cap_id] = {
            name: value == "true" for name, value in zip(MATURITY_BOOLS, values, strict=True)
        }
    if not rows:
        raise ValueError("docs/STATUS.md maturity table contains no capability rows")
    return rows


def validate_status_docs(
    status_text: str,
    inventory: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    cr_true_ids = {
        str(entry["id"])
        for entry in inventory.get("capabilities") or []
        if isinstance(entry, dict) and entry.get("cr_eligible") is True
    }
    if CR_ELIGIBLE_TRUE_RE.search(status_text) and not cr_true_ids:
        errors.append(
            "docs/STATUS.md claims cr_eligible/crEligible=true but the inventory "
            "denies CR eligibility for every capability"
        )

    try:
        table = parse_status_table(status_text)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    expected = {
        str(entry["id"]): {name: bool(entry[name]) for name in MATURITY_BOOLS}
        for entry in inventory.get("capabilities") or []
        if isinstance(entry, dict)
    }
    if set(table) != set(expected):
        errors.append(
            "docs/STATUS.md maturity table capability set disagrees with inventory: "
            f"docs={sorted(table)} inventory={sorted(expected)}"
        )
    for cap_id, expected_row in expected.items():
        got = table.get(cap_id)
        if got is None:
            continue
        if got != expected_row:
            errors.append(
                f"docs/STATUS.md maturity row for {cap_id} disagrees with inventory: "
                f"docs={got} inventory={expected_row}"
            )
        if got.get("cr_eligible") is True and cap_id not in cr_true_ids:
            errors.append(
                f"docs/STATUS.md claims cr_eligible=true for {cap_id} but inventory denies it"
            )
    return errors


def main() -> int:
    if not INVENTORY_PATH.is_file():
        print(f"FAIL missing {INVENTORY_PATH.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not STATUS_PATH.is_file():
        print("FAIL missing docs/STATUS.md", file=sys.stderr)
        return 1

    store = SchemaStore()
    errors = 0
    try:
        inventory = load_inventory()
        store.validate(SCHEMA_NAME, inventory)
        print(f"ok schema {INVENTORY_PATH.name}")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {INVENTORY_PATH.name}: {exc}", file=sys.stderr)
        return 1

    try:
        catalog_ids = catalog_capability_ids()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL catalog.json: {exc}", file=sys.stderr)
        return 1

    for message in validate_inventory_document(inventory, catalog_ids=catalog_ids):
        print(f"FAIL inventory: {message}", file=sys.stderr)
        errors += 1

    status_text = STATUS_PATH.read_text(encoding="utf-8")
    for message in validate_status_docs(status_text, inventory):
        print(f"FAIL STATUS.md: {message}", file=sys.stderr)
        errors += 1

    if errors:
        return 1
    n = len(inventory.get("capabilities") or [])
    print(f"maturity-inventory ok ({n} capabilities; all live CR claims match registry)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
