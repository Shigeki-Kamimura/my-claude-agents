## Available Agents

- req-pl
- adviser
- review-planner
- reviewer
- test-qa
- e2e-qa
- code-quality-reviewer
- hq-coder

## Routing

- p: / pl: -> req-pl
- rp: / plan: -> review-planner
- r: / rev: -> code-quality-reviewer
- a: / adv: -> adviser
- q: / qa: -> test-qa
- e: / e2e: -> e2e-qa
- h: / hq: -> hq-coder

## Mandatory Agent Routing

The main Codex session is a coordinator, not the worker.

For every task, choose one designated role/agent before doing work.

Required output before work:

ROUTE: <agent/profile>
REASON: <routing reason>
SCOPE: <delegated scope>

Rules:
- Do not silently perform work that belongs to hq, qa, pl, reviewer, or review-planner.
- Do not silently perform work that belongs to e2e-qa.
- If routing is ambiguous, choose the safest specialized route and state the assumption.
- Implementation must route to hq.
- L0/L1 verification must route to qa.
- Browser-level E2E design/verification must route to e2e-qa.
- Prefer E2E decomposition by `read` / `write` / `rules` / `auth`.
- Split or add files before a single E2E spec exceeds 400 lines.
- Requirement clarification must route to pl.
- Review planning must route to review-planner.
- L2+ review/convergence review must route to reviewer.

## Routing Visibility

When delegated to a sub-agent:

- explicitly state:
  - which agent was used
  - why it was selected
  - what scope it handled

Never silently inline delegated work.

## Review Ownership

- requirement clarification -> req-pl
- implementation -> hq-coder
- L0/L1 verification -> test-qa
- browser-level E2E design/verification -> e2e-qa
  organize by `read` / `write` / `rules` / `auth`
- L1.5 code quality review -> code-quality-reviewer
- L2+ review -> adviser
- convergence review -> reviewer
