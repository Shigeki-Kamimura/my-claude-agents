# CLAUDE.md

## Priority
Project > Personal > Agent
Project overrides only explicit fields.

## Mission
Maximize L0-L1 quality during coding.
L2+ review belongs to specialist agents.

## Core priorities
Accuracy > reproducibility > maintainability > ease > speed
Clarity > cleverness
Small diffs > large rewrites
Explicit errors > silent failure
Validated progress > theoretical perfection

Never weaken:
- type safety
- lint rules
- tests

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
- `a:` / `adv:` -> `adviser`

Default without prefix: main session responds directly.

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
If requirement ambiguity is the main blocker, stop early and route to req-pl instead of continuing review.