# Repository commands. CI is authoritative; local `just check` mirrors required gates.

set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

# Full local gate assumed by CONTRIBUTING.md
check: lean-build import-boundary sorry-audit schema-validate registry-validate federation-validate assurance-validate python-check test conformance replay adversarial agent-held-out foundry-validate tool-selection
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

assurance-validate:
    python scripts/validate_assurance.py

python-check:
    python -c "import adapters.common; import adapters.common.discovery; import adapters.common.rpc_client; import adapters.sympy; import adapters.mathematica; import adapters.sage; import agent.api; import agent.sdk; import agent.hypothesis; import agent.conjecture; import agent.trace_to_plan; import foundry.capture; import foundry.pipelines; print('adapters+agent+foundry import ok')"

lint:
    python -m ruff check adapters scripts agent foundry

test:
    python -m pytest adapters agent foundry -q

agent-held-out:
    python scripts/run_agent_held_out.py

foundry-corpus:
    python scripts/build_foundry_corpus.py

foundry-validate:
    python scripts/validate_foundry_corpus.py

tool-selection:
    python scripts/run_tool_selection_benchmark.py

agent-api:
    python -m agent.api.server --host 127.0.0.1 --port 8787

conformance:
    python scripts/run_adapter_conformance.py

replay: replay-python replay-lean

replay-python:
    python scripts/offline_replay_python.py

replay-lean:
    lake build MathEvidence.Core.JsonCanonicalTests MathEvidence.Checkers.RationalEquality.OfflineFixtures MathEvidence.Checkers.Calculus.Tests MathEvidence.Tactic.Examples MathEvidence.Hypothesis MathEvidence.Conjecture MathEvidence.TraceToPlan MathEvidence.Assurance

adversarial:
    python scripts/validate_adversarial_seed.py

generate-evidence:
    python scripts/generate_evidence_fixtures.py

generate-m3-evidence:
    python scripts/generate_m3_evidence.py

generate-m5-evidence:
    python scripts/generate_m5_evidence.py

generate-lean-fixtures:
    python scripts/generate_lean_offline_fixtures.py

fmt:
    @echo "Phase 1: no Lean formatter gate yet"
