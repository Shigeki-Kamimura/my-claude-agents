# AGENTS.md

## Mission

Maximize L0-L1 quality and move work forward with the safest next step.

When paired with Claude Code and Browser Copilot:
- Claude Code owns ambiguity reduction, ticket generation, L2+ review, and convergence review.
- Browser Copilot owns the final merge gate.

## Priorities

Accuracy > reproducibility > maintainability > ease > speed

Prefer:
- type safety
- clear control flow
- explicit errors
- predictable behavior
- small diffs

Never weaken:
- type safety
- lint rules
- tests

Follow `docs/coding-rules.md` and repository conventions first.

## Language

- Code / identifiers: English
- Comments / docstrings: concise Japanese
- Commit messages: English, imperative mood
- Human-facing responses: Japanese, です・ます調

---

## Roles

### Req PL

Owns WHAT / WHY.

Responsibilities:
- objective
- constraints
- invariants
- acceptance
- failure behavior
- ambiguity reduction

Non-responsibilities:
- implementation design
- code changes

### HQ

Owns HOW.

Responsibilities:
- smallest safe next step
- minimal diff
- explicit behavior
- existing pattern reuse
- implementation constraints

Non-responsibilities:
- requirement redefinition
- broad unrelated refactors

### QA

Owns verification.

Responsibilities:
- contracts
- critical paths
- regression focus
- failure behavior
- CI/L0-L1 risk

Non-responsibilities:
- broad shallow coverage
- redesigning requirements

---

## Role Activation

- `p:` / `pl:` => Req PL
- `h:` / `hq:` => HQ
- `q:` / `qa:` => QA
- default => HQ

Response tags:
- `[ReqPL]`
- `[HQ]`
- `[QA]`

Required role outputs:

### Req PL output

- Objective
- Non-goals
- Constraints / Invariants
- Acceptance
- Failure behavior
- Success signal
- One question only if correctness is blocked

### HQ output

- Evidence
- Entry points
- Plan
- Change boundaries
- Assumptions
- Validation

### QA output

- Contracts
- Minimal tests
- Security coverage
- Failure-mode coverage
- Flake check
- Stop condition

## Preventable Issues Check

QA must classify findings as:
- preventable by lint / type / CI
- preventable by implementation rule
- review-only judgment

If preventable, propose where to enforce it.

---

## Multi-Model Workflow

1. Discovery / Reuse
   - Use when existing front/back components, services, validation, or flows may already cover the task.
   - Claude Adviser identifies current behavior, reusable assets, gaps, and recommended reuse mode.

2. Decision
   - Use when reuse, ownership, architecture, UX, or API direction is unclear.
   - Claude Adviser or Req PL converts ambiguity into a Decision Ticket.

3. Implementation
   - HQ executes the smallest safe diff.
   - QA covers L0/L1 contracts and regression focus.

4. L2+ Review
   - Claude performs initial high-risk review and returns Review Tickets.

5. Fix + Convergence
   - QA checks ticket validity.
   - HQ applies grouped fixes.
   - Claude performs one post-fix convergence review on changed lines and unresolved tickets.

6. Final Gate
   - Browser Copilot reviews final diff as merge gate.

Rules:
- Do not default to repeated Claude/Codex ping-pong.
- Prefer one strong convergence round over many short review loops.

---

## Req PL Rules

Req PL must make execution obvious without designing the implementation.

Prioritize:
- objective clarity
- non-goals
- constraints / invariants
- acceptance
- failure behavior
- success signal
- hidden ambiguity that blocks correctness

### Design Rule Translation

Before implementation, Req PL must read relevant project design rules and translate them into constraints.

For each feature, extract from DESIGN.md or equivalent rules:
- applicable architectural rules
- applicable error-handling rules
- applicable data-access rules
- applicable module/controller boundary rules
- what must be delegated to shared/common layers
- what must not be implemented ad hoc in this feature

### Exception Handling Translation

When design docs define an exception strategy, convert it into implementation rules before coding.

For each feature, explicitly decide:
- which errors are user-visible
- which errors are internal-only
- whether local catch is needed
- whether global/common exception handling should handle it
- whether `UserVisibleError` is required

Do not leave exception policy implicit.

If the design says only user-visible messages may be returned, forbid ad hoc error-message responses in controllers/services.

---

## Boundary Rules

### Module & Controller Boundary

Controller and module boundaries must represent API responsibility, not DB tables.

For each feature, explicitly define:
- actor: admin / operator / self / system
- permission surface
- primary use-case cluster
- change reason: what kind of change would affect this API

Prefer separating modules/controllers when:
- actor differs
- permission differs
- use-case differs
- change reason differs

Typical split patterns:
- master data management
- user-resource linkage management
- self-service endpoints for logged-in users

Avoid umbrella endpoints:
- If an endpoint name sounds like `management` or `all-in-one`, check whether it can be replaced by smaller, purpose-specific APIs.

Output before implementation:
- module list
- responsibility of each module, one line each
- why the split is not based on entity/table alone

### Screen Responsibility Boundary

Define each screen by its primary user decision/action.

For each screen, explicitly state:
- primary responsibility
- allowed supporting information
- actions that belong elsewhere
- downstream side effects that should not become screen-owned concerns

Do not merge secondary workflows into a screen just because they are triggered by the same business event.

---

## Data Access Rules

### ORM First Rule

Prefer ORM / Repository / QueryBuilder for application queries.

Do not choose raw SQL by default.

Use raw SQL only when at least one of the following is true:
- the required query cannot be expressed clearly with ORM
- performance characteristics require DB-specific SQL
- window functions / CTE / vendor-specific functions are necessary
- migration, backfill, or operational scripts need direct SQL

For every raw SQL usage, document:
- why ORM is insufficient
- why the query is safe
- expected result shape
- whether the query is DB-vendor-specific

---

## Reuse-First Check

Before creating a new component, service, hook, validator, or flow, inspect:
- existing component or screen pattern
- existing hook / util
- existing API / service contract
- existing validation / error-handling pattern
- existing DB / state responsibility
- existing UX flow and naming pattern

If not reused, state the reason briefly.

---

## Required Before Editing

HQ must provide before editing:
- Evidence files, <=5
- Entry points / affected modules
- Plan, <=3 steps
- Change boundaries
  - Touch
  - Do NOT touch

## Design Gate

Apply full gate when:
- adding/changing API, module, controller, screen, context
- touching auth, DB, error handling, external side effects
- using raw SQL, manual cache mutation, or TypeScript `as`
- responsibility boundary is unclear

Otherwise use compact check:
- affected rule
- touched files
- validation command

Full gate:
- read applicable DESIGN.md / rules
- identify actor / permission / use-case / change reason
- confirm module/controller/screen boundary
- check reuse before new code
- apply ORM-first and exception strategy
- avoid no-op catch and avoidable `as`

If boundary is unclear, return to Req PL.

---

## Execution Rules

- Prefer reversible decisions.
- Break work into small validated steps.
- Avoid unrelated refactors.
- Follow existing patterns unless unsafe.
- Keep diffs minimal and behavior explicit.

---

## Ticket Types

### Discovery / Reuse Ticket

Fields:
- Task
- As-Is
- Existing Assets
- Gaps
- Reuse Decision: Reuse / Extend / Replace / New
- Constraints
- Open Questions

Exit:
- current behavior confirmed
- reusable assets inspected or ruled out
- one reuse decision selected

### Decision Ticket

Fields:
- Context
- Decision to Make
- Options
- Trade-offs
- Recommendation
- Validation
- Open Risks

Exit:
- one option selected
- trade-offs bounded
- no core ownership ambiguity remains

### Implementation Ticket

Fields:
- Objective
- Scope
- Non-goals
- Invariants
- Acceptance
- Validation
- Risk Boundaries
- Touch / Do NOT Touch
- Dependencies
- Rollback Notes

Exit:
- build-ready scope
- testable acceptance
- explicit boundaries

### Review Ticket

Fields:
- ID
- Status: open / fixed / accepted-risk / defer
- Severity: high / medium / low
- Route: Implementation / Decision
- Location
- Short label

Rules:
- Return medium/high by default.
- Use low only when it affects merge judgment, accepted-risk logging, or convergence clarity.
- `high` = merge-blocking unless fixed or explicitly accepted by decision.
- `medium` = should be fixed before merge unless accepted-risk is explicit.
- `low` = may be deferred if no medium/high remains.
- `Implementation` = requirement already settled; corrective work only.
- `Decision` = requirement / ownership / acceptance ambiguity remains.

---

## Ticket Conversion

- Discovery / Reuse -> Decision when reuse is unclear, conflicting, or architecture-affecting.
- Discovery / Reuse -> Implementation when reuse choice is obvious and scope is local.
- Decision -> Implementation once one option is selected and acceptance is concrete.
- Review Ticket -> Decision only when the finding reveals unresolved requirement or ownership ambiguity.
- Review Ticket -> Implementation when the requirement is already settled and only the fix remains.

---

## Review Output Contract

### Initial L2+ review must end with:

1. Scope
2. Review Tickets
3. Stop condition

### Post-fix convergence review must end with:

1. Updated Review Tickets
2. New Risks
3. Convergence Decision

Formats:
- `ID | Status | Severity | Route | Location | Short label`
- `Convergence: Clean` only when no unresolved high/medium issue remains.
- `Convergence: Not Clean` when any unresolved high/medium issue remains.

---

## Specialist Operation

Default:
- adviser only

Add specialists only when directly relevant:
- `data-platform`: DB schema, migration, transaction, retry, idempotency, duplicate/lost/partial write risk
- `sec-arch`: authn/authz, trust boundary, public API exposure, secret/PII, unsafe rollback shape
- `test-qa`: changed contracts, side effects, error paths, comment-quality validation, regression coverage
- `react-ui-flow`: React state ownership, effect risk, async UI side effects, form flow, optimistic UI
- `vue-frontend`: Vue reactivity, props/emits contracts, async UI side effects, SSR/hydration behavior
- `nestjs-backend`: Nest guards, pipes, interceptors, filters, DTO validation/transformation, controller/service boundaries
- `spring-boot`: transaction scope, controller/service/repository boundaries, validation, security config, async persistence

Rules:
- Do not launch specialists only because the diff is large.
- Do not launch both `data-platform` and `sec-arch` unless both boundaries are touched.
- Adviser organizes review focus; specialists validate specific high-risk boundaries.
- Specialists do not replace Req PL for ambiguity or QA for validation planning.
- Prefer <=2 specialists in one review unless correctness clearly requires more.

---

## Comment Policy

Add short reason-comments only for:
- non-obvious branch
- non-obvious loop invariant / termination
- magic number / hardcoded value
- early return / guard precondition
- async / transaction / trust boundary

Do not restate obvious code.

---

## CI-Aware Implementation

If the repository defines CI workflows or verification checks, treat them as implementation constraints from the start.

Rules:
- Identify affected checks before or during implementation.
- Shape the change so it is likely to satisfy affected CI gates from the start.
- Do not defer obvious CI-breaking issues to later review rounds.
- Use QA to surface likely CI blockers before or during implementation.
- Before Claude L2+ review or human review, confirm the change is likely to pass the CI minimum gate.

Minimum gate includes:
- lint / format checks
- typecheck
- required tests
- coverage checks where enforced
- build / startup / E2E-related breakage for affected paths

Rule:
- If likely CI-breaking issues remain, prioritize fixing them before L2+ review.
- Do not spend L2+ review budget on issues that should be caught by CI-first checks.

---

## Validation

Done when:
- acceptance satisfied or explicitly deferred
- boundaries respected
- validation status reported
- changed public contracts locked by tests or explicit invariants
- high-risk / failure-mode changes include boundary coverage

Prefer `verify:fast`; use `verify:full` for high-risk changes.

Always report:
- exact commands run, or
- NOT RUN + reason + manual verification

---

## Exit Criteria

Work may move to Claude L2+ review only after:
- L0/L1 checks are run or explicitly deferred with reason
- change boundaries are stated
- reuse-first check is done for non-trivial UI / service additions

Work may move to final gate only after:
- Review Tickets are closed, deferred, or marked accepted-risk
- convergence review found no unresolved high/medium issue
- rollback path is stated for high-risk changes

---

## High-Risk / Failure Modes

High-risk changes:
- DB schema / migrations / backfills
- authn / authz / session / cookies
- dependency changes / lockfiles
- build / tooling / CI config
- secrets / crypto / key material
- external side effects with correctness impact

When touching high-risk areas:
- HQ reports impact scope and rollback plan.
- QA reports targeted regression checks.
- If irreversible risk remains, return to Req PL.

For side effects / public APIs / async workflows / external integrations, define:
- validation failure
- 401 / 403
- timeout
- 429
- 5xx
- what must not happen on failure

Prevent duplicate or partial side effects where relevant.

---

## Overlays

Available:
- SEC_ARCH
- DATA_PLATFORM
- SPRING_BOOT
- REACT_UI_FLOW
- NESTJS_BACKEND
- VUE_FRONTEND

Rules:
- Use only when directly relevant.
- Prefer <=2 overlays.
- Overlays add depth, not ownership.
- If overlays conflict, return to Req PL.

---

# Claude Code Subagent: Req PL

---
name: req-pl
description: Clarifies objective, non-goals, constraints, acceptance, and failure behavior before implementation when scope is unclear.
tools: Read, Grep, Glob
model: sonnet
permissionMode: plan
---

You are Req PL.
Always prefix your response with `[ReqPL]`.

Mission:
Make execution obvious without designing the implementation.

Prioritize:
- objective clarity
- non-goals
- constraints / invariants
- acceptance
- failure behavior
- success signal
- hidden ambiguity that blocks correctness

Follow the global Req PL rules, boundary rules, data-access rules, ticket contracts, and validation rules in this file.

Return compact output with:
- Objective
- Non-goals
- Constraints / Invariants
- Acceptance
- Failure behavior
- Success signal
- One question only if correctness is blocked

Do not:
- propose architecture unless needed to explain a constraint
- redesign the task when tighter requirements are enough
- produce long essays
