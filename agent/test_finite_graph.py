"""FiniteGraph conjecture vertical tests (Product 04 primary)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.conjecture.finite_graph import (
    ATLAS_REL,
    GENERATOR_VERSION,
    INVARIANT_NAMES,
    calibrated_candidates,
    compute_invariants,
    decode_graph6,
    encode_graph6,
    expand_falsification_variants,
    family_request,
    load_atlas,
    run_falsification_batch,
)
from adapters.common.lean_mirrors import check_finite_counterexample

ROOT = Path(__file__).resolve().parents[1]


def test_atlas_nonduplicate_ge_1000() -> None:
    instances = load_atlas(ROOT / ATLAS_REL)
    assert len(instances) >= 1000
    ids = {g.instance_id for g in instances}
    assert len(ids) == len(instances)
    g6s = {g.graph6 for g in instances}
    assert len(g6s) == len(instances)


def test_graph6_roundtrip_sample() -> None:
    instances = load_atlas(ROOT / ATLAS_REL)
    for g in instances[:50]:
        n, bits = decode_graph6(g.graph6)
        assert n == g.n
        assert bits == g.upper_triangle
        assert encode_graph6(n, bits) == g.graph6


def test_invariants_cover_five_plus() -> None:
    instances = load_atlas(ROOT / ATLAS_REL)
    assert len(INVARIANT_NAMES) >= 5
    inv = compute_invariants(instances[10])
    for name in INVARIANT_NAMES:
        assert name in inv


def test_calibrated_batch_falsifies_with_mirror() -> None:
    batch = run_falsification_batch(n=3)
    assert batch["generatorVersion"] == GENERATOR_VERSION
    assert batch["precisionAccounting"]["falsified"] >= 1
    assert batch["counterexamples"], "expected at least one certified refutation"
    for cex in batch["counterexamples"]:
        assert check_finite_counterexample(cex["request"], cex["certificate"])
        assert cex["mirrorAccepted"] is True


def test_empty_graph_falsifies_has_edge_like_lean() -> None:
    """Mirror the Lean FiniteGraph empty-graph path for Fin-3."""
    cands = [c for c in calibrated_candidates(3) if c["id"] == "fin3_has_edge"]
    assert len(cands) == 1
    batch = run_falsification_batch(n=3, candidates=cands)
    assert batch["precisionAccounting"]["falsified"] == 1
    cex = batch["counterexamples"][0]
    witness = cex["certificate"]["witness"]["assignment"]
    assert witness == [
        {"tag": "bool", "v": False},
        {"tag": "bool", "v": False},
        {"tag": "bool", "v": False},
    ]


def test_expanded_variants_are_falsifiable() -> None:
    variants = expand_falsification_variants(3, limit=16)
    assert len(variants) == 7  # Fin-3 has 2^3-1 nonempty edge subsets
    batch = run_falsification_batch(n=3, candidates=variants)
    assert batch["precisionAccounting"]["falsified"] == 7
    big = expand_falsification_variants(5, limit=32)
    assert len(big) == 32
    batch5 = run_falsification_batch(n=5, candidates=big[:8])
    assert batch5["precisionAccounting"]["falsified"] == 8


def test_family_request_digest_bound() -> None:
    req = family_request(3, calibrated_candidates(3)[0]["pred"])
    assert req["requestDigest"].startswith("sha256:")
    assert len(req["predicate"]["domains"]) == 3


def test_nat_inequality_not_in_calibrated_primary() -> None:
    """Nat inequality fixtures remain non-primary; calibrated preds are Bool edges."""
    for c in calibrated_candidates(3):
        domains = family_request(3, c["pred"])["predicate"]["domains"]
        assert all(d.get("ty") == "bool" for d in domains)
