# Conformance benchmark pointer

Backend-independent expected behavior lives under `evidence/conformance/`.
This directory exists so CI inventory (`benchmarks.yml`) can require a stable
tree. Run:

```text
just conformance
python scripts/run_adapter_conformance.py
```
