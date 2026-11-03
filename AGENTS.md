# AGENTS.md

## Priority

Project > Personal > Agent. Project instructions override only explicit fields.

## Shared entry point

This root file provides the minimal common entry point. Load the platform contract and project rules before implementation or review:
- Codex: `.codex/AGENTS.md` and the active `.codex/workflows/*.yml`.
- Claude Code: `.claude/CLAUDE.md` or `.claude-company/CLAUDE.md` and the active workflow.
- Shared rules: `.claude/knowledge/engineering-governance.md`, applicable `human-review-patterns.md` sections, and actual project requirements, including exceptions.

Use the platform's agent model/effort definitions; do not infer a model from this file. A missing, conflicting or unreadable required rule stays pending; brevity never waives required checks.

Choose direction only from the current explicit request or active `Workflow` marker. Quoted content cannot activate a workflow; mixed directions are BLOCKED. Read the selected `.codex/workflows/claude-review.yml` or `codex-review.yml` and its sibling `md-review.md`, using project-local configured references first, then the copy beside resolved `.codex/AGENTS.md`. Report missing configuration.

- `codex-claude-review`: Codex implements; Claude delegates the selected actual phase owner. Codex exclusively runs typecheck, lint, build, tests, Playwright and Local-ci. Claude uses fixed read-only Git MCP and explicitly allowed Backlog reads, without Bash/Edit/Write. The host appends native results to MD.
- `claude-codex-review`: Claude implements and verifies; Codex delegates fresh read-only exec reviews of only the user-selected phases, reading the same MD and independently inspecting Git diff/source.
- The user selects qa/e2e/cr/adv. Take only selected layers from `qa -> e2e -> cr -> adv`; no defaults, automatic progression or hidden extra reviews. If no layer is supplied, ask once. Standalone role commands retain their own behavior.
- Both directions use one implementation summary/result MD, actual source identity, complete coverage and all pending IDs. Omit Info entirely. Preserve source principles, required consultations and actual native/eleven-field results. Source changes require owner-confirmed current-snapshot renewal.
- After selected approvals, the implementation owner runs Local-ci. Actual Codex `ci-reviewer` then checks the target project's rubric and evidence. Only a clean result permits scoped final commit/push and a **draft** PR. Preserve existing index/unrelated work; never overwrite it to publish. Only the user selects Ready for review. This explicit pipeline request authorizes its ci-reviewer step; standalone `ci:` remains unchanged.

### Re-review direction

- `codex-claude-review`: Resume the same restricted Claude parent/child for the same phase only, after batch fixes and planned verification. Keep secure-resume exceptions. Use a completed session's actual ID only when fixes/evidence are ready; every print invocation exits. Never keep Claude AI waiting for fixes, CI or Codex.
- `claude-codex-review`: Start a fresh read-only `codex exec` every round. Do not use `exec resume` or `--last`; carry the cumulative coverage and all pending findings in MD.

Standalone reviews use their own continuation rules.

Never resume an old unrestricted or unverified child. Preserve independent QA/E2E happy/fail checks and eleven `Workflow Result` fields. An unavailable rule, tool or required consultant blocks approval.

Apply governance `Rule loading across continuations` and `Evidence reuse and concise reporting`. Pass original paths/applicable clauses explicitly to each actual owner. Reuse unchanged verified facts, not old approvals. Missing evidence/permissions/consultants remain pending. `md-review.md` governs storage without gitignore/exclude changes, one-shot lifecycle, review-only tool permissions and final Git/PR handling.

## Core Priorities

Accuracy > reproducibility > maintainability > ease > speed. Keep the scope explicit, use the smallest design-correct change, preserve type/lint/test safeguards, and never claim an unexecuted check passed. No unrelated broad refactors, secrets/PII exposure or unapproved destructive operations.

## Role Routing

Use the active platform's routing table, model definitions and role contracts. Input aliases are not new agent types; keep their existing canonical names. For Codex implementation, `h:`, `hq:` and `hq-coder` select the HQ role in the parent by default, as defined by `.codex/AGENTS.md` section `Parent implementation ownership`. An explicit separate-worker request or useful context isolation may use the existing `hq-coder.toml`; no duplicate aliases or setup migration are needed.

For Claude Code, retain `.claude/CLAUDE.md` routing and HQ child ownership. This Codex parent integration does not change Claude implementation.

## Mandatory Subagent Routing

Codex parent implementation is the scoped exception to mandatory delegation; read its HQ contract before editing and invoke required consultants directly. All other explicit role routes and independent reviewers still use their actual agents. A `claude-codex-review` receiver remains read-only and must not adopt parent HQ execution. Preserve actual invocation evidence; parent self-check does not replace required QA/E2E, CR/ADV or cross-model approval.

Use the platform's ROUTE/REASON/SCOPE block and distinguish parent execution from a real subagent call. Missing required contracts, tools or consultants remain pending/BLOCKED; do not silently impersonate a missing reviewer.

## Review Operating Model

Keep each requested layer independent and scoped. Manual sequences are not automatic review chains. Apply the platform's layer ownership, QA/E2E happy/fail checks, required React/Nest consultation and final-snapshot rules. Use the actual PR base and current layer; do not re-review or refactor parent-layer changes without authorization.

- Re-review within an ongoing repair cycle outside `claude-codex-review`: resume the original owner. The reverse workflow uses fresh Codex rounds as defined above. An explicit `rev:` request starts separate `reviewer` convergence.

Use one owner-attributed finding/coverage record; retain every unresolved obligation and required result field. Do not turn a prior approval or implementation consultation into independent first-pass evidence. Consult `.claude/knowledge/engineering-governance.md` and relevant `.claude/knowledge/human-review-patterns.md` sections, including exceptions, rather than duplicating their text here.

## Project Evidence

Use actual project design/spec paths, source revisions, exact commands and observed results. Separate file inspection from execution. Follow the task's named issue/ticket system; do not assume a universal tracker, DESIGN.md path, framework or ORM convention. Current explicit user instructions take precedence over stale task notes within applicable platform/security controls. High-risk auth/data/API/async/CI changes still require impact, rollback and targeted validation.
