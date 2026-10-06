## Language
- Think in English.
- Output in Japanese.
- Be concise.

## Goal
Reduce production risk with minimal discussion.
Prefer one-pass, high-signal review.

## Severity
Focus ONLY on Medium/High production risks.

A finding is valid only if:
- realistic failure path exists
- user/data/operational impact is non-trivial
- supported by code-level evidence

## CI
Treat executed CI results as source of truth.
Passing suites do not establish coverage of an untested API-to-screen case.

## Review Knowledge
For changed API-to-consumer behavior or supplied review tickets, read only the relevant sections of `.claude/knowledge/human-review-patterns.md`: `API-to-UI Semantics`, `Reachable Failure Evidence`, `Cross-Layer Regression Cases`, and `Scope and Unresolved Blockers`.
Apply only the assigned role and changed scope. Prove the actual request/filter-to-response-to-render failure path before assigning a blocker.
State the reviewed revision and scope. Retain supplied, validated unresolved blockers with severity and fix evidence; a clean scoped pass must not imply overall PR approval while those remain open.

## Output
Sort by:
1. severity
2. blast radius
3. confidence

For each finding:
- Location
- Failure scenario
- Impact
- Minimal fix

If none:
- 今回の確認範囲では新規の Medium/High リスクは見当たりませんでした
- List any supplied unresolved blockers or pending handoffs separately; overall readiness remains blocked/deferred until their status is established.
