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

## Model Allocation

Default strategy:
- main coordinator -> GPT-5.6 Luna / medium
- hq-coder -> GPT-5.6 Sol / high
- review-planner -> GPT-5.6 Luna / medium
- code-quality-reviewer -> GPT-5.6 Luna / xhigh
- adviser -> GPT-5.6 Luna / xhigh
- reviewer -> GPT-5.6 Luna / high
- test-qa -> GPT-5.6 Luna / xhigh
- e2e-qa -> GPT-5.6 Luna / high
- framework/security/data specialists -> GPT-5.6 Luna / xhigh
- sol-escalation -> GPT-5.6 Sol / high

Reasoning:
- Spend Sol continuously on implementation quality in hq-coder.
- Use narrow Luna agents for normal review work.
- Escalate only the unresolved hard question, not the whole PR, to Sol.
- Do not use Terra as an intermediate default layer.

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

CR never escalates directly to Sol.
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

Adviser may request Sol escalation under the rules below.

### test-qa
Owns:
- unit/service/controller test obligations
- fail-path-first test design
- regression matrix
- targeted test implementation/evidence

Does not own browser/API E2E completeness.
QA does not escalate directly to Sol; route unresolved boundary risk to adviser/sec/data.

### e2e-qa
Owns:
- changed user-flow E2E
- browser/API/module-boundary smoke/regression
- high-value changed-flow negative/auth checks

Does not own unit/service/controller adequacy.
E2E QA does not escalate directly to Sol.

### reviewer
Owns convergence only:
- prior Review Tickets
- claimed fixes
- fix-induced high/medium regression
- required verification evidence

Reviewer does not perform first-pass rediscovery and does not escalate to Sol.
If specialist depth is still required, return the exact unresolved question to the original route.

## Sol Escalation

`sol-escalation` is a complexity escalation path, not another review layer.

Eligible originating roles:
- adviser
- sec-arch
- data-platform
- react-ui-flow
- vue-frontend
- nestjs-backend
- spring-boot

Not eligible for automatic escalation:
- review-planner
- code-quality-reviewer
- req-pl
- test-qa
- e2e-qa
- reviewer
- hq-coder (already runs on Sol)

Escalate only when at least one is true:
- two or more high-risk boundaries interact, such as auth + persistence,
  transaction + external side effect, migration + API contract, or lifecycle + authorization
- two or more plausible merge-relevant hypotheses remain after targeted inspection
- resolving the issue requires tracing more than 3 responsibility boundaries
- requirement/design/code evidence conflicts and the conflict affects correctness
- a Blocker/High finding is plausible but evidence is not strong enough for a safe conclusion
- the required fix would change a public API, persistence semantics, authorization semantics,
  or distributed-execution behavior and the safer boundary is unresolved
- the normal inspection budget is insufficient to establish the causal path

Do NOT escalate for:
- style, naming, formatting, or cleanup
- a local bug already proven by changed-line evidence
- an ordinary test gap
- straightforward CRUD
- a finding whose fix and failure path are already clear
- simply because the diff is large
- missing product decisions that require human/req-pl confirmation

When escalation is needed, the Luna agent must stop broadening its own search and return:

```
ESCALATE_SOL
Role: <originating agent role>
Root cause: <one root cause only>
Trigger: <matched escalation condition>
Scope:
- <files/boundaries already in scope>
Evidence already checked:
- <evidence>
Unresolved decision:
- <exact question Sol must resolve>
Do not repeat:
- <completed checks/findings>
Additional file budget: <default max 5>
```

Parent coordinator behavior:
1. Detect the exact `ESCALATE_SOL` marker.
2. Do not ask the Luna agent to continue deeper.
3. Spawn `sol-escalation`.
4. Pass the handoff unchanged.
5. Wait for the Sol result.
6. Use Sol only for the unresolved escalated question.
7. Do not repeat lower-layer review already completed by Luna.
8. Allow at most one Sol escalation per root cause.

A Sol escalation must preserve the originating role.
It must not convert a narrow security/data/framework question into a broad PR review.

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
Sol escalation is the one exception: it is a continuation of the same unresolved root cause,
not a new review layer.

Direct-use exceptions:
- `cr:` explicit L1.5 check/re-review
- `adv:` explicit focused L2+ review
- `e:` explicit E2E-only verification
- `rev:` prior Review Tickets or claimed fixes already exist
- `sol:` explicit manual high-complexity override

## Duplicate-review Rule

Assign one primary owner per root cause.

- later layers may cite earlier results without re-reviewing them
- reopen only when evidence is missing/contradicted or the current layer owns a distinct consequence
- adviser must not duplicate a specialist ticket for the same root cause
- reviewer must not rediscover unrelated findings during convergence
- sol-escalation must not re-run already completed Luna checks
- only one Sol escalation is allowed per root cause

## Review Budgets

Targets, not hard token guarantees:
- `rp:` 5k-10k
- `cr:` 12k-25k
- `q:` 15k-30k
- `e:` 15k-25k
- `adv:` 20k-40k
- `rev:` 8k-20k
- `sol-escalation:` only the unresolved question, default <=5 additional files

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
