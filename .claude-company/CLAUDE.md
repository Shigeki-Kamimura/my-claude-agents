# CLAUDE.md

## Priority

Project > Personal > Agent

Project instructions override only explicit fields.

## Mission

Keep the main session lightweight.

Use dedicated agents for:
- requirement clarification
- implementation
- QA verification
- L2+ review
- convergence review

Do not duplicate agent work in the main session.

---

## Core Priorities

Accuracy > reproducibility > maintainability > ease > speed

Prefer:
- clear scope
- small diffs
- explicit behavior
- validated progress
- ticket-based review

Never weaken:
- type safety
- lint rules
- tests

---

## Role Routing

Use agents by prefix:

- `p:` / `pl:` -> `req-pl`
- `h:` / `hq:` -> `hq-coder`
- `q:` / `qa:` -> `test-qa`
- `adv:` -> `adviser`

Default without prefix:
- answer directly when the task is simple
- route to the appropriate agent when role ownership is clear
- ask at most one question only if correctness is blocked

---

## Review Flow

Default review order:

1. `req-pl` if requirements, ownership, or acceptance are unclear
2. `adviser` for L2+ review and Review Ticket normalization
3. `test-qa` for regression / L0-L1 safety net
4. specialists only for directly relevant high-risk boundaries

Rules:
- track findings as Review Tickets
- prefer one strong convergence round over many short loops
- re-review changed lines and unresolved tickets only
- do not reopen closed issues unless reintroduced

---

## Review Output Constraints

Review findings should be ticket-level.

Use:
- ID
- severity
- route
- location
- short label

Avoid:
- long narrative explanations
- style-only findings
- speculative improvements
- broad redesign without concrete failure path

Keep top risks to max 5 unless correctness clearly requires more.

---

## Boundary Principle

Controller and module must represent API responsibility, not DB tables.

Split when:
- actor differs
- permission differs
- use-case differs
- change reason differs

Avoid:
- screen-shaped APIs
- umbrella `management` endpoints
- mixing self-service and admin operations
- mixing master data and user-linkage operations

---

## Evidence

Use:
- relative path
- line numbers when available
- exact command names for validation

Do not:
- invent missing facts
- assume uninspected files
- claim validation was run when it was not

---

## Always-on Safety Rails

- no unused dependencies
- no unrelated broad refactors
- no weakening lint / typecheck / tests
- no secrets or PII in logs / commits / URLs
- destructive operations require approval

---

## High-Risk Areas

High-risk changes include:
- DB schema / migration / backfill
- authn / authz / session
- public API contracts
- dependencies / lockfile
- CI / tooling
- secrets / PII
- external integrations
- async side effects

For high-risk changes, require:
- impact scope
- rollback path
- targeted validation

---

## Comment Policy

Add comments only when intent is non-obvious.

Good comments explain:
- why a branch exists
- guard precondition
- transaction / async boundary
- trust boundary
- magic number rationale

Do not add comments that restate obvious code.