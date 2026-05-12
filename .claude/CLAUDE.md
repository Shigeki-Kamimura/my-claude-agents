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

## Spec-grounded Merge Blocker Rule

🔴 Merge Blocker に分類する場合は、必ず以下を揃える。

- Code Evidence: 該当ファイル・行・実装内容
- Spec Evidence: 該当する設計書・画面仕様・API仕様・権限定義の節番号
- Impact: ユーザー影響 / セキュリティ影響 / データ不整合 / 仕様未達
- Required Fix: merge 前に必要な修正方針
- Verification: 修正後に確認すべき観点

Spec Evidence がない場合でも、security / data integrity / auth boundary / production failure に該当する場合は Merge Blocker として扱ってよい。
ただし、その場合は設計書ではなく production risk を根拠として明示する。

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

## Consistency Check Table

レビュー本文の最後に、必ず整合性チェック表を出す。

| Check | Result | Evidence |
|---|---|---|
| Route/View consistency | ✅/❌ | file/spec |
| API/frontend consistency | ✅/❌ | file/spec |
| Permission boundary | ✅/❌ | file/spec |
| DB/transaction integrity | ✅/❌ | file/spec |
| Tests added/updated | ✅/❌ | file |

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