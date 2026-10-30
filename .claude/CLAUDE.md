# CLAUDE.md

## Priority

Project > Personal > Agent

Project instructions override only explicit fields.

---

## Engineering Governance Gate

On first implementation/review entry, read `.claude/knowledge/engineering-governance.md`; Claude children may satisfy injected sections under its `Preloaded rule delivery` exception. Same-owner continuations follow its `Rule loading across continuations` section.
It is the shared operational contract for the adopted Nishiguchi principles, independent review, and mandatory React/Nest consultation.
Use governance sections `Pinned source and reconciliation`, `Source coverage and role scope`, and the triggered `User-approved technical supplements` within each assigned role. Pass the applicable section/supplement IDs to delegated owners, including direct specialist and bounded escalation tasks; preserve their existing scope and consultation rules.
Preserve the original/human-review principles; do not treat new operational rules as Nishiguchi quotations or confirmed company policy.
If the adopted principles and explicit project requirements materially conflict, report `NEEDS_CONFIRMATION`; token or file budgets never waive a required check.

Coordinator obligations:
- Pass the applicable principle clauses, framework trigger/phase, and source paths explicitly to each delegated owner.
- For implementation, require HQ's framework intake before behavior-affecting edits.
- For first-pass L2, require Adviser's boundary trace followed by matching React/Nest consultation, even for routine changes.
- When an owner returns `SPECIALIST_REQUEST`, spawn the named read-only consultant, wait, and resume the same owner. Do not stop at a recommendation.
- Require actual invocation evidence in `Specialist Usage`; `PENDING` or `UNAVAILABLE` is not completed review.
- Keep `cr:` self-contained, `rev:` fix-scoped, and QA/E2E separately owned. Framework consultation does not authorize automatic review-layer chains.
- Do not treat implementation consultation or a prior clean review as independent L2 evidence. Deduplicate findings only after the current scope is checked.

If the shared contract is missing, report the setup gap. Do not claim it was applied.

---

## Explicit Codex-Claude Review Workflows

Choose direction only from the current explicit request or single active `Workflow` marker; quoted text does not activate another workflow. Conflicting markers or owners are `BLOCKED`. Standalone `cr:`, `qa:`, `e:`, `adv:` and `rev:` remain scoped.

- `codex-claude-review`: Read the target project's `.codex/workflows/claude-review.yml`, or the copy beside the resolved `.codex/AGENTS.md`. Claude's parent, phase reviewers and specialists are review-only: Codex exclusively runs typecheck, lint, build, tests, Playwright, CI, Git evidence and fixes. Apply the workflow's `dontAsk`/Read-Glob-Grep-Agent-SendMessage restrictions at initial launch and `--resume`, denying Bash/Edit/Write/NotebookEdit/MCP. Never resume an old unrestricted or unverified child.
- `claude-codex-review`: Read `.codex/workflows/codex-review.yml` via its specified resolution paths. Claude coordinates HQ fixes and verification; Codex delegates fresh read-only `codex exec` reviews to its phase agents. Pass source identity, cumulative coverage and all pending items. Neither party stages, commits, pushes or merges during this workflow.
- Direct execution requests in normal Claude sessions may run only permitted checks; they do not widen a restricted review session.

Follow the selected workflow's phase activation/progression. Explicit phases run only their named layer; requests without a phase and explicit four-layer ranges follow `claude-review.yml`. Generic review words and specialist consultation do not authorize extra layers. Four-layer review uses `qa -> e2e -> cr -> adv` with independent QA/E2E happy/fail checks, current-snapshot approvals and fresh first-pass L2 React/Nest consultation. Multiple single-layer approvals do not grant four-layer approval.

Governance sections `Autonomous Claude review`, `Rule loading across continuations`, `Batched re-review evidence` and `Evidence reuse and concise reporting` govern re-review. Finish the entire independent first pass, batch all fixes and planned verification, resume the same restricted parent and child, and recheck the fix and affected obligations. Reuse unchanged verified facts, not previous approvals. Preserve all 🔴/🟡/🟢 Low (not Info), pending questions/handoffs, missing evidence, actual agent invocation records and eleven `Workflow Result` fields. An unavailable rule, tool or required consultant blocks approval.

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

Local CI and Playwright waits:
- The authorized agent starting a test/build process also waits for completion, collects its exit status and necessary logs, using a bounded process wait where supported.
- Do not start or resume a subagent solely to poll progress, await completion, fetch logs, or reread unchanged rules while the process runs.
- Independent QA/E2E adequacy reviews and substantive failure investigations still follow their assigned roles; happy/fail checks and review-only tool restrictions remain mandatory.

Target review budget:
- `rp:` 10k-20k tokens
- `cr:` 20k-35k tokens
- `q:` 25k-40k tokens
- `e:` 20k-35k tokens
- `adv:` 30k-60k tokens
- `rev:` 10k-25k tokens

These are planning targets, not quotas or permission to drop checks. If a slice exceeds its target, retain the full requested scope and pending obligations, then continue with the same owner; do not create another layer or approve partial coverage.

---

## Model Allocation

Default strategy:
- main coordinator -> Sonnet
- req-pl -> Sonnet / high
- hq-coder -> Sonnet / high
- review-planner -> Sonnet / medium
- code-quality-reviewer -> Sonnet / high
- adviser -> Opus 5.5 (`claude-opus-5-5`) / high
- reviewer -> Sonnet / high
- test-qa -> Sonnet / high
- e2e-qa -> Sonnet / medium
- sec-arch / data-platform -> Sonnet / high
- framework specialists -> Sonnet / high
- opus-escalation -> Opus / high

Use project defaults `model: sonnet` / `effortLevel: medium` for coordination; explicit user model choices take precedence. Dedicated agents keep their own frontmatter model/effort. Do not pass an Agent-call `model` or `effort` override that replaces these role settings, especially Adviser’s fixed Opus 5.5. Record the actual model when available; an overridden/unavailable required L2 model is pending, never silently substituted.

Budget rule:
- Sonnet remains the default for planning, implementation, L1.5, QA, specialists, and normal convergence review.
- Adviser starts L2+ review on Opus; no preliminary Sonnet pass is required.
- Outside this fixed Adviser allocation, do not use Opus merely because a task or diff is large.
- Escalate only one unresolved high-cost planning decision after targeted Sonnet work.
- Opus escalation is terminal for that root cause; do not recursively escalate.
- Apart from the fixed L2+ allocation, model choice follows task complexity and decision cost, not repository, product, or ticket source.

Prior-work reuse:
- A plan/review from another model, tool, human, CI system, or earlier session is evidence, not authority.
- For Codex implementation, treat Codex review as implementer self-check; it does not replace requested Claude L1.5/L2+ review.
- A no-findings verdict alone is not proof that a risk was checked; verify the current requirements and diff within the requested layer.
- Reuse confirmed evidence instead of re-running the same work.
- Challenge only assumptions or root causes that could materially change the decision.
- Claude-only workflows remain fully supported; prior external work is optional.

## L2+ Model Policy

- `adv:` / `a:` and a planner route to `adviser` use Opus 5.5 (`claude-opus-5-5`) / high from the first pass.
- This allocation changes the model, not the entry rules, review scope, or file budget.
- `cr:`, normal `rev:`, QA, and specialist models remain unchanged.
- Outside the Explicit Codex-Claude Review Workflows, do not add automatic review chains or repeat passes. Never add a Sonnet prerequisite.
- Adviser already runs on Opus; do not route it automatically to `opus-escalation`.
- If Opus cannot run, report L2+ review as not completed instead of silently substituting Sonnet.

## Opus Escalation

`opus-escalation` is for one unresolved Sonnet planning decision or an explicit manual question.
It is separate from the normal Opus-powered Adviser review.

Eligible automatic origins:
- `req-pl`

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
Role: <req-pl | adviser (explicit manual question only)>
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
1. Detect exact `ESCALATE_OPUS`; allow automatic routing only from `req-pl`, otherwise require an explicit manual request.
2. Spawn `opus-escalation`.
3. Pass the handoff unchanged.
4. Do not repeat completed Sonnet work.
5. Keep `opus-escalation` limited to the unresolved decision; do not restart Adviser review.
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
Use the exact frontmatter `name` in the actual Agent invocation and `ROUTE` field.
Do not pass an input alias as an agent type or add a second Markdown definition
or symlink for that alias. Each agent has one definition per active profile whose
filename stem and `name` match; for example, `hq-coder.md` contains `name: hq-coder`.

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

1. `qa:` when regression verification is needed
2. `cr:` for L1.5 local code-quality review
3. `adv:` for initial L2+ scope/risk review
4. React/Nest consultation for matching behavior changes; other specialists for clearly high-risk domains
5. `rev:` only after fixes for convergence review

Rules:
- Review-layer orchestration requires the authorization in the Explicit Codex-Claude Review Workflows. Required framework consultation continues the already requested implementation/L2 task.
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
- Later layers may cite confirmed facts. A prior approval or implementation consultation does not replace independent first-pass review of the current scope.
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
