# Repository commands. CI is authoritative; local `just check` mirrors required gates.

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

# Full local gate assumed by CONTRIBUTING.md. It is intentionally heavy and
# includes Ruff lint/format checks, mypy, pytest including tests/forensic, and
# capability registry validation.
check: lean-build import-boundary sorry-audit schema-validate registry-validate federation-validate assurance-validate python-check lint fmt mypy test forensic-test studio-test conformance differential replay adversarial adversarial-exec leanlink-fuzz property metamorphic perf-budgets real-world agent-held-out foundry-validate tool-selection foundry-metrics metrics registry-historical-replay trace-to-plan-demo
    @echo "just check: ok"

lean-build:
    lake build

import-boundary:
    python scripts/check_import_boundaries.py

sorry-audit:
    python scripts/audit_sorry_axioms.py

schema-validate:
    python scripts/validate_schemas.py

registry-validate:
    python scripts/validate_registry.py

federation-validate:
    python scripts/validate_federation.py
    python scripts/run_federation_harness.py

assurance-validate:
    python scripts/validate_assurance.py

registry-historical-replay:
    python scripts/test_registry_historical_replay.py

trace-to-plan-demo:
    python scripts/run_trace_to_plan_demo.py

python-check:
    python -c "import adapters.common; import adapters.common.discovery; import adapters.common.rpc_client; import adapters.sympy; import adapters.mathematica; import adapters.sage; import agent.api; import agent.sdk; import agent.hypothesis; import agent.conjecture; import agent.trace_to_plan; import foundry.capture; import foundry.pipelines; print('adapters+agent+foundry import ok')"

lint:
    python -m ruff check adapters scripts agent foundry tests

fmt:
    python -m ruff format --check adapters scripts agent foundry tests

mypy:
    python -m mypy adapters agent

test:
    python -m pytest adapters agent foundry -q

forensic-test:
    python -m pytest tests/forensic -q

# Product 09 Studio epistemic gate + golden transcripts (VS Code / Wolfram contract)
studio-test:
    python -m pytest adapters/common/test_epistemic_studio.py -q

agent-held-out:
    python scripts/run_agent_held_out.py

agent-held-out-baseline:
    python scripts/run_agent_held_out_baseline.py

foundry-corpus:
    python scripts/build_foundry_corpus.py

foundry-validate:
    python scripts/validate_foundry_corpus.py

tool-selection:
    python scripts/run_tool_selection_benchmark.py

metrics:
    python scripts/metrics/run_section19_metrics.py

foundry-metrics:
    python scripts/metrics/foundry_tool_selection.py
    python scripts/metrics/foundry_corpus_quality.py
    python scripts/metrics/track_contributions.py

# Train trivial selector on foundry corpus train split; eval on tool_selection.
foundry-train-eval:
    python scripts/metrics/foundry_trained_selector.py

agent-api:
    python -m agent.api.server --host 127.0.0.1 --port 8787

conformance:
    python scripts/run_adapter_conformance.py

differential:
    python scripts/run_differential_backends.py

replay: replay-python replay-lean

replay-python:
    python scripts/offline_replay_python.py

replay-lean:
    lake build MathEvidence.Core.JsonCanonicalTests MathEvidence.Checkers.RationalEquality.OfflineFixtures MathEvidence.Checkers.Calculus.Tests MathEvidence.Tactic.Examples MathEvidence.Hypothesis MathEvidence.Conjecture MathEvidence.TraceToPlan MathEvidence.Assurance

adversarial:
    python scripts/validate_adversarial_seed.py

adversarial-exec:
    python scripts/run_adversarial_executable.py

leanlink-fuzz:
    python scripts/run_leanlink_fuzz_stubs.py

property:
    python scripts/run_property_tests.py

metamorphic:
    python scripts/run_metamorphic.py

perf-budgets:
    python scripts/run_perf_budgets.py

real-world:
    python scripts/run_real_world.py

generate-evidence:
    python scripts/generate_evidence_fixtures.py

generate-m3-evidence:
    python scripts/generate_m3_evidence.py

generate-m5-evidence:
    python scripts/generate_m5_evidence.py

generate-lean-fixtures:
    python scripts/generate_lean_offline_fixtures.py

release-provenance:
    python scripts/generate_release_provenance.py

