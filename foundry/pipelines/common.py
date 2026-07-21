"""Shared constants and digests for Foundry pipelines."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CONTENT_DIGEST_ALG = "sha256"
REPO_ROOT = Path(__file__).resolve().parents[2]
FOUNDRY_ROOT = REPO_ROOT / "foundry"
SCHEMA_DIR = FOUNDRY_ROOT / "schema"
DEFAULT_CORPUS_DIR = FOUNDRY_ROOT / "corpus" / "v0.1"
EVIDENCE_EXAMPLES = REPO_ROOT / "evidence" / "examples"
CAPTURE_DIR = FOUNDRY_ROOT / "episodes"

# Capabilities known to the Agent / registry at corpus build time.
KNOWN_CAPABILITIES = [
    "algebra.rational_equality",
    "algebra.linear_algebra",
    "algebra.groebner_membership",
    "logic.finite_counterexample",
    "logic.sat_unsat",
    "logic.pseudo_boolean",
    "logic.smt",
    "algebra.formal_rational_calculus",
]

# Legacy path-suffix split seeds (source-family policy lives in split.py).
SPLIT_HELD_OUT_SUFFIXES = (
    "finite_counterexample_nat_eq0",
    "calculus_ode_y_eq_x",
)
SPLIT_EVAL_SUFFIXES = (
    "linear_algebra_inverse_2x2",
    "calculus_antiderivative_x2",
)


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def content_digest(obj: Any) -> str:
    digest = hashlib.sha256(canonical_json_bytes(obj)).hexdigest()
    return f"{CONTENT_DIGEST_ALG}:{digest}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
