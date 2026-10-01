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

Default strategy:
- main coordinator -> Sonnet
- req-pl -> Sonnet / high
- hq-coder -> Sonnet / high
- review-planner -> Sonnet / medium
- code-quality-reviewer -> Sonnet / high
- adviser -> Sonnet / high
- reviewer -> Sonnet / high
- test-qa -> Sonnet / high
- e2e-qa -> Sonnet / medium
- sec-arch / data-platform -> Sonnet / high
- framework specialists -> Sonnet / high
- opus-escalation -> Opus / high

Budget rule:
- Sonnet is the default worker for normal planning, implementation, and review.
- Do not use Opus merely because a task or diff is large.
- Escalate only one unresolved high-cost decision after targeted Sonnet work.
- Opus escalation is terminal for that root cause; do not recursively escalate.
- Model choice follows task complexity and decision cost, not repository, product, workflow stage, or ticket source.

Prior-work reuse:
- A plan/review from another model, tool, human, CI system, or earlier session is evidence, not authority.
- Reuse confirmed evidence instead of re-running the same work.
- Challenge only assumptions or root causes that could materially change the decision.
- Claude-only workflows remain fully supported; prior external work is optional.

## Opus Escalation

Opus is an escalation tier for one unresolved decision, not a normal review layer.

Eligible automatic origins:
- `req-pl`
- `adviser`

Typical triggers:
- authoritative requirement/design sources materially conflict
- multiple high-risk boundaries interact and the causal path remains ambiguous
- a high-impact decision has multiple materially different valid options after targeted Sonnet inspection
- compatibility, migration, rollback, authorization, persistence, or cross-system behavior cannot be decided safely within the normal budget
- a wrong conclusion would cause substantial rework or correctness risk

Do not escalate for:
- style or naming
- ordinary CRUD
- straightforward task splitting
- a normal missing test
- merely large diffs or issue lists
- missing information that should become an open question

Handoff:
```
ESCALATE_OPUS
Role: <req-pl | adviser>
Root cause: <one root cause>
Trigger: <matched condition>
Scope:
- ...
Evidence already checked:
- ...
Unresolved decision:
- ...
Do not repeat:
- ...
Additional file budget: <default max 5>
```

Coordinator behavior:
1. Detect exact `ESCALATE_OPUS`.
2. Spawn `opus-escalation`.
3. Pass the handoff unchanged.
4. Do not repeat completed Sonnet work.
5. Use Opus only for the unresolved decision.
6. Allow at most one Opus escalation per root cause.

Manual override:
- `o:` / `opus:` -> one bounded Opus escalation question

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
- `o:` / `opus:` -> `opus-escalation` (explicit bounded override only)

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
- Normal PR: `rp -> cr -> q -> adv`
- E2E changes: `rp -> cr -> q -> e -> adv`
- High-risk API/auth/data/design change: `rp -> adv`, then focused specialists as needed
- Re-review after fixes: `rev`
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

## Issue / Ticket Reference

Issue and ticket systems are project-specific.

Rules:
- Use the source explicitly named by the user or project instructions.
- A local ticket cache, Backlog, GitHub Issues, Jira, or another tracker may be used when configured.
- Do not assume one tracker or local path is canonical across repositories.
- If the referenced ticket/project is ambiguous and cannot be resolved from current context, ask only when the ambiguity blocks safe work.
- A more recent explicit user instruction overrides stale ticket text.

