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

## Routing

- p: / pl: -> req-pl
- rp: / plan: -> review-planner
- cr: -> code-quality-reviewer
- r: / rev: -> reviewer
- a: / adv: -> adviser
- q: / qa: -> test-qa
- e: / e2e: -> e2e-qa
- h: / hq: -> hq-coder

## Model Allocation

Default strategy:
- main coordinator -> GPT-5.6 Terra / medium
- hq-coder -> GPT-5.6 Sol / high
- review-planner -> GPT-5.6 Luna / medium
- code-quality-reviewer -> GPT-5.6 Terra / high
- adviser -> GPT-5.6 Terra / high
- reviewer -> GPT-5.6 Terra / high
- test-qa -> GPT-5.6 Terra / high
- e2e-qa -> GPT-5.6 Terra / medium
- framework/security/data specialists -> GPT-5.6 Terra / high

Reasoning:
- Spend the strongest fixed model on implementation quality before review debt is created.
- Keep routing cheap and bounded.
- Use multiple focused Terra review layers instead of placing Sol on every reviewer.
- If a rare high-risk review needs Sol, run it as an explicit exceptional review rather than changing the normal reviewer fleet.

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

### test-qa
Owns:
- unit/service/controller test obligations
- fail-path-first test design
- regression matrix
- targeted test implementation/evidence

Does not own browser/API E2E completeness.

### e2e-qa
Owns:
- changed user-flow E2E
- browser/API/module-boundary smoke/regression
- high-value changed-flow negative/auth checks

Does not own unit/service/controller adequacy.

### reviewer
Owns convergence only:
- prior Review Tickets
- claimed fixes
- fix-induced high/medium regression
- required verification evidence

Reviewer does not perform first-pass rediscovery.

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

Direct-use exceptions:
- `cr:` explicit L1.5 check/re-review
- `adv:` explicit focused L2+ review
- `e:` explicit E2E-only verification
- `rev:` prior Review Tickets or claimed fixes already exist

## Duplicate-review Rule

Assign one primary owner per root cause.

- later layers may cite earlier results without re-reviewing them
- reopen only when evidence is missing/contradicted or the current layer owns a distinct consequence
- adviser must not duplicate a specialist ticket for the same root cause
- reviewer must not rediscover unrelated findings during convergence

## Review Budgets

Targets, not hard token guarantees:
- `rp:` 5k-10k
- `cr:` 12k-25k
- `q:` 15k-30k
- `e:` 15k-25k
- `adv:` 20k-40k
- `rev:` 8k-20k

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
