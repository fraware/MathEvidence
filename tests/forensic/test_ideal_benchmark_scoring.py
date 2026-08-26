from __future__ import annotations

import pytest

import scripts.run_ideal_membership_benchmark as benchmark


def _negative_task() -> dict:
    return {
        "id": "negative_scoring_regression",
        "target": {"varCount": 1, "terms": []},
        "generators": [{"varCount": 1, "terms": []}],
        "expectedMultipliers": None,
        "expectedStatus": "xfail",
        "claimClass": "membership",
        "stratum": "adversarial",
    }


@pytest.mark.parametrize(
    ("adapter_claim", "independent_accepts", "expected_status", "false_accept"),
    [
        (False, True, "xfail_unexpected_accept", True),
        (True, False, "xfail_ok", False),
    ],
)
def test_negative_scoring_uses_independent_checker_not_adapter_self_report(
    monkeypatch: pytest.MonkeyPatch,
    adapter_claim: bool,
    independent_accepts: bool,
    expected_status: str,
    false_accept: bool,
) -> None:
    """Negative-corpus scoring must not trust an adapter's acceptance Boolean."""

    def propose_membership_witness(**_: object) -> dict:
        return {
            "multipliers": [{"varCount": 1, "terms": []}],
            "pythonMirrorAccepts": adapter_claim,
            "backend": "adversarial-test",
        }

    def independent_checker(*_: object) -> bool:
        return independent_accepts

    monkeypatch.setattr(benchmark, "propose_membership_witness", propose_membership_witness)
    monkeypatch.setattr(benchmark, "check_membership_python", independent_checker)

    row = benchmark._score_task(
        _negative_task(),
        backend="adversarial-test",
        tier=benchmark.TIER_CANDIDATE,
    )

    assert row["status"] == expected_status
    assert row["proposedAccepts"] is independent_accepts
    assert row["adapterPythonMirrorAccepts"] is adapter_claim
    assert row["adapterCheckerAgreement"] is False
    assert row["criticalFalseAccept"] is false_accept
