#!/usr/bin/env python3
"""Aggregate PROJECT_SPEC §19 instrumented metrics (+ Foundry engineering metrics)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.metrics import foundry_corpus_quality  # noqa: E402
from scripts.metrics import foundry_tool_selection  # noqa: E402
from scripts.metrics import open_replay_rate  # noqa: E402
from scripts.metrics import semantic_defect_rate  # noqa: E402
from scripts.metrics import track_contributions  # noqa: E402
from scripts.metrics import verified_coverage  # noqa: E402


def main() -> int:
    payload = {
        "spec": "PROJECT_SPEC §19 + Foundry engineering metrics",
        "verified_coverage": verified_coverage.measure(),
        "open_replay_rate": open_replay_rate.measure(),
        "semantic_defect_rate": semantic_defect_rate.measure(),
        "foundry_tool_selection": foundry_tool_selection.measure(),
        "foundry_corpus_quality": foundry_corpus_quality.measure(),
        "contributions": track_contributions.measure(),
        "human_research_open": [
            "live federation emit/consume (≥2 peers with maintainer agreement)",
            "frontier-grade trained selector (trivial bag-of-token lift measured; see just foundry-train-eval)",
            "frontier program materially accelerated",
            "maintenance funding secured",
            "field semantic defect rate (expert audit)",
            "capability status stable (governance; blocked on G1)",
        ],
    }
    print(json.dumps(payload, indent=2))
    # Informational aggregate; corpus quality hard-fails separately via just foundry-metrics
    vc = payload["verified_coverage"]["real_world_coverage_rate"]
    orr = payload["open_replay_rate"]["open_replay_rate"]
    print(
        f"section19: verified_coverage={vc:.1%} open_replay={orr:.1%} "
        f"(field semantic defect + research exits remain OPEN)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
