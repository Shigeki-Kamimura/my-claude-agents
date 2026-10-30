# AGENTS.md

## Priority

Project > Personal > Agent. Project instructions override only explicit fields.

## Shared entry point

This root file provides the minimal common entry point. Load the platform contract and project rules before implementation or review:
- Codex: `.codex/AGENTS.md` and the active `.codex/workflows/*.yml`.
- Claude Code: `.claude/CLAUDE.md` or `.claude-company/CLAUDE.md` and the active workflow.
- Shared rules: `.claude/knowledge/engineering-governance.md`, applicable `human-review-patterns.md` sections, and actual project requirements, including exceptions.

Use the platform's agent model/effort definitions; do not infer a model from this file. A missing, conflicting or unreadable required rule stays pending; brevity never waives required checks.

Choose `codex-claude-review` or `claude-codex-review` only from the current user request or active `Workflow` marker. Quoted requests do not activate workflows; conflicts are `BLOCKED`. Standalone `cr:`, `qa:`, `e:`, `adv:` and `rev:` retain their scoped behavior. Only expressly authorized four-layer review runs `qa -> e2e -> cr -> adv`; QA/E2E check happy/fail, L2 independently obtains relevant React/Nest consultation, and all approvals must cover the final snapshot.

In `codex-claude-review`, Claude reviewers/consultants remain read-only; Codex owns edits, tests, CI and Git evidence. In `claude-codex-review`, Codex reviewers/consultants remain read-only; Claude owns implementation and verification. The actual workflow governs CLI restrictions, single-layer progression, independent first passes and eleven-field results; never widen a restricted session through another agent.

Within the same review owner/phase, reuse verified unchanged rules and evidence after checking the relevant source identity. Batch repairs and verification, and resume the original parent/child when supported. New phase owners inspect their scope independently. Keep all unresolved 🔴/🟡/🟢 Low findings (not Info), questions, handoffs and missing checks open until their owner confirms closure.

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
- `rp:` / `plan:` -> `review-planner`
- `h:` / `hq:` -> `hq-coder`
- `cr:` -> `code-quality-reviewer`
- `r`: / `rev:` -> `reviewer` (convergence only)
- `q:` / `qa:` -> `test-qa`
- `a:` / `adv:` -> `adviser` (L2+ review routing)
- `e:` / `e2e:` -> `e2e-qa`
- `o:` / `opus:` -> `opus-escalation` (explicit bounded override only)

These are input aliases, not separate registered agents. Normalize an explicit
agent request such as `hq`, `pl`, or `qa` (with or without `:`) to the canonical
name above before spawning it. `rp` / `plan` always routes to `review-planner`.
Use the canonical name in the actual invocation and `ROUTE` field. Do not pass
an input alias as an agent type or add a second TOML/symlink for that alias.
Each Codex agent has one definition whose filename and `name` match; for example,
`hq-coder.toml` contains `name = "hq-coder"`.

Default without prefix:
- answer directly when the task is simple
- route when role ownership is clear
- ask at most one blocking question

---

## Mandatory Subagent Routing

The main Codex session must act as router/coordinator only.

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

1. `qa:` when regression verification is needed
2. `cr:` for L1.5 local code-quality review
3. `adv:` for initial L2+ scope/risk review
4. specialists only for clearly high-risk domains
5. `rev:` only after fixes for convergence review

Rules:
- Do not chain review agents without the authorization in the Explicit Codex-Claude Review Workflows.
- A standalone `cr:` never starts `adv:` automatically.
- Do not send first-pass PR review to `reviewer`.
- Each review command owns only its scoped review layer.
- `cr:` runs only `code-quality-reviewer`.
- `adviser` is used only when the user explicitly uses `adv:` / `a:` or review-planner routes L2+ review.
- `reviewer` is used only for convergence after prior Review Tickets or claimed fixes.

## Review Operating Model

`rp` is the lightweight review hub.

`rp` decides only:
- PR/base/head and rough change scale
- coarse risk tags
- first reviewer route
- duplicate-review exclusions
- file-inspection budget
- stop condition

`rp` does NOT decide:
- requirement correctness
- review findings
- specialist verdicts
- test sufficiency
- architecture correctness
- caller/callee execution paths

Standard flows:
- These are recommended manual sequences, not automatic chains.
- Agents stop after their own layer unless explicitly instructed otherwise.
- Tiny local change: direct `cr:`
- Normal PR: `rp -> q -> cr -> adv`
- E2E changes: `rp -> q -> e -> cr -> adv`
- High-risk API/auth/data/design change: `rp -> adv`, then focused specialists as needed
- Re-review within an ongoing repair cycle: resume the original owner. An explicit `rev:` request starts separate `reviewer` convergence.
- Prior plan/review available: pass it as evidence to the relevant agent; do not restart every layer

Layer split:
- `cr`: local implementation quality and review readiness
- `q`: unit/service/controller test adequacy and failure-mode evidence
- `e`: E2E/integration adequacy
- `adv`: L2+ boundary review and high-risk assumption challenge
- `rev`: prior Review Tickets / claimed fixes only

Duplicate-review rule:
- Once a layer has proven a topic, later layers may cite it without re-evaluating it.
- Re-open only when evidence is missing/contradicted, merge judgment depends on unresolved evidence,
  or the current layer owns a distinct consequence.
- Different-model review should seek independent failure evidence, not produce a second copy of the same review.

rp size rule:
- `rp` creates the review route only.
- `rp` must not perform code review, test adequacy review, E2E review, L2+ judgment, or full-file deep inspection.
- If routing requires deep reading, route that uncertainty to the target reviewer instead.

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
- `.Codex/knowledge/human-review-patterns.md`

Required review-pattern section for design alignment:
- `## Design Document Alignment`

For changed API-to-consumer behavior or supplied review tickets, read only the matching shared knowledge sections:
- `## API-to-UI Semantics`
- `## Reachable Failure Evidence`
- `## Cross-Layer Regression Cases`
- `## Scope and Unresolved Blockers`

Apply these within the selected agent's ownership and existing file budget. Knowledge does not authorize automatic review chains or a broader review.

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

## Issue / Ticket Reference

Issue and ticket systems are project-specific.

Rules:
- Use the source explicitly named by the user or project instructions.
- A local ticket cache, Backlog, GitHub Issues, Jira, or another tracker may be used when configured.
- Do not assume one tracker or local path is canonical across repositories.
- If the referenced ticket/project is ambiguous and cannot be resolved from current context, ask only when the ambiguity blocks safe work.
- A more recent explicit user instruction overrides stale ticket text.
