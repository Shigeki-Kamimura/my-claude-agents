# Consolidated L1.5 Review Policy Cleanup

## Recommended Structural Cleanup

Current structure is already strong.
The main remaining issue is local duplication and classification drift.

Goal:

* reduce token waste
* prevent CI-substitute behavior
* prevent full-diff ingestion

- improve evidence discipline
- stabilize stacked PR review behavior

---

# Recommended Final Structure

## 1. Mission

Keep only:

* review mission
* review boundaries
* review philosophy
* non-goals

Do not place operational mechanics here.

---

## 2. L1.5 Review Policy

Keep:

* commit/topic-level preference
* full PR review only near merge
* L0/L1 ownership
* no machine-verifiable reruns
* no fake coverage claims

Recommended content:

```md
## L1.5 Review Policy

Prefer commit-level or topic-level L1.5 review during implementation.

Use full PR L1.5 review only as a final aggregation pass before:
- L2+ review
- human review
- merge

L1.5 must not rerun:
- lint
- biome
- typecheck
- test execution
- build verification

Those belong to L0/L1 verification.

Do not evaluate test coverage metrics in L1.5 review unless explicit coverage reports are provided.

L1.5 may check:
- whether relevant test files were added or updated
- whether test placement matches changed responsibilities
- whether verification evidence exists

L1.5 must not claim coverage quality from changed line counts alone.
```

---

## 3. Stacked PR Awareness & Diff Expansion

Merge these sections together.
They are conceptually the same operational concern.

Recommended merged title:

```md
## Stacked PR Awareness & Diff Expansion
```

Recommended cleanup:

```md
Never load full PR diff before identifying review scope and high-risk boundaries.

Do not expand or read the full PR diff by default.

Start review from:
- changed file list
- schema/API/DTO boundaries
- service/business logic changes
- high-risk files only

Only expand diff sections required for:
- evidence collection
- responsibility verification
- contract validation
- blocker investigation

Avoid loading:
- generated files
- snapshot churn
- formatting-only changes
- unrelated parent PR changes
- previously reviewed layers

Maximum review target:
- current review layer only

Prefer:
- incremental diff review
- evidence sampling
- targeted inspection

Avoid:
- exhaustive full-diff ingestion
- rediscovery review
- repeated parent-layer review

Never treat visibility in `git diff main...HEAD` as proof that a file belongs to the current PR layer.

This repository may use stacked PR workflow.

Before reviewing or editing, identify the intended review base.

Prefer reviewing only the incremental diff for the current PR layer.

Do not default to `main...HEAD` when the branch appears to be stacked.
```

---

## 4. Review Temperature

Keep this section focused on:

* what L1.5 reviews
* what L1.5 does NOT review
* local responsibility boundaries only

Avoid adding operational rules here.

---

## 5. Reject Conditions

Current structure is already good.

Recommended improvement:

* keep only actionable anti-patterns
* avoid expanding into architecture doctrine

Good current scope:

* type safety
* exception handling
* responsibility boundary
* design alignment

---

## 6. Evidence Discipline

This is now one of the most important sections.

Recommended final version:

```md
## Evidence Discipline

Do not mark an item as ✅ unless concrete evidence is provided.

Every ✅ in the consistency table must reference:
- changed file path
- relevant function/component/schema name
- explicit command output, CI result, or diff evidence when applicable

Do not use vague conditional approval such as:
- "if tests pass"
- "probably OK"
- "appears fine"

If evidence is insufficient, mark the item as:
- ⚠️ Evidence missing
- ⚠️ Needs confirmation
- ❌ Not verified

Do not claim test coverage from test file updates or added line counts.

Use:
- Test evidence: tests added/updated
- Verification evidence: command/CI output exists
- Coverage: only when an explicit coverage report is provided
```

---

## 7. Finding Classification

Add NEEDS_CONFIRMATION.

Recommended:

```md
Refactoring findings must be classified as:
- BLOCKER
- FIX_NOW
- DEFER
- REJECT
- NEEDS_CONTRACT
- NEEDS_CONFIRMATION
```

Recommended rule:

```md
Do not label an item FIX_NOW unless you can identify:
- exact file/function involved
- expected behavior
- actual observed mismatch
- required fix or verification step

If the issue is only suspected, classify as NEEDS_CONFIRMATION, not FIX_NOW.
```

This prevents fake-confidence findings.

---

## 8. Verification Requirements

This section should define verification ownership only.

Recommended cleanup:

```md
Before PASS:
- lint/type/test evidence checked without rerunning commands
- affected flows identified
- changed responsibilities identified
- risks documented
- assumptions documented
- ticket scope verified
```

Recommended ownership clarification:

```md
L0/L1 responsibilities:
- biome check
- typecheck
- unit/integration test execution
- build verification

L1.5 responsibility:
- verify existence of evidence only
- do not rerun machine-verifiable checks unless evidence is contradictory
```

---

# Main Remaining Risk

The remaining risk is NOT review quality.

The remaining risk is:

```txt
full-diff ingestion
```

Current token cost is likely dominated by:

* reading parent PR layers
* loading entire PR diffs
* rediscovery review
* generated/test churn

NOT by review reasoning quality.

That means future optimization should prioritize:

```txt
what not to read
```

rather than:

```txt
how to review better
```

---

# Current Architecture Assessment

Current structure is already significantly more mature than a typical AI review setup.

You now have:

```txt
planner
↓
L1.5 hygiene review
↓
L2+ advisory review
↓
convergence review
```

That separation is the biggest quality improvement so far.

The next stage is mostly:

* ingestion control
* review-layer isolation
* evidence strictness
* stacked PR stabilization
