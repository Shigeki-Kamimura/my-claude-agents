# AGENTS.md

## Mission
Maximize L0-L1 quality and move work forward with the safest next step.

## Priorities
Accuracy > reproducibility > maintainability > ease > speed

Never weaken:
- type safety
- lint rules
- tests
- repository CI gates

## Operating Rule
Agents must execute the declared MODE.
If MODE is omitted, choose the least destructive safe mode and state the assumption.

Default:
- vague requirement -> DISCOVERY
- design trade-off -> DECISION
- coding-ready task -> IMPLEMENTATION
- staged diff -> L0_AUDIT
- previous review fix check -> DIFF_ONLY_CONVERGENCE

## Core Implementation Rules
- Reuse existing patterns first.
- Make the smallest safe diff.
  - Prefer small, safe diffs, but do not preserve poor structure when the current implementation violates clear responsibility boundaries, type safety, or testability.
  - When a fix requires structural improvement, propose the smallest design-correct change rather than the smallest textual diff.
- Preserve unrelated code.
- Avoid opportunistic refactoring.
- Avoid unsafe TypeScript `as`.
- Avoid no-op `catch`.
- Prefer ORM / Repository / QueryBuilder over raw SQL.
- Follow DESIGN.md and docs/coding-rules.md first.

## Required Before Editing
- Evidence files, <=5
- Entry points / affected modules
- Plan, <=3 steps
- Touch / Do NOT touch

## Validation
Always report:
- exact commands run, or
- NOT RUN + reason

