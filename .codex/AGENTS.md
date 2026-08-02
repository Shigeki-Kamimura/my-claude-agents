## Available Agents

This file documents the routing mirrored by `.codex/config.toml`.
The effective project-wide coordinator instructions live in `developer_instructions` there because this nested `AGENTS.md` applies only under `.codex/`.

- pl
- adviser
- review_planner
- reviewer
- qa
- e2e_qa
- code_quality_reviewer
- hq
- data_platform
- sec_arch
- react_ui_flow
- vue_frontend
- nestjs_backend
- spring_boot

## Routing

- p: / pl: -> pl
- rp: / plan: -> review_planner
- cr: -> code_quality_reviewer
- r: / rev: -> reviewer
- a: / adv: -> adviser
- q: / qa: -> qa
- e: / e2e: -> e2e_qa
- h: / hq: -> hq

## Mandatory Agent Routing

The main Codex session is a coordinator, not the worker.

For every task, choose one designated role/agent before doing work.

Required output before work:

ROUTE: <agent/profile>
REASON: <routing reason>
SCOPE: <delegated scope>

Rules:
- Do not silently perform work that belongs to hq, qa, pl, reviewer, adviser, or review_planner.
- Do not silently perform work that belongs to e2e_qa.
- If routing is ambiguous, choose the safest specialized route and state the assumption.
- Implementation must route to hq.
- L0/L1 verification must route to qa.
- Browser-level E2E design/verification must route to e2e_qa.
- Prefer E2E decomposition by `read` / `write` / `rules` / `auth`.
- Split or add files before a single E2E spec exceeds 400 lines.
- Requirement clarification must route to pl.
- Review planning must route to review_planner.
- First-pass L2+ review must route to adviser.
- Post-fix convergence review must route to reviewer.

## Routing Visibility

When delegated to a sub-agent:

- explicitly state:
  - which agent was used
  - why it was selected
  - what scope it handled

Never silently inline delegated work.

## Review Ownership

- requirement clarification -> pl
- implementation -> hq
- L0/L1 verification -> qa
- browser-level E2E design/verification -> e2e_qa
  organize by `read` / `write` / `rules` / `auth`
- L1.5 code quality review -> code_quality_reviewer
- L2+ review -> adviser
- convergence review -> reviewer
- reviewer execution contract -> `.claude/contracts/reviewer.xml` with detailed knowledge in `.claude/knowledge/review/*.md`
