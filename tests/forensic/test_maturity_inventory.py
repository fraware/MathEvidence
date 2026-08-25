"""SPEC-00 maturity inventory policy and STATUS.md drift tests."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

_CR_ELIGIBLE = frozenset(
    {
        "algebra.ideal_membership_witness",
        "algebra.rational_equality",
        "algebra.linear_algebra",
        "logic.finite_counterexample",
        "algebra.formal_rational_calculus",
        "analysis.analytic_calculus",
    }
)


def _mod():
    path = ROOT / "scripts" / "validate_maturity_inventory.py"
    spec = importlib.util.spec_from_file_location("validate_maturity_inventory", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_inventory_and_status_pass() -> None:
    assert _mod().main() == 0


def test_catalog_coverage_matches_disk() -> None:
    mod = _mod()
    inventory = mod.load_inventory()
    catalog_ids = mod.catalog_capability_ids()
    assert not mod.validate_inventory_document(inventory, catalog_ids=catalog_ids)
    inv_ids = [entry["id"] for entry in inventory["capabilities"]]
    assert set(inv_ids) == set(catalog_ids)
    eligible = sorted(
        entry["id"] for entry in inventory["capabilities"] if entry["cr_eligible"]
    )
    assert eligible == sorted(_CR_ELIGIBLE)
    for entry in inventory["capabilities"]:
        if entry["id"] not in _CR_ELIGIBLE:
            assert entry["cr_eligible"] is False


def test_cr_eligible_without_exact_binding_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    target = next(
        entry for entry in inventory["capabilities"] if entry["id"] == "logic.smt"
    )
    target["cr_eligible"] = True
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("cr_eligible=true" in message for message in errors)


def test_exact_binding_without_generator_metadata_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    target = next(
        entry
        for entry in inventory["capabilities"]
        if entry["id"] == "algebra.ideal_membership_witness"
    )
    target["exactBinding"] = {"supported": True}
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("exactBinding fields" in message for message in errors)


def test_status_cr_eligible_true_is_rejected_when_registry_denies() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    for entry in inventory["capabilities"]:
        entry["cr_eligible"] = False
    poisoned = Path(mod.STATUS_PATH).read_text(encoding="utf-8") + "\ncr_eligible: true\n"
    errors = mod.validate_status_docs(poisoned, inventory)
    assert any("cr_eligible/crEligible=true" in message for message in errors)


def test_status_table_drift_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    # Drift a currently eligible row so the committed STATUS table disagrees.
    target = next(
        entry
        for entry in inventory["capabilities"]
        if entry["id"] == "algebra.formal_rational_calculus"
    )
    target["cr_eligible"] = False
    status = Path(mod.STATUS_PATH).read_text(encoding="utf-8")
    errors = mod.validate_status_docs(status, inventory)
    assert any("disagrees with inventory" in message for message in errors)


def test_duplicate_capability_version_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    inventory["capabilities"].append(copy.deepcopy(inventory["capabilities"][0]))
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("duplicate" in message for message in errors)


def test_missing_catalog_capability_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    inventory["capabilities"] = [
        entry for entry in inventory["capabilities"] if entry["id"] != "logic.smt"
    ]
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("missing catalog capabilities" in message for message in errors)


def test_inventory_cr_eligible_must_match_capability_json() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    target = next(
        entry
        for entry in inventory["capabilities"]
        if entry["id"] == "algebra.ideal_membership_witness"
    )
    target["cr_eligible"] = False
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("assurancePolicy.certification.crEligible" in message for message in errors)


def test_federated_cr_eligible_is_rejected() -> None:
    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    target = next(entry for entry in inventory["capabilities"] if entry["id"] == "logic.sat_unsat")
    target["cr_eligible"] = True
    target["exact_candidate_binding_exists"] = True
    target["exactBinding"] = {
        "supported": True,
        "generatorId": "forbidden",
        "generatorVersion": "0.1.0",
        "grammarVersion": "0.1.0",
        "generatorPath": "scripts/generate_exact_ideal_replay_module.py",
        "verifier": "mathevidence-declaration-identity",
    }
    errors = mod.validate_inventory_document(inventory, catalog_ids=mod.catalog_capability_ids())
    assert any("federated" in message for message in errors)


def test_schema_rejects_unknown_field() -> None:
    from adapters.common.errors import AdapterError
    from adapters.common.schema_validate import SchemaStore

    mod = _mod()
    inventory = copy.deepcopy(mod.load_inventory())
    inventory["unexpected"] = True
    with pytest.raises(AdapterError):
        SchemaStore().validate("maturity-inventory.schema.json", inventory)
