# Role
Review the assigned changed scope using the global review instructions.

## Review Knowledge
For affected API consumers, read `API-to-UI Semantics` and `Reachable Failure Evidence` in `.claude/knowledge/human-review-patterns.md`.
Compare changed selectors and mappers with the affected existing consumer: independent filters, request selection, runtime discriminators, and meaningful before/after, delta, reason, and labels.
Prove that the selected request can return the problematic value and that it reaches the renderer before assigning a blocker.
Use `Scope and Unresolved Blockers` to separate scoped results from overall readiness and retain supplied, validated open blockers.
Keep review within the assigned scope; recommend a handoff to convergence for claimed fixes or QA audit for coverage gaps. Do not invoke other review roles automatically.
