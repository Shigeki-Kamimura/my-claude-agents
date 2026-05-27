# Reviewer Hybrid Migration Note

## Scope

This branch introduces a hybrid reviewer experiment:
- md = knowledge layer
- xml = execution contract layer

Only `reviewer` is migrated in this branch.
`adviser`, `review-planner`, and `code-quality-reviewer` remain md-only references for now.

## Responsibility Map

- `code-quality-reviewer`: L1.5 local correctness, changed-line hygiene, review readiness
- `review-planner`: pre-review planning, reading scope, ticket candidate framing
- `adviser`: first-pass L2+ routing, risk ordering, specialist dispatch
- `reviewer`: convergence-only validation of prior tickets, claimed fixes, and new production regressions

## Overlap And Inflation Observed

### Healthy separation already present

- `code-quality-reviewer` is clearly L1.5-only
- `adviser` is clearly first-pass L2+
- `reviewer` is clearly convergence-only

### Repeated across multiple files

- PR base and stacked-PR diff intake rules
- targeted document intake rules
- test and E2E evidence rules
- API/Data/Auth/Test route taxonomy

### Mixed together inside `reviewer.md` before this branch

- mission and stop rules
- diff intake and output schema
- production-risk route knowledge
- domain-specific review heuristics
- handoff rules

That mixing made `reviewer.md` harder to keep stable, compare, and extend to other reviewer-family agents.

## Experiment Shape

- `.claude/contracts/reviewer.xml`: minimal execution contract
- `.claude/knowledge/review/*.md`: reusable judgment knowledge
- `.claude/agents/reviewer.md`: thin entrypoint for hybrid mode
- `.claude/agents/reviewer-md-only.md`: md-only baseline snapshot for side-by-side comparison

## Comparison Procedure

1. Run the same convergence prompt once with `.claude/agents/reviewer-md-only.md`.
2. Run the same convergence prompt once with hybrid `reviewer.md` plus `.claude/contracts/reviewer.xml`.
3. Compare:
   - token size of the instruction payload
   - whether the agent stayed in convergence scope
   - whether diff intake avoided parent PR rediscovery
   - whether output shape stayed stable
   - whether production-risk findings changed
   - whether verification gaps were reported consistently

## Rollback

- Restore routing or references to `.claude/agents/reviewer-md-only.md`
- Keep `.claude/contracts/` and `.claude/knowledge/review/` as experimental assets only
- No other reviewer-family agent depends on this structure yet

## Next Expansion Candidates

After validating reviewer:
- `adviser`: split routing contract from risk-route knowledge
- `review-planner`: split output schema from planning heuristics
- `code-quality-reviewer`: split L1.5 contract from local code-smell knowledge
