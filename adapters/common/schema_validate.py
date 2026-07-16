"""JSON Schema loading and validation with local $ref resolution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from adapters.common.errors import stable_error

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"


class SchemaStore:
    def __init__(self, schemas_dir: Path = SCHEMAS_DIR) -> None:
        self.schemas_dir = schemas_dir
        self._validators: dict[str, Draft202012Validator] = {}
        self._registry = self._build_registry()

    def _build_registry(self) -> Registry:
        registry: Registry = Registry()
        for path in sorted(self.schemas_dir.glob("*.schema.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            resource = Resource.from_contents(data, DRAFT202012)
            # Register under filename for relative $ref values used in schemas.
            registry = registry.with_resource(path.name, resource)
            # Also under a file:// URI so retrieval has a stable base.
            registry = registry.with_resource(path.resolve().as_uri(), resource)
            schema_id = data.get("$id")
            if isinstance(schema_id, str):
                registry = registry.with_resource(schema_id, resource)
        return registry

    def validator(self, schema_name: str) -> Draft202012Validator:
        if schema_name not in self._validators:
            # Retrieve from registry so $ref resolution uses the registered URI.
            resolved = self._registry.resolver().lookup(schema_name)
            self._validators[schema_name] = Draft202012Validator(
                resolved.contents,
                registry=self._registry,
            )
        return self._validators[schema_name]

    def validate(self, schema_name: str, instance: Any) -> None:
        validator = self.validator(schema_name)
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        if errors:
            err = errors[0]
            path = "/".join(str(p) for p in err.absolute_path)
            raise stable_error(
                "malformed_evidence",
                f"schema validation failed ({schema_name}): {err.message}",
                details={"path": path, "schema": schema_name},
            )


def load_default_schema_store() -> SchemaStore:
    return SchemaStore()
