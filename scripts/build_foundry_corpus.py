#!/usr/bin/env python3
"""Build the Foundry public certified tool-use corpus (never on acceptance path)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from foundry.pipelines.build_corpus import build_corpus  # noqa: E402
from foundry.pipelines.common import DEFAULT_CORPUS_DIR  # noqa: E402

DATASHEET = """# Foundry Corpus Datasheet — v0.1 (sample)

## Motivation

Provide a public, provenance-tracked corpus of verification-aware tool-use
episodes for mathematical AI evaluation and diagnosis.

## Composition

Episodes are built from:

- committed offline evidence under `evidence/examples/`;
- optional Foundry capture-hook records under `foundry/episodes/`;
- labeled synthetic negatives for tool-selection failure modes.

## Hard invariant

`acceptanceInfluence` is always `false`. This corpus MUST NEVER influence Lean
theorem acceptance, checker results, or `ResultStatus`.

## Quality tiers

| Tier | Meaning |
| --- | --- |
| Q0_raw | unreviewed |
| Q1_schema_valid | schema-valid / metadata complete |
| Q2_formally_verified | replayable committed evidence |
| Q3_semantically_reviewed | human semantic review (none auto-assigned) |
| Q4_library_grade | library-integrated (none auto-assigned) |

## Contamination controls

- Immutable `train` / `eval` / `held_out` splits in `splits.json`.
- Content digests for duplicate detection.
- Synthetic negatives labeled and excluded from eval contamination.
- Flags for results already present in public libraries (default false for sample).

## Licensing

Apache-2.0 for MathEvidence-authored sample content. Solver artifact
redistribution rights must be reviewed before including proprietary backends'
raw outputs in future releases.

## Intended uses

- Verification-aware tool-selection training and evaluation.
- Failure diagnosis (negative episodes).
- System benchmarking (not capability promotion alone).

## Out of scope / known limitations

- Not a claim of live frontier acceleration.
- Sample is small and algebra/calculus-skewed.
- Q3/Q4 require human review queues not closed by this release.

## Maintenance

See `docs/foundry/maintenance-ownership.md`.
"""


def ensure_datasheet(out_dir: Path) -> None:
    path = out_dir / "DATASHEET.md"
    if not path.is_file():
        path.write_text(DATASHEET, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help="Corpus output directory",
    )
    parser.add_argument(
        "--no-captures",
        action="store_true",
        help="Skip foundry/episodes capture promotion",
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Skip synthetic negative episodes",
    )
    args = parser.parse_args()

    result = build_corpus(
        out_dir=args.out,
        include_captures=not args.no_captures,
        include_synthetic_negatives=not args.no_synthetic,
        repo_root=ROOT,
    )
    ensure_datasheet(args.out)
    # LICENSE pointer for the sample slice
    license_note = args.out / "LICENSE.txt"
    if not license_note.is_file():
        license_note.write_text(
            "Apache-2.0 — see repository LICENSE.\n"
            "Corpus episodes have acceptanceInfluence=false and never feed theorem acceptance.\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2))
    print(f"foundry corpus ok → {result['outDir']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
