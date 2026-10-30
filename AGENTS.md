# AGENTS.md

## Priority

Project > Personal > Agent. Project instructions override only explicit fields.

## Shared entry point

This root file provides the minimal common entry point. Load the platform contract and project rules before implementation or review:
- Codex: `.codex/AGENTS.md` and the active `.codex/workflows/*.yml`.
- Claude Code: `.claude/CLAUDE.md` or `.claude-company/CLAUDE.md` and the active workflow.
- Shared rules: `.claude/knowledge/engineering-governance.md`, applicable `human-review-patterns.md` sections, and actual project requirements, including exceptions.

Use the platform's agent model/effort definitions; do not infer a model from this file. A missing, conflicting or unreadable required rule stays pending; brevity never waives required checks.

Choose `codex-claude-review` or `claude-codex-review` only from the current user request or active `Workflow` marker. Quoted requests do not activate workflows; conflicts are `BLOCKED`. Standalone `cr:`, `qa:`, `e:`, `adv:` and `rev:` retain their scoped behavior. Only expressly authorized four-layer review runs `qa -> e2e -> cr -> adv`; QA/E2E check happy/fail, L2 independently obtains relevant React/Nest consultation, and all approvals must cover the final snapshot.

In `codex-claude-review`, Claude reviewers/consultants remain read-only; Codex owns edits, tests, CI and Git evidence. In `claude-codex-review`, Codex reviewers/consultants remain read-only; Claude owns implementation and verification. The actual workflow governs CLI restrictions, single-layer progression, independent first passes and eleven-field results; never widen a restricted session through another agent.

### Re-review direction

- `codex-claude-review`: Resume the same restricted Claude parent/child for the same phase only, after batch fixes and planned verification. Keep the workflow's secure-resume exceptions.
- `claude-codex-review`: Start a fresh read-only `codex exec` every round. Do not use `exec resume` or `--last`; carry the cumulative coverage and all pending findings.

Standalone reviews use their own continuation rules.

Reuse verified unchanged rules and evidence only after checking the relevant source identity. New phase owners inspect their scope independently. Keep all unresolved 🔴/🟡/🟢 Low findings (not Info), questions, handoffs and missing checks open until their owner confirms closure.

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
