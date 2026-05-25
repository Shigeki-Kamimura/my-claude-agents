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
- `r`: / `rev:` -> `reviewer` (convergence only)
- `q:` / `qa:` -> `test-qa`
- `a:` / `adv:` -> `adviser` (L2+ review routing)
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

Rules:
- Prefix routing has priority over default review order.
- `cr:` runs only `code-quality-reviewer`.
- `cr:` must not automatically continue to `adviser`.
- `adviser` is used only when the user explicitly uses `adv:` / `a:` or requests L2+ review.
- `reviewer` is used only for convergence after prior Review Tickets or claimed fixes.

## Review Flow

Review agents are independent.

Prefix routing always has priority.

Typical human-operated flow:

1. `cr:` for L1.5 local code-quality review
2. `qa:` when regression verification is needed
3. `adv:` for initial L2+ scope/risk review
4. specialists only for clearly high-risk domains
5. `rev:` only after fixes for convergence review

Rules:
- Do not automatically chain review agents.
- Do not escalate from `cr:` to `adv:` automatically.
- Do not send first-pass PR review to `reviewer`.
- Each review command owns only its scoped review layer.

## QA Boundary

- `test-qa` owns unit/integration regression planning and high-signal verification gaps.
- `e2e-qa` owns Playwright/Cypress scenario design and implementation for user-flow coverage.
- Use `e2e-qa` only when behavior must be proven through browser-level user actions.
- Prefer structuring E2E by `read` / `write` / `rules` / `auth`.
- Split browser tests by dominant risk axis instead of feature size alone.
- Split or add files before a single E2E spec exceeds 400 lines.

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

## Design References

Canonical review-pattern reference in this config repository:
- `.claude/knowledge/human-review-patterns.md`

Required review-pattern section for design alignment:
- `## Design Document Alignment`

This config repository does not define universal project design paths such as `DESIGN.md`, `docs/design/`, `docs/adr/`, `ARCHITECTURE.md`, or `SPEC.md`.

When reviewing a target project:
- enumerate actual design/spec paths in that project before citing them
- grep for directly related sections before reading
- cite only sections personally inspected in the current task

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
