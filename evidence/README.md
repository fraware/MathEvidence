# Evidence bundles

Committed offline-replayable artifacts.

- `examples/` — human-oriented demos (SymPy + Mathematica offline fixtures)
- `conformance/rfc0001/` — RFC 0001 adapter conformance cases (+ bundles)
- `conformance/vectors/` — canonical JSON digest vectors

## Replay

Python (schemas + digests, no backends):

```text
python scripts/offline_replay_python.py
```

Lean checker (same committed bundles mirrored into `OfflineFixtures.lean`, no backends):

```text
python scripts/generate_lean_offline_fixtures.py
lake build MathEvidence.Checkers.RationalEquality.OfflineFixtures
lake build MathEvidence.Tactic.Examples
```

Or: `just replay` (Python + Lean).
