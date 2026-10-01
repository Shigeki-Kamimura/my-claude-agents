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

Target review budget:
- `rp:` 10k-20k tokens
- `cr:` 20k-35k tokens
- `q:` 25k-40k tokens
- `e:` 20k-35k tokens
- `adv:` 30k-60k tokens
- `rev:` 10k-25k tokens

If a scoped review is likely to exceed its target, reduce scope before reading more files and state what was left for another layer.

---

## Model Allocation

Use Opus only where broad judgment has the highest leverage:
- `req-pl` -> Opus / high
- `adviser` -> Opus / high

Use Sonnet for normal execution and bounded review:
- main coordinator
- `hq-coder`
- `review-planner`
- `code-quality-reviewer`
- `reviewer`
- `test-qa`
- `e2e-qa`
- `sec-arch`
- `data-platform`
- framework specialists

Budget rule:
- Do not upgrade another agent to Opus merely because the task is large.
- Opus agents must use targeted reads and stop conditions.
- Do not automatically chain Opus agents.
- With Codex/Astra/Sol output available, use Claude Opus as an independent challenger/reviewer,
  not as a second full execution of the same work.

Cross-model operating mode:
- Codex may remain the primary planner/implementer when available.
- `req-pl` challenges release scope, task decomposition, assumptions, and missing prerequisites.
- `adviser` provides independent L2+ cross-model review for high-risk boundaries.
- Sonnet agents handle implementation, local review, tests, convergence, and framework-specific checks.
- In Claude-only projects, `req-pl` may act as the primary planner when no prior plan exists.

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
- `cr:` runs only `code-quality-reviewer`.
- `adviser` is used only when the user explicitly uses `adv:` / `a:` or review-planner routes L2+ review.
- `reviewer` is used only for convergence after prior Review Tickets or claimed fixes.

## Review Operating Model

`rp` is the lightweight review hub.

`rp` must decide only:
- PR/base/head and rough change scale
- coarse risk tags
- first reviewer route
- duplicate-review exclusions
- file-inspection budget
- stop condition

`rp` must NOT decide:
- requirement correctness
- review findings
- specialist verdicts
- test sufficiency
- architecture correctness
- caller/callee execution paths

Standard flows:
- These are recommended manual sequences, not automatic chains.
- Agents must stop after their own layer and wait for the user's next command unless explicitly instructed otherwise.
- Tiny PR: direct `cr:` is allowed for formatting, small refactors, one-test additions, or obvious bug fixes
- Normal PR: `rp -> cr -> q -> adv`
- E2E changes present: `rp -> cr -> q -> e -> adv`
- High-risk design/API/auth/DB change: `rp -> adv`, then focused `cr/q/e` only as needed
- Re-review after fixes: `rev`
- Cross-model review: pass existing Codex findings/plan to `req-pl` or `adv` as challenge input; do not restart all layers

Layer split:
- `cr`: lightweight implementation smell and review-readiness check
- `q`: unit/service/controller spec adequacy only
- `e`: E2E/integration adequacy only
- `adv`: Opus L2+ boundary review and cross-model challenge
- `rev`: prior Review Tickets / claimed fixes only

Duplicate-review rule:
- Once a layer has covered a topic, later layers may cite the result but must not re-evaluate it unless merge judgment depends on unresolved evidence.
- Later layers may re-open a topic only when evidence is missing or contradicted, merge judgment depends on unresolved evidence, or the current layer owns a distinct consequence.
- Cross-model review should challenge high-risk assumptions, not reproduce already-proven low-risk findings.

rp size rule:
- `rp` creates the review route only.
- `rp` must not perform code review, test adequacy review, E2E review, L2+ judgment, or full-file deep inspection.
- If routing starts to require deep reading, route that uncertainty to the target reviewer instead.

## QA Boundary

- `test-qa` owns changed-test-file adequacy, unit/integration regression planning, and high-signal verification gaps.
- `test-qa` must not expand into E2E/integration scenario completeness, non-functional risk hunts, or coverage percentage scoring.
- `e2e-qa` owns changed E2E/integration adequacy: browser E2E user flows, backend controller/API e2e, auth/role behavior, and major fail paths crossing module or HTTP boundaries.
- `e2e-qa` must not inspect unit/service/controller spec adequacy or re-evaluate test-qa findings.
- Use `e2e-qa` when behavior must be proven through browser-level user actions or HTTP/module-boundary E2E/integration tests.
- Prefer structuring E2E by `read` / `write` / `rules` / `auth`.
- Split browser tests by dominant risk axis instead of feature size alone.
- Split or add files before a single E2E spec exceeds 400 lines.

## Review Entry Rule

First-pass review normally starts with `rp:`, but direct focused review is allowed.

Direct use exceptions:
- `cr:`: explicit L1.5 check or re-check
- `adv:` / `a:`: explicit focused L2+ review
- `rev:`: Review Ticket or claimed fix already exists
- `e:`: explicit E2E-only verification

When `rp:` output exists, downstream agents must honor its scope, exclusions, file budget, and stop condition.
When `adv:` is invoked directly, Adviser must resolve the real PR base and apply the same bounded-inspection discipline.
Do not run a hidden full review-planner pass inside Adviser.

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
