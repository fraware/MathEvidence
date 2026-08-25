# SPEC-11 — Bounded Execution and Security Hardening for Generated Replay


> **Repository baseline:** `fraware/MathEvidence`  
> **Open integration branch:** PR #53  
> **Pinned head assessed:** `30522d70e9be0f3fda9b9b6febc7502b9ef4c34b`  
> **Assessment date:** 2026-08-25  
>
> This specification is intentionally pinned to the repository state above. If implementation begins from a different commit,
> engineers MUST first execute SPEC-00 and record the delta. Historical status labels are not authority for theorem-level
> certification eligibility.


**Priority:** Cross-cutting P0/P1  
**Current baseline:** security and adversarial gates pass at pinned head  
**Owner profile:** Security/platform engineer

## Objective

Ensure candidate-bound code generation and Lean replay inherit or strengthen the repository's bounded-execution guarantees
without creating a new command, filesystem, output, or resource-exhaustion escape path.

## Threat model

Treat candidate/evidence payloads and artifact metadata as untrusted.

Relevant threats include:

- Lean/source injection;
- shell/metacharacter injection;
- path traversal;
- symlink escape;
- unbounded generated source;
- gigantic integer/rational/expression payloads;
- verifier hang;
- child-process orphaning;
- unbounded stdout/stderr;
- hostile filenames/module names;
- environment-variable influence;
- hidden network/dependency fetch;
- decompression/artifact expansion abuse where applicable.

## Requirements

### Input/generator boundary

- typed AST only for generated Lean syntax;
- reject raw arbitrary Lean fragments;
- canonical controlled module/file naming;
- validate all identifiers;
- enforce depth/size/cardinality limits before rendering.

### Process boundary

Use the repository's bounded execution abstraction consistently:

- wall-clock timeout;
- process-group termination;
- maximum captured output;
- controlled working directory;
- explicit environment allowlist where feasible;
- no shell string interpolation;
- executable + argv invocation;
- clear timeout/resource failure status.

### Filesystem boundary

- confine generated files and replay artifacts to designated workspace;
- reject path traversal;
- resolve/check paths before use;
- test symlink escape if filesystem semantics permit it.

### Dependency/network boundary

- exact offline replay uses pinned/materialized dependencies;
- no implicit network fallback;
- integrity failure is explicit.

## Required adversarial tests

- `../` and absolute-path identifiers;
- shell metacharacters;
- Lean-looking malicious text in string fields;
- extreme nesting;
- extreme matrix/vector dimensions;
- huge integer/rational literal;
- output-flooding fake verifier process where testable;
- hanging child process;
- spawned child process killed with group;
- symlink out of workspace;
- environment poisoning attempt.

## Acceptance criteria

- [ ] Generated replay uses typed IR.
- [ ] No candidate field is interpolated into a shell command.
- [ ] Time/output/process-group limits cover Lean replay.
- [ ] Workspace/path confinement tests pass.
- [ ] Oversized inputs fail before expensive verification.
- [ ] Offline mode has no network fallback.
- [ ] Existing security/adversarial CI remains green.
- [ ] New exact capabilities inherit the same execution policy by construction.

## Definition of done

Exact replay increases mathematical assurance without expanding the operational trust boundary in an uncontrolled way.
