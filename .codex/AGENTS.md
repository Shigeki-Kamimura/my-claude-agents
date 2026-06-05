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

## Mandatory Agent Routing

The main Codex session is a coordinator, not the worker.

For every task, choose one designated role/agent before doing work.

Required output before work:

ROUTE: <agent>
REASON: <routing reason>
SCOPE: <delegated scope>

Rules:
- Do not silently perform work that belongs to hq-coder, test-qa, req-pl, reviewer, or review-planner.
- Do not silently perform work that belongs to e2e-qa.
- If routing is ambiguous, choose the safest specialized route and state the assumption.
- Implementation must route to hq-coder.
- L0/L1 verification and fail-path test design must route to test-qa.
- Browser-level E2E design/verification must route to e2e-qa.
- Prefer E2E decomposition by `read` / `write` / `rules` / `auth`.
- Split or add files before a single E2E spec exceeds 400 lines.
- Requirement clarification must route to pl.
- L2+ review planning must route to review-planner.
- L2+ risk review must route to adviser.
- Convergence review must route to reviewer.

## Routing Visibility

When delegated to a subagent:

- explicitly state:
  - which agent was used
  - why it was selected
  - what scope it handled

Never silently inline delegated work.

## Review Ownership

- requirement clarification -> req-pl
- implementation -> hq-coder
- L0/L1 verification, changed-test-file adequacy, fail-path test design, and targeted test implementation -> test-qa
  do not expand into browser-flow E2E completeness, non-functional risk hunts, or coverage percentages
- changed browser-level E2E design/verification -> e2e-qa
  do not inspect unit/service/controller spec adequacy or re-evaluate test-qa findings
  organize by `read` / `write` / `rules` / `auth`
- L1.5 code quality review -> code-quality-reviewer
- L2+ review -> adviser
- convergence review -> reviewer

## Review Entry Rule

All review from L1.5 onward must start with `rp:` (review-planner).

`cr:`, `a:`, `e:`, `rev:` should be invoked based on review-planner output.

Direct use exceptions:
- `cr:`: Re-checking L1.5 only for a specific concern
- `rev:`: Review Ticket or claimed fix already exists
- `e:`: Explicitly verifying E2E only

Do not start first-pass L2+ review directly from `a:`.
