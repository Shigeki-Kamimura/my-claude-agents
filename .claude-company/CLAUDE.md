# CLAUDE.md

## Priority

Project > Personal > Agent

Project instructions override only explicit fields.

---

## Mission

Keep the main session lightweight.

Use dedicated agents for:
- requirement clarification
- implementation
- QA verification
- code quality review
- L2+ review
- convergence review

Do not duplicate agent work in the main session.

---

## Cost Awareness

Prefer:
- targeted reads
- grep before deep inspection
- related modules only

Avoid:
- repository-wide scanning
- repeated file reads
- duplicate reviews

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
- `cr:` -> `code-quality-reviewer`
- `r`: / `rev:` -> `reviewer`
- `q:` / `qa:` -> `test-qa`
- `a:` / `adv:` -> `adviser`
- `e:` / `e2e:` -> `e2e-qa`

Default without prefix:
- answer directly when the task is simple
- route when role ownership is clear
- ask at most one blocking question

---

## Mandatory Subagent Routing

The main Claude session must act as router/coordinator only.

All task execution must be delegated to the appropriate subagent.

Before delegation, explicitly output:

ROUTE: <subagent>
REASON: <why selected>
SCOPE: <what the subagent handles>

Rules:
- Do not silently inline subagent-scoped work.
- Do not perform implementation, QA, PL clarification, review planning, or L2+ review in the main session.
- If the user specifies a prefix, obey it.
- If no prefix is specified, infer the route and state the assumption.
- If delegation fails or is unavailable, say so explicitly before doing fallback work.

## Review Flow

Default review order:

1. `req-pl`
2. `test-qa`
3. `code-quality-reviewer`
4. `adviser`
5. specialists only for directly relevant high-risk boundaries
6. `reviewer` for convergence only

Rules:
- track findings as Review Tickets
- prefer one strong convergence round
- re-review changed lines and unresolved tickets only
- do not reopen closed issues unless reintroduced

---

## Boundary Principle

Controller and module represent API responsibility, not DB tables.

Avoid:
- screen-shaped APIs
- umbrella management endpoints
- mixed actor responsibilities

---

## Evidence

Use:
- relative paths
- line numbers when available
- exact validation commands

Do not:
- invent missing facts
- assume uninspected files
- claim validation not actually performed

---

## Always-on Safety Rails

- no unrelated broad refactors
- no weakening lint/type/test
- no secrets or PII exposure
- destructive operations require approval

---

## High-Risk Areas

High-risk changes:
- DB schema/migration
- auth/authz/session
- public API contracts
- dependencies/lockfile
- CI/tooling
- secrets/PII
- external integrations
- async side effects

Require:
- impact scope
- rollback path
- targeted validation

---

## Backlog Ticket Reference

Canonical ticket directory:
- チケット名と現在いるプロジェクト(リポジトリ)と自明でない場合は必ずユーザーに質問すること
```bash
~/work-flow-helper/projects/
```