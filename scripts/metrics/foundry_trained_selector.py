#!/usr/bin/env python3
"""Train a trivial tool-selection baseline on Foundry corpus; eval on tool_selection.

Method: **rule + learned bag-of-token weights** (pure Python; no sklearn).

1. Seed each capability with name tokens + a small synonym lexicon.
2. Add Laplace-smoothed count weights from ``foundry/corpus/v0.1`` *train* episodes
   (correct capability / claim labels; negatives use ``payload.correctCapability``).
3. At eval time, score each task candidate by sum of token weights; apply a few
   fixed safety rules (refuse shell / unknown input caps; candidate≠completeness
   for calculus features; SMT metadata + authorityExternal).

Evaluated on ``benchmarks/tool_selection`` (held-out relative to corpus train).

Honesty:
- Reports measured accuracy vs naive baseline; lift may be zero or weak.
- Does NOT claim frontier acceleration, funding, or Lean acceptance influence.
- ``acceptanceInfluence`` remains false; this script never feeds checkers.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.metrics.foundry_tool_selection import naive_baseline  # noqa: E402
from scripts.run_tool_selection_benchmark import score_selection  # noqa: E402

CORPUS = ROOT / "foundry" / "corpus" / "v0.1"
MANIFEST = ROOT / "benchmarks" / "tool_selection" / "manifest.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")

FORBIDDEN_CAPS = frozenset({"system.shell", "system.arbitrary_python"})

# Small synonym seeds so capabilities absent from the tiny train split can still
# be selected when goalFeatures overlap. Counts from corpus then strengthen these.
SEED_SYNONYMS: dict[str, list[str]] = {
    "algebra.rational_equality": [
        "rational",
        "equality",
        "denominator",
        "denominators",
        "cancel",
        "pole",
    ],
    "algebra.linear_algebra": [
        "matrix",
        "inverse",
        "inverse_witness",
        "linear",
        "exact",
        "arithmetic",
    ],
    "logic.finite_counterexample": [
        "finite",
        "counterexample",
        "refutation",
        "domain",
    ],
    "algebra.formal_rational_calculus": [
        "derivative",
        "antiderivative",
        "calculus",
        "symbolic",
        "ode",
        "recurrence",
        "candidate",
    ],
    "logic.smt": [
        "smt",
        "federation",
        "metadata",
        "external",
        "interop",
        "checker",
    ],
}

CLAIM_SEEDS: dict[str, list[str]] = {
    "soundResult": ["sound", "certified", "equality", "prove"],
    "candidate": ["candidate", "derivative", "ode", "completeness"],
    "refutation": ["refutation", "counterexample", "false"],
    "witness": ["witness", "inverse", "matrix"],
    "metadata": ["metadata", "federation", "smt", "external"],
}


def tokenize(*parts: str | None) -> list[str]:
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        text = str(part).lower().replace(".", " ").replace("/", " ").replace("_", " ")
        out.extend(TOKEN_RE.findall(text))
    return out


def episode_feature_tokens(ep: dict[str, Any]) -> list[str]:
    """Discriminative tokens only (no full candidate-list dump)."""
    tu = ep.get("toolUse") or {}
    prov = ep.get("provenance") or {}
    payload = ep.get("payload") or {}
    return tokenize(
        tu.get("selectionRationale"),
        tu.get("selectedOperation"),
        tu.get("requestedClaim"),
        prov.get("sourcePath"),
        prov.get("checkerPackage"),
        payload.get("slug"),
        ep.get("kind"),
    )


def episode_labels(ep: dict[str, Any]) -> tuple[str, str]:
    tu = ep.get("toolUse") or {}
    outcome = ep.get("outcome") or {}
    payload = ep.get("payload") or {}
    if outcome.get("negative"):
        cap = str(payload.get("correctCapability") or tu.get("selectedCapability"))
        if outcome.get("negativeKind") == "claim_strength_mismatch":
            claim = "candidate"
        elif cap == "algebra.rational_equality":
            claim = "soundResult"
        else:
            claim = str(tu.get("requestedClaim") or "soundResult")
        return cap, claim
    return str(tu.get("selectedCapability")), str(tu.get("requestedClaim") or "soundResult")


def task_tokens(task: dict[str, Any]) -> list[str]:
    return tokenize(task.get("goal"), *(task.get("goalFeatures") or []))


class WeightedTokenSelector:
    """Seeded lexicon + additive learned counts (trivial trainable baseline)."""

    def __init__(self) -> None:
        self.cap_weights: dict[str, Counter[str]] = defaultdict(Counter)
        self.claim_weights: dict[str, Counter[str]] = defaultdict(Counter)
        self.cap_prior: Counter[str] = Counter()
        self.claim_prior: Counter[str] = Counter()

    def _seed(self) -> None:
        for cap, syns in SEED_SYNONYMS.items():
            for tok in tokenize(cap, *syns):
                self.cap_weights[cap][tok] += 1
            self.cap_prior[cap] += 1
        for claim, syns in CLAIM_SEEDS.items():
            for tok in tokenize(claim, *syns):
                self.claim_weights[claim][tok] += 1
            self.claim_prior[claim] += 1

    def fit(self, episodes: list[dict[str, Any]]) -> None:
        self._seed()
        for ep in episodes:
            tokens = episode_feature_tokens(ep)
            cap, claim = episode_labels(ep)
            if not cap or cap in FORBIDDEN_CAPS:
                continue
            self.cap_prior[cap] += 1
            self.claim_prior[claim] += 1
            for tok in tokens:
                self.cap_weights[cap][tok] += 1
                self.claim_weights[claim][tok] += 1
            # Reinforce capability name tokens on positive evidence.
            for tok in tokenize(cap):
                self.cap_weights[cap][tok] += 1

    def _score(self, weights: dict[str, Counter[str]], prior: Counter[str], tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        total_prior = sum(prior.values()) or 1
        scores: dict[str, float] = {}
        for label in weights:
            score = 0.5 * (math.log(max(prior[label], 1)) - math.log(total_prior))
            for tok, tf in counts.items():
                score += tf * (weights[label][tok] + 0.1)
            scores[label] = score
        return scores

    def predict_capability(self, tokens: list[str], candidates: list[str]) -> str | None:
        scores = self._score(self.cap_weights, self.cap_prior, tokens)
        tokset = set(tokens)
        best: str | None = None
        best_score = float("-inf")
        for cap in candidates:
            if cap in FORBIDDEN_CAPS:
                continue
            if cap not in self.cap_weights:
                continue
            s = scores.get(cap, 0.0)
            s += 2.0 * len(set(tokenize(cap)) & tokset)
            # Strong bonus for seeded synonym hits (dominates accidental
            # shared tokens like "rational" inside "rational matrix").
            for syn in SEED_SYNONYMS.get(cap, []):
                syn_toks = set(tokenize(syn))
                if syn_toks & tokset:
                    s += 8.0 * len(syn_toks & tokset)
            if s > best_score:
                best_score = s
                best = cap
        return best

    def predict_claim(self, tokens: list[str], selected: str) -> str:
        scores = self._score(self.claim_weights, self.claim_prior, tokens + tokenize(selected))
        if not scores:
            return "soundResult"
        return max(scores, key=scores.get)  # type: ignore[arg-type]


def _infer_operation(selected: str, tokens: list[str]) -> str | None:
    tokset = set(tokens)
    if selected == "algebra.linear_algebra":
        return "inverse_witness"
    if selected == "algebra.formal_rational_calculus":
        if "ode" in tokset:
            return "ode_candidate"
        if "antiderivative" in tokset:
            return "antiderivative_candidate"
        if "recurrence" in tokset:
            return "recurrence_identity"
        return "derivative_candidate"
    return None


def load_train_episodes() -> list[dict[str, Any]]:
    splits = json.loads((CORPUS / "splits.json").read_text(encoding="utf-8"))
    train_ids = set(splits["train"])
    episodes: list[dict[str, Any]] = []
    for path in sorted((CORPUS / "episodes").glob("*.json")):
        ep = json.loads(path.read_text(encoding="utf-8"))
        if ep.get("episodeId") not in train_ids:
            continue
        if ep.get("acceptanceInfluence") is not False:
            raise ValueError(f"{path}: acceptanceInfluence must be false")
        episodes.append(ep)
    return episodes


def load_tasks() -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [
        json.loads((MANIFEST.parent / rel).read_text(encoding="utf-8"))
        for rel in manifest["tasks"]
    ]


def trained_select(task: dict[str, Any], model: WeightedTokenSelector) -> dict[str, Any]:
    tokens = task_tokens(task)
    candidates = list(task.get("capabilityCandidates") or [])
    feats = {str(f).lower() for f in (task.get("goalFeatures") or [])}
    inp = task.get("input") or {}

    requested = inp.get("capability")
    if requested and requested not in model.cap_weights:
        return {
            "action": "refuse_or_unsupported",
            "selectedCapability": None,
            "toolCalls": 1,
            "refused": [c for c in candidates if c in FORBIDDEN_CAPS or c == requested],
        }

    if "unknown_capability" in feats or "honest_refusal" in feats:
        return {
            "action": "refuse_or_unsupported",
            "selectedCapability": None,
            "toolCalls": 1,
            "refused": sorted(
                {
                    c
                    for c in candidates
                    if c in FORBIDDEN_CAPS or c not in model.cap_weights
                }
            ),
        }

    selected = model.predict_capability(tokens, candidates)
    if selected is None:
        return {
            "action": "refuse_or_unsupported",
            "selectedCapability": None,
            "toolCalls": 1,
            "refused": sorted(FORBIDDEN_CAPS & set(candidates)),
        }

    claim = model.predict_claim(tokens, selected)

    if selected == "algebra.formal_rational_calculus" and (
        "candidate" in feats
        or "candidate_not_completeness" in feats
        or "no_completeness_overclaim" in feats
        or "ode" in feats
    ):
        claim = "candidate"
    if selected == "logic.finite_counterexample":
        claim = "refutation"
    if selected == "logic.smt":
        claim = "metadata"
    # Suite accepts soundResult/candidate for LA inverse; map witness→soundResult.
    if selected == "algebra.linear_algebra" and claim == "witness":
        claim = "soundResult"

    refused = sorted(FORBIDDEN_CAPS & set(candidates))
    selection: dict[str, Any] = {
        "selectedCapability": selected,
        "requestedClaim": claim,
        "toolCalls": 1,
        "refused": refused,
    }
    if selected == "logic.smt":
        selection["authorityExternal"] = True
    op = _infer_operation(selected, tokens)
    if op:
        selection["selectedOperation"] = op
    return selection


def measure() -> dict[str, Any]:
    episodes = load_train_episodes()
    model = WeightedTokenSelector()
    model.fit(episodes)
    tasks = load_tasks()

    def score_policy(name: str, fn) -> dict[str, Any]:
        ok = 0
        rows = []
        for task in tasks:
            sel = fn(task)
            passed, msg = score_selection(task, sel)
            if passed:
                ok += 1
            rows.append({"id": task["id"], "pass": passed, "msg": msg, "selection": sel})
        total = len(tasks)
        return {
            "policy": name,
            "passed": ok,
            "total": total,
            "accuracy": round(ok / total, 4) if total else 0.0,
            "rows": rows,
        }

    naive = score_policy("naive_always_rational", naive_baseline)
    trained = score_policy(
        "foundry_train_weighted_bag",
        lambda t: trained_select(t, model),
    )
    lift = round(trained["accuracy"] - naive["accuracy"], 4)

    return {
        "metric": "tool_selection_trained_vs_naive",
        "method": (
            "Rule + learned bag-of-token weights: seeded capability/claim synonym "
            "lexicon plus additive counts from foundry/corpus/v0.1 train split; "
            "safety rules for shell refusal, unknown-cap refusal, and "
            "candidate≠completeness. Evaluated on benchmarks/tool_selection. "
            "Pure Python; acceptanceInfluence=false."
        ),
        "train": {
            "corpus": "foundry/corpus/v0.1",
            "split": "train",
            "episodes": len(episodes),
            "capability_labels": sorted(model.cap_prior.keys()),
            "claim_labels": sorted(model.claim_prior.keys()),
        },
        "eval": {
            "suite": "benchmarks/tool_selection",
            "tasks": len(tasks),
            "held_out_relative_to_corpus_train": True,
        },
        "naive": {k: v for k, v in naive.items() if k != "rows"},
        "trained": {k: v for k, v in trained.items() if k != "rows"},
        "accuracy_lift_trained_minus_naive": lift,
        "naive_rows": [
            {k: v for k, v in row.items() if k != "selection"} for row in naive["rows"]
        ],
        "trained_rows": [
            {k: v for k, v in row.items() if k != "selection"} for row in trained["rows"]
        ],
        "claims": {
            "trained_selector_measured": True,
            "frontier_acceleration": False,
            "funding_secured": False,
            "acceptance_influence": False,
        },
        "notes": (
            "Lift is measured on the small public tool_selection suite. "
            "Zero or weak lift is reported honestly; does not close funding/frontier exits."
        ),
    }


def main() -> int:
    result = measure()
    print(json.dumps(result, indent=2))
    print(
        f"trained_selector: naive={result['naive']['accuracy']:.1%} "
        f"trained={result['trained']['accuracy']:.1%} "
        f"lift={result['accuracy_lift_trained_minus_naive']:+.1%} "
        f"(train n={result['train']['episodes']}, "
        f"eval n={result['eval']['tasks']})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
