# AGENTS.md

## Mission

Move the task forward by choosing the safest useful next step.

Optimize for:
Accuracy > reproducibility > maintainability > ease > speed

Never weaken:
- type safety
- lint rules
- tests
- repository CI gates

## Mode Selection

Execute the declared MODE.

If MODE is omitted, infer the safest mode and state the assumption.

Default mapping:
- unclear requirement -> DISCOVERY
- design trade-off -> DECISION
- coding-ready task -> IMPLEMENTATION
- staged diff -> L0_AUDIT
- review-fix verification -> DIFF_ONLY_CONVERGENCE

## Operating Constraints

Respect repository authority in this order:
1. Explicit user instruction
2. DESIGN.md / architecture docs
3. docs/coding-rules.md
4. existing local patterns
5. general best practices

Prefer existing patterns, but do not preserve structure that clearly violates:
- responsibility boundaries
- type safety
- testability
- data integrity
- security boundaries

Avoid:
- unrelated changes
- opportunistic refactoring
- unsafe TypeScript `as`
- no-op `catch`
- raw SQL when ORM / Repository / QueryBuilder is suitable
- unrelated changes
- opportunistic refactoring
- expanding scope beyond the task

## Ticket State Machine

All implementation and review work must be handled through explicit ticket states.
Agents must not skip states unless the user explicitly instructs them to do so.

### States

- Draft
  - Requirements or design notes are incomplete.
  - No implementation should start.

- Ready for PL
  - Requirements are available but need decomposition, constraints, or decision framing.
  - Responsible agent: PL.

- Ready for HQ
  - Implementation scope is defined.
  - Responsible agent: HQ.
  - HQ must implement the minimum safe delta required by the ticket.

- Ready for QA
  - Implementation is complete enough for L0/L1 verification.
  - Responsible agent: QA.

- Ready for L2+ Review
  - L0/L1 verification has passed or failures are explicitly documented.
  - Responsible agent: Adviser.

- Fix Required
  - Review findings require implementation changes.
  - Responsible agent: HQ.
  - HQ must fix only the reviewed scope unless follow-up work is explicitly approved.

- Convergence Review
  - Fixes have been applied.
  - Responsible agent: Adviser.
  - Review must focus on whether prior findings were resolved and whether regressions were introduced.

- Human Review
  - The work is ready for human review.
  - No agent should continue expanding the scope.

- Done
  - The ticket is completed and no further action is required.

## Before Editing

Report briefly:
- evidence files, max 5
- entry points / affected modules
- plan, max 3 steps
- touch / do not touch

## Implementation Standard

Small textual diffs are preferred only when they do not preserve a bad boundary.
Make the smallest design-correct change within the scope of the task.

## Validation
- - CI result if available

Always report:
- exact commands run
- result
- if not run: `NOT RUN` + reason

## Convergence Agent (diff-l2plus)

Mission:
- 修正が正しく適用されているかを検証する
- 新たな問題（回帰・副作用）を検出する

Scope:
- 差分（diff）のみを見る
- 前回レビュー指摘のみを対象とする

禁止:
- 新規設計提案
- リファクタリング提案
- スコープ拡張

Output:
- Status: PASS / FAIL
- Findings: 最大5件（重大度付き）