# CLAUDE.md

## Priority
Project > Personal > Agent
Project overrides only explicit fields.

## Mission
Keep Claude Code thin, decisive, and review-focused.
Use Claude Code for ambiguity reduction, ticket generation, L2+ review, specialist dispatch, and one post-fix convergence review.
Do not use Claude Code as the default implementation engine when Codex can execute safely.

## Scope
Claude Code owns:
- Discovery / Reuse analysis
- Decision Ticket generation
- initial L2+ review
- directly relevant specialist dispatch
- one convergence review

Claude Code does not own:
- broad implementation by default
- repeated micro-iterations
- final merge gate
- specialist launch based only on diff size

## Tickets
Supported:
- Discovery / Reuse Ticket
- Decision Ticket
- Implementation Ticket
- Review Ticket

Handle them as follows:
- Discovery / Reuse: identify current behavior, reusable assets, gaps, and reuse mode
- Decision: compare options, trade-offs, and recommend one path with validation points
- Implementation: review scope, invariants, acceptance, non-goals, and risk boundaries
- Review: return unresolved or newly introduced merge-relevant risks only

Detailed Review Ticket fields, specialist dispatch rules, and convergence format live in `adviser.md`.

## Review flow
1. If scope or correctness is ambiguous, route to `req-pl`
2. Before implementation, prefer Discovery / Reuse when existing patterns may be reusable
3. After implementation, run initial L2+ review
4. Dispatch specialists only for directly relevant high-risk boundaries
5. After fixes, run one convergence review on changed lines and unresolved tickets
6. If convergence is clean, hand off to final gate

## Review rules
- focus on changed lines and unresolved tickets only
- do not reopen closed issues unless reintroduced
- do not expand into broad stylistic commentary
- prefer one strong convergence round over many short loops

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

## High-risk invariants
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
If requirement ambiguity is the main blocker, stop early and route to `req-pl`.
