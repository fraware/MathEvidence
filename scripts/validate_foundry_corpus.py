#!/usr/bin/env python3
"""Validate Foundry corpus release + episode schemas and hard invariants."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from foundry.pipelines.common import DEFAULT_CORPUS_DIR  # noqa: E402
from foundry.pipelines.validate import (  # noqa: E402
    schema_store,
    validate_corpus_episode,
    validate_corpus_release,
)


def main() -> int:
    corpus = DEFAULT_CORPUS_DIR
    manifest_path = corpus / "manifest.json"
    if not manifest_path.is_file():
        print(
            f"missing {manifest_path}; run: python scripts/build_foundry_corpus.py",
            file=sys.stderr,
        )
        return 1

    store = schema_store()
    # Capture + corpus schemas present
    for name in (
        "training-episode.schema.json",
        "corpus-episode.schema.json",
        "corpus-release.schema.json",
    ):
        store.validator(name)
        print(f"ok schema {name}")

    release = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_corpus_release(release, store)
    print(f"ok release {release.get('releaseId')}")

    if release.get("acceptanceInfluence") is not False:
        print("FAIL: release acceptanceInfluence must be false", file=sys.stderr)
        return 1
    if release.get("splits", {}).get("immutable") is not True:
        print("FAIL: splits must be immutable", file=sys.stderr)
        return 1

    errors = 0
    for rel in release.get("episodes") or []:
        path = corpus / rel
        ep = json.loads(path.read_text(encoding="utf-8"))
        try:
            validate_corpus_episode(ep, store)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {rel}: {exc}", file=sys.stderr)
            errors += 1
            continue
        if ep.get("acceptanceInfluence") is not False:
            print(f"FAIL {rel}: acceptanceInfluence", file=sys.stderr)
            errors += 1

    splits_path = corpus / "splits.json"
    cont_path = corpus / "contamination.json"
    datasheet = corpus / "DATASHEET.md"
    for p in (splits_path, cont_path, datasheet):
        if not p.is_file():
            print(f"FAIL missing {p}", file=sys.stderr)
            errors += 1
        else:
            print(f"ok {p.name}")

    if errors:
        print(f"foundry-validate: {errors} failed", file=sys.stderr)
        return 1
    print(
        f"foundry-validate ok ({len(release.get('episodes') or [])} episodes, "
        f"tiers={release.get('tierComposition')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
