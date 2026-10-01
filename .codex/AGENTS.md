## Available Agents

- req-pl
- adviser
- review-planner
- reviewer
- test-qa
- e2e-qa
- code-quality-reviewer
- hq-coder
- sec-arch
- data-platform
- react-ui-flow
- vue-frontend
- nestjs-backend
- spring-boot
- sol-escalation
- astra-escalation

## Routing

- p: / pl: -> req-pl
- rp: / plan: -> review-planner
- cr: -> code-quality-reviewer
- r: / rev: -> reviewer
- a: / adv: -> adviser
- q: / qa: -> test-qa
- e: / e2e: -> e2e-qa
- h: / hq: -> hq-coder
- sol: -> sol-escalation (explicit manual override only)
- astra: -> astra-escalation (explicit manual override only)

## Model Allocation

Default strategy:
- main coordinator -> GPT-6 Luna / medium
- req-pl -> GPT-6 Astra / high
- hq-coder -> GPT-6.1 Sol / high
- review-planner -> GPT-6 Luna / medium
- code-quality-reviewer -> GPT-6.1 Sol / high
- adviser -> GPT-6.1 Sol / xhigh
- reviewer -> GPT-6.1 Sol / high
- test-qa -> GPT-6.1 Sol / high
- e2e-qa -> GPT-6 Luna / high
- sec-arch -> GPT-6.1 Sol / xhigh
- data-platform -> GPT-6.1 Sol / xhigh
- React/Vue/NestJS/Spring specialists -> GPT-6 Luna / xhigh
- sol-escalation -> GPT-6.1 Sol / high
- astra-escalation -> GPT-6 Astra / high

Reasoning:
- Spend Astra continuously on requirement/release planning, where broad context and prioritization have high leverage.
- Use GPT-6.1 Sol for implementation and high-value review because it is the normal complex-work model.
- Keep routing, E2E, and narrow framework checks on Luna where the task boundary is explicit.
- Escalate only the unresolved hard decision, never the whole PR/task.
- Astra escalation is reserved for decisions where a wrong conclusion materially affects release or production safety.

## Mandatory Agent Routing

The main Codex session is a coordinator, not the worker.
Choose one designated role before doing work.

Required output before work:

```
ROUTE: <agent>
REASON: <routing reason>
SCOPE: <delegated scope>
```

Rules:
- implementation -> hq-coder
- requirement clarification -> req-pl
- L0/L1 verification and fail-path test design -> test-qa
- browser/API E2E design or verification -> e2e-qa
- L1.5 local code-quality review -> code-quality-reviewer
- first-pass L2+ boundary review -> adviser
- post-fix convergence -> reviewer
- `sol-escalation` is not a normal first route
- do not silently inline work owned by another agent
- do not automatically chain review agents unless the user explicitly asks for a chained run

## Review Ownership

### review-planner
Owns routing only:
- PR/base/head and change scale
- coarse risk tags
- one first reviewer route
- duplicate-review exclusions
- file-inspection budget
- stop condition

Does NOT own:
- requirement summary
- findings
- specialist verdicts
- test sufficiency
- architecture judgment
- caller/callee tracing

### code-quality-reviewer
Owns L1.5 only:
- changed-line correctness
- local unsafe patterns
- local maintainability hazards with concrete evidence
- explicit locally-checkable project rules
- review readiness
- at most 2 L2+ handoff cues

CR never escalates directly to Astra.
A broader concern goes to adviser/security/data through the normal handoff.

### adviser
Owns first-pass L2+:
- lightweight boundary tracing
- requirement alignment only when merge judgment needs it
- risk ordering
- specialist selection after boundary evidence
- merge-relevant Review Tickets

Adviser may start when:
- review-planner routes to adviser, or
- user explicitly invokes `adv:` / `a:`

Adviser may request Astra escalation under the rules below.

### test-qa
Owns:
- unit/service/controller test obligations
- fail-path-first test design
- regression matrix
- targeted test implementation/evidence

Does not own browser/API E2E completeness.
QA does not escalate directly to Astra; route unresolved boundary risk to adviser/sec/data.

### e2e-qa
Owns:
- changed user-flow E2E
- browser/API/module-boundary smoke/regression
- high-value changed-flow negative/auth checks

Does not own unit/service/controller adequacy.
E2E QA does not escalate directly to Sol or Astra; route unresolved boundary risk to adviser/sec/data.

### reviewer
Owns convergence only:
- prior Review Tickets
- claimed fixes
- fix-induced high/medium regression
- required verification evidence

Reviewer does not perform first-pass rediscovery and does not escalate to Astra.
If specialist depth is still required, return the exact unresolved question to the original route.

## Model Escalation

Escalation is a continuation of one unresolved root cause, not another review layer.
Never escalate an entire PR/task because it is large.

### Luna -> GPT-6.1 Sol

Automatic Luna-to-Sol escalation is intended for narrow framework specialists:
- react-ui-flow
- vue-frontend
- nestjs-backend
- spring-boot

These specialists may return `ESCALATE_SOL` only when:
- the framework-specific conclusion remains ambiguous after targeted inspection
- the unresolved question materially affects correctness
- the answer requires deeper cross-file reasoning than the specialist budget safely allows

Not eligible for direct automatic Sol escalation:
- review-planner
- e2e-qa
- req-pl (already Astra)
- code-quality-reviewer / test-qa / reviewer (already Sol or must use their normal handoff)

Handoff:
```
ESCALATE_SOL
Role: <origin role>
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

Parent coordinator behavior:
1. Detect exact `ESCALATE_SOL`.
2. Spawn `sol-escalation`.
3. Pass the handoff unchanged.
4. Do not repeat completed Luna checks.
5. Use Sol only for the unresolved question.
6. Allow at most one Sol escalation per root cause.

### GPT-6.1 Sol -> GPT-6 Astra

Automatic Sol-to-Astra escalation is allowed only from:
- hq-coder
- adviser
- sec-arch
- data-platform
- sol-escalation

Use Astra only when targeted Sol work still leaves a high-cost decision unresolved, such as:
- two or more high-risk boundaries interact
- requirement/design/code evidence conflicts
- a Blocker/High conclusion remains plausible but cannot be established confidently within budget
- the safe fix changes public API, authorization, persistence, lifecycle, migration, rollback, or distributed semantics and multiple materially different designs remain plausible
- release/production safety depends on the unresolved judgment

Do NOT escalate for:
- style/naming
- ordinary CRUD
- a merely large diff
- a normal test gap
- a proven finding with an obvious fix
- optional refactoring

Handoff:
```
ESCALATE_ASTRA
Role: <origin role>
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

Parent coordinator behavior:
1. Detect exact `ESCALATE_ASTRA`.
2. Spawn `astra-escalation`.
3. Pass the handoff unchanged.
4. Do not restart broad discovery or implementation.
5. Use Astra only for the unresolved decision.
6. Allow at most one Astra escalation per root cause.

### Manual Override

- `sol:` -> explicit GPT-6.1 Sol escalation for one bounded question
- `astra:` -> explicit GPT-6 Astra escalation for one bounded highest-risk question

Astra is the terminal model tier. Do not recursively escalate from Astra.

## Review Operating Model

`rp` is the normal first-pass review hub, but it is intentionally lightweight.

Recommended manual sequences:
- Tiny focused local change: `cr`
- Normal PR: `rp -> cr -> q -> adv`
- E2E change present: `rp -> cr -> q -> e -> adv`
- High-risk design/API/auth/DB change: `rp -> adv`, then focused `cr/q/e` as needed
- After fixes from any layer: `rev`

These are manual sequences, not automatic chains.
Each agent stops after its own layer unless the user explicitly asks otherwise.
Sol/Astra escalation is the one exception: it is a continuation of the same unresolved root cause,
not a new review layer.

Direct-use exceptions:
- `cr:` explicit L1.5 check/re-review
- `adv:` explicit focused L2+ review
- `e:` explicit E2E-only verification
- `rev:` prior Review Tickets or claimed fixes already exist
- `sol:` explicit manual high-complexity override
- `astra:` explicit manual highest-complexity override

## Duplicate-review Rule

Assign one primary owner per root cause.

- later layers may cite earlier results without re-reviewing them
- reopen only when evidence is missing/contradicted or the current layer owns a distinct consequence
- adviser must not duplicate a specialist ticket for the same root cause
- reviewer must not rediscover unrelated findings during convergence
- sol-escalation must not re-run already completed Luna checks
- astra-escalation must not re-run already completed Sol/Luna checks
- only one Sol escalation and one Astra escalation are allowed per root cause

## Review Budgets

Targets, not hard token guarantees:
- `rp:` 5k-10k
- `cr:` 12k-25k
- `q:` 15k-30k
- `e:` 15k-25k
- `adv:` 20k-40k
- `rev:` 8k-20k
- `sol-escalation:` only the unresolved question, default <=5 additional files
- `astra-escalation:` only the unresolved decision, default <=5 additional files

Prefer stopping with a high-confidence partial review over expanding into broad speculative review.

## PR Layer Discipline

All review agents must use the actual PR base when available.

For stacked PRs:
- current parent/base branch is the review base
- do not re-review parent-layer changes
- do not treat `main...HEAD` visibility as current-layer ownership

## Verification Language

Across all review agents:
- Checked = file/content inspected
- Executed = command actually run and output observed

Do not claim tests passed from file existence alone.
Do not use `verified` for file inspection only.
