# ADR 0003 — Use JSON-RPC over stdio for v0 adapters

## Decision

Adapters communicate through versioned JSON-RPC over standard input/output.

## Rationale

This transport is language-neutral, easy to sandbox, simple to test, and avoids premature daemon lifecycle and network security complexity.

## Revisit condition

A persistent transport is considered only when measured startup overhead materially limits supported workflows.
