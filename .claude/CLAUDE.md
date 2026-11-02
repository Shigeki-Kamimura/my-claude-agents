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

### Re-review direction

- `codex-claude-review`: Resume the same restricted Claude parent/child for the same phase only, after batch fixes and planned verification. Keep the workflow's secure-resume exceptions.
- `claude-codex-review`: Start a fresh read-only `codex exec` every round. Do not use `exec resume` or `--last`; carry the cumulative coverage and all pending findings.

Standalone reviews use their own continuation rules.

Apply governance sections `Autonomous Claude review`, `Rule loading across continuations`, `Batched re-review evidence` and `Evidence reuse and concise reporting` within their stated scopes. Finish the independent first pass and recheck fixes and affected obligations. Reuse unchanged verified facts, not previous approvals. Preserve all 🔴/🟡/🟢 Low (not Info), pending questions/handoffs, missing evidence, actual agent invocation records and eleven `Workflow Result` fields. An unavailable rule, tool or required consultant blocks approval.

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

Claude review intake and consultation:
- Resolve repository, actual base/head, working-tree inclusion, requirements and active rule identity from available sources. Ask only for a missing fact that changes scope or judgment; unfilled templates or missing usage readings alone do not block intake. Start only the requested role and required consultation. The standard operating decision is recorded in docs/claude-review-policy.md; this coordinator reference is not an extra reviewer reading assignment.
- Apply governance `Claude role-scoped intake` and `Review objective and evidence`. Pass the objective, source identity, applicable original section IDs and exclusions once; each owner independently inspects its scope. For active codex-claude-review, the coordinator reads the full workflow and supplies its path/version, mode/phase and role_sections keys. Children read their complete assigned originals/exceptions; summaries or Codex AGENTS are not substitutes. Preserve reverse-workflow rules.
- Verify actual injected rule delivery against current sources; retain injected/read/missing sections in Rules loaded. Pass native Read guidance: explicit offset/limit when supported, initially at most 100 lines (fewer for long lines), completing all required ranges/exceptions. Batch only outputs that fit; recover missing ranges after truncation. Preserve whole-file requirements; no script/tool-permission workaround.
- After Adviser's initial boundary trace, batch decision-specific React/Nest questions. Run independent consultations concurrently when the permitted tool supports it; dependent questions wait. Preserve role model/effort and restrictions. Direct Agent calls need no run_in_background parameter if absent from the schema. When direct calls are unavailable, obtain SPECIALIST_REQUEST results and return accessible originals/IDs together once to the same Adviser.
- Use completion notifications or permitted waits, never status polling or waiting agents. Launch acknowledgement is not evidence. Retain unavailable capability and pending obligations. Adviser integrates scoped answers; the parent relays verdict and remaining items without repeating the review. Keep original consultation records, advice disposition, all open IDs and required native/Workflow Result fields.

Local CI and Playwright waits:
- The authorized agent starting a test/build process also waits for completion, collects its exit status and necessary logs, using a bounded process wait where supported.
- Never launch a separate subagent solely to await completion, poll progress, fetch logs, or reread unchanged rules. An existing execution owner may continue/resume to finish its run.
- Independent QA/E2E adequacy reviews and substantive failure investigations still follow their assigned roles; happy/fail checks and review-only tool restrictions remain mandatory.

Review budget trial (user-approved 2026-11-02):
- Target about 30 percentage points of the Claude Pro five-hour usage window for one requested review, including coordinator and all reviewers/consultants. This is a planning target, not a token allowance, per-agent target or instruction to consume unused capacity.
- Record the account's displayed usage before and after, timestamps and reset/window identity when available. Take a midpoint reading only when already available without interrupting reviewers. Do not invent a telemetry endpoint or delegate quota polling. The human coordinator may supply these readings.
- Compare readings only in the same window. Concurrent unrelated usage makes attribution CONFOUNDED; a reset makes it INCOMPARABLE. Missing readings mean NOT_MEASURED. Never convert token totals or dollar costs into subscription percentages, or claim the target passed from a token count.
- At an observed approach to the target, finish the current bounded investigation and report coverage, remaining obligations and the next bounded continuation. A budget-limited result stays PARTIAL/DEFER unless confirmed blockers require REQUEST_CHANGES. Never silently omit checks, close findings, downgrade severity, replace mandatory specialists or lower model/effort to hit the target.
- Start only the requested layer and its required consultants. Reuse the same owners for repair; batch fixes and verification. After three repair rounds, report the unresolved cause and required decision before another unbounded cycle. Preserve stricter workflow continuation/approval rules and all open obligations.
- The coordinator uses docs/claude-review-trial.md in the shared configuration repository for the experiment record, outside the reviewer's discovery input; it is not a required project-local file or reviewer reading assignment. A normal review needs no additional report per read or consultant. Quality and time are evaluated alongside usage; source/rule identity and independent first-pass requirements still apply.

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
- Re-review within an ongoing repair cycle outside `claude-codex-review`: resume the original owner. The reverse workflow uses fresh Codex rounds as defined above. An explicit `rev:` request starts separate `reviewer` convergence.
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
