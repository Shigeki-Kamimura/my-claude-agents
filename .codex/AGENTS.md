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
  do not expand into E2E/integration completeness, non-functional risk hunts, or coverage percentages
- changed E2E/integration design/verification -> e2e-qa
  do not inspect unit/service/controller spec adequacy or re-evaluate test-qa findings
  organize by `read` / `write` / `rules` / `auth`
- L1.5 code quality review -> code-quality-reviewer
- L2+ review -> adviser
- convergence review -> reviewer

## Review Operating Model

`rp` is the review hub.

`rp` must decide:
- requirement summary
- non-goals
- changed responsibility boundary
- important risks
- which reviewer sees which files
- duplicate-review exclusions
- adviser handoff points

Standard flows:
- These are recommended manual sequences, not automatic chains.
- Agents must stop after their own layer and wait for the user's next command unless explicitly instructed otherwise.
- Tiny PR: direct `cr:` is allowed for formatting, small refactors, one-test additions, or obvious bug fixes
- Normal PR: `rp -> cr -> q -> adv`
- E2E changes present: `rp -> cr -> q -> e -> adv`
- Large design change: `rp -> adv first -> cr/q/e -> adv convergence`
- Re-review: previous findings only; no new broad adequacy review

Layer split:
- `cr`: lightweight implementation smell and review-readiness check
- `q`: unit/service/controller spec adequacy only; do not review E2E/integration tests unless explicitly routed
- `e`: E2E/integration adequacy only, including browser E2E and backend controller/API e2e
- `adv`: L2+ boundary review against rp risk handoff
- `rev`: prior Review Tickets / claimed fixes only
- `adv convergence`: re-check only L2+ boundary risks previously raised by adv; do not perform broad PR review
- `rev`: verify prior Review Tickets or claimed fixes across layers after concrete fixes

Target review budget:
- `rp:` 10k-20k tokens
- `cr:` 20k-35k tokens
- `q:` 25k-40k tokens
- `e:` 20k-35k tokens
- `adv:` 30k-60k tokens
- `rev:` 10k-25k tokens

Duplicate-review rule:
- Once a layer has covered a topic, later layers may cite the result but must not re-evaluate it unless merge judgment depends on unresolved evidence.
- Later layers may re-open a topic only when previous evidence is missing or contradicted, merge judgment depends on unresolved evidence, or the topic is part of that layer's explicit risk handoff.

rp size rule:
- `rp` creates the review plan only.
- `rp` must not perform code review, test adequacy review, E2E review, L2+ judgment, or full-file deep inspection.
- `rp` should stay lightweight; if planning starts to require deep reading, route the uncertainty to the target reviewer instead.

## Review Entry Rule

All review from L1.5 onward must start with `rp:` (review-planner).

`cr:`, `a:`, `e:`, `rev:` should be invoked based on review-planner output.

Direct use exceptions:
- `cr:`: Re-checking L1.5 only for a specific concern
- `rev:`: Review Ticket or claimed fix already exists
- `e:`: Explicitly verifying E2E only

Do not start first-pass L2+ review directly from `a:`.
