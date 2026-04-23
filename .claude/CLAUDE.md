# CLAUDE.md

## Priority
Project > Personal > Agent
Project overrides only explicit fields.

## Mission
Maximize L0-L1 quality during coding.
L2+ review belongs to specialist agents.

## Core priorities
Review flow: use L2+ for initial high-risk review; track issues as tickets; re-review diffs only.

Review findings must be ticket-level:
- ID + location + short label only
- max 1 line per issue
- max 5 issues
- no narrative explanation

Re-review must focus on changed lines and unresolved tickets only.
Accuracy > reproducibility > maintainability > ease > speed
Clarity > cleverness
Small diffs > large rewrites
Explicit errors > silent failure
Validated progress > theoretical perfection

Never weaken:
- type safety
- lint rules
- tests

## Controller Boundary Principle
Controller must represent API responsibility, not database tables.

Do not group endpoints only by entity.
Split when actor, permission, or use-case differs.

## Output
- User-facing replies: Japanese
- Code / identifiers / commit messages: English
- Comments / docstrings: concise Japanese

## Evidence
Use relative path + line numbers.
Do not invent missing facts.
Ask at most 1 question only if correctness is blocked.

## Role boundary
- `p:` / `pl:` -> `req-pl`
- `h:` / `hq:` -> `hq-coder`
- `q:` / `qa:` -> `test-qa`

Default without prefix: main session responds directly.
Default review order: if requirements are unclear use `req-pl` first; after implementation review with `adviser`, then `test-qa`; escalate specialists only for high-risk boundaries.
Review: `req-pl` if unclear → `adviser` → `test-qa`; specialists for high-risk only.


## Always-on safety rails
- no unused dependencies
- no broad refactor outside scope
- no weakening lint / typecheck / tests
- no secrets or PII in logs / commits / URLs
- destructive ops require approval

## Repo invariants
For high-risk changes, state:
- impact scope
- rollback path
- targeted validation

High-risk:
- DB schema / migration
- authn / authz / session
- public API contracts
- dependencies / lockfile
- CI / tooling
- secrets / PII
- external integrations
- async side effects

## Comment minimum
File header:
- Why
- Scope
- Depends (optional)

Function / method:
- Why
- Contract
- Side effects

Only add comments where intent is non-obvious.