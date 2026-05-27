# L2+ Production Risk Knowledge

This file is knowledge for `reviewer` convergence work, not an execution contract.

## Reviewer Focus

`reviewer` owns only:
- unresolved Review Tickets
- claimed-fix validation
- newly introduced production regressions in the fix layer
- merge-relevant verification sufficiency

`reviewer` does not own:
- first-pass PR review
- L1.5 local code-quality sweep
- requirement clarification
- broad architecture redesign

If the request is a new PR or a fresh L2+ pass, route to `adviser`.

## Merge-Relevant Risk Routes

### API Contract

Inspect:
- controller or route declaration
- DTO, schema, validation, or request parser
- service method receiving the input
- caller/client/hook using the contract
- nearest tests asserting request/response behavior

Look for:
- path, method, or param drift
- optional/required mismatch
- response shape drift
- missing validation for new fields

### Data Integrity

Inspect:
- schema or migration diff
- service write path
- transaction boundary
- unique/FK/nullability assumptions
- seed or backfill behavior when touched

Look for:
- missing transaction around multi-step writes
- non-idempotent seeds or retries
- duplicate or lost write risk
- deploy or rollback risk that needs human verification

### Authorization Boundary

Inspect:
- controller guard or decorator
- service-side authorization check
- ownership boundary
- caller assumptions about current user
- negative or forbidden-path verification

Look for:
- missing guards
- trusting client-provided identity
- ownership bypass via params or body
- frontend-only authorization

### Frontend Flow

Inspect:
- submit or event handler
- loading and disabled state
- API call and error mapping
- refresh or invalidation path
- user-visible feedback

Look for:
- double submit
- stale state after fix
- success shown before durable success
- swallowed or mis-mapped errors

### Async / Notification

Inspect:
- event producer
- enqueue or persistence point
- consumer or handler when changed
- idempotency or dedupe markers
- retry and failure behavior

Look for:
- side effects before commit
- duplicate notifications on retry
- missing durable completion state

## Convergence Judgment

Mark `Clean` only when:
- no unresolved medium/high production risk remains
- matched high-risk routes were inspected or explicitly left unresolved
- required verification evidence is sufficient

Mark `Not Clean` when:
- a blocker or high/medium unresolved risk remains
- fix evidence is partial
- verification required for merge is missing
