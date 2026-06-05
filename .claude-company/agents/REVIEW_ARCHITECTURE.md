# Claude Review Architecture

This document is the reference model for Claude-side review agents.
It is intended to be portable to Codex reviewer TOML/XML definitions.

## Core Principle

Review agents are separate from implementation agents.

- `hq-coder` implements.
- Review agents inspect, route, normalize tickets, or verify convergence.
- QA/E2E agents provide test confidence, not general code review.

The system optimizes for high-signal review under token constraints:
- start from PR metadata and changed-file summaries
- inspect targeted files only
- use trigger-based mandatory checks
- dispatch specialists only when the route is justified
- avoid broad rediscovery and duplicate review

## Layer Model

| Layer | Agent | Owns | Does Not Own |
|---|---|---|---|
| L0/L1 QA | user / QA automation | biome, lint, typecheck, build, test execution | L1.5/L2+ review judgment |
| Planning | `review-planner` / `rp:` | review scope, routing, specialist necessity | findings, approval, implementation |
| L1.5 | `code-quality-reviewer` / `cr:` | local code quality, maintainability, nearby pattern fit, reviewability | feature correctness, API/auth/DB/test adequacy |
| L2+ | `adviser` / `adv:` | boundary trace, risk ordering, project-rule checks, specialist dispatch, ticket normalization | convergence, implementation, test sufficiency |
| Convergence | `reviewer` / `rev:` | claimed-fix verification, unresolved ticket status, current-state regressions | first-pass review, broad rediscovery |
| Security | `sec-arch` | authn/authz, trust boundary, IDOR, PII/secret exposure | general code quality |
| Data | `data-platform` | transaction, idempotency, migration, rollback, audit raw values | security/style/general review |
| Test | `test-qa` | regression matrix, failure-mode coverage, contract verification | browser E2E execution, general implementation review |
| E2E | `e2e-qa` / `e:` | Playwright/Cypress browser-flow scenario design and execution | app implementation, unit/integration test strategy |

## Routing Rules

- First-pass review from L1.5 onward starts with `rp:`.
- Direct `cr:` is allowed only for focused L1.5 re-checks.
- Direct `rev:` is allowed only when Review Tickets or claimed fixes exist.
- Direct `e:` is allowed for explicit browser E2E verification.
- `adv:` must not run first-pass L2+ review without `rp:` output.

## Mandatory L2+ Project-Rule Patterns

These patterns must route to `adviser` Project Rule Check when present in changed code:

- Prisma `findFirst` / `findUnique` with manual null handling and `NotFoundException`
- audit/history/activity `before_value` / `after_value` / `diff` built from normalized DTO/API response values
- code touching or citing `docs/process/rules/backend/DESIGN.md`

Specialists may also must-check scoped variants:
- missing ownership/tenant/actor `where`
- broad or actor-unscoped `updateMany` / `deleteMany`
- transaction/audit/side-effect ordering risk
- request-derived identity trusted across a backend boundary

## Token Discipline

Default review behavior:
- use changed-file list/stat before file reads
- prefer targeted file diffs over full PR diffs
- read exact design sections only when triggered
- stop after blocker-quality evidence is sufficient
- record uninspected risk instead of pretending broad coverage

Default implementation behavior:
- `hq-coder` checks only triggered risk categories
- `hq-coder` hands off L0/L1 QA commands instead of running broad suites by default

## Handoff Vocabulary

Use handoff language instead of cross-layer findings:

- `adv:` for broad first-pass L2+ risk
- `sec:` for auth/trust-boundary risk
- `data:` for persistence/transaction/idempotency risk
- `test:` for regression matrix or test design gap
- `e:` for browser-flow / user-visible E2E gap
- `rev:` for post-fix convergence only

## Quality Bar

Every reviewer output should make clear:
- scope inspected
- route used
- evidence read
- what was not inspected
- whether specialist handoff is needed
- whether the decision is first-pass, specialist, or convergence
