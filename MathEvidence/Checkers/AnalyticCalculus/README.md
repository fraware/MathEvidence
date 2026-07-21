# AnalyticCalculus checker scaffold

This directory reserves documentation for the future analytic-calculus vertical
(ME-105). No full analytic checker or proof-producing implementation is added in
this pass.

## Required theorem shape

Analytic-calculus evidence must ultimately establish Lean analytic statements
such as `HasDerivAt`, `DifferentiableAt`, or explicitly equivalent theorem
forms over the interpreted analytic expression. It must not conclude only a
`RationalExpr.polyEqual` or similar polynomial identity.

Polynomial equalities may be useful subgoals after a sound reduction, but they
are not the top-level analytic claim. Domain, differentiability, and side
condition handling must be explicit before any future checker claims success.
