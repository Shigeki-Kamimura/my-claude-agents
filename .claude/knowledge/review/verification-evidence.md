# Verification Evidence Knowledge

This file defines what counts as usable evidence for convergence review.

## Accepted Evidence Order

1. Explicit CI result tied to the current layer
2. Command output tied to the reviewed change
3. Direct inspection of relevant test or E2E files plus execution evidence
4. Missing or stale evidence

## Tests

Tests count as merge evidence only when you inspected:
- the relevant test file or command output
- the specific behavior covered
- the gap between tested and assumed behavior

Do not claim sufficiency from filenames alone.

## E2E

E2E counts only when you inspected:
- the relevant spec
- the exact user-visible behavior covered
- positive, negative, or role-boundary coverage when relevant
- execution evidence, not just spec creation

If E2E was blocked by fixture, factory, seed, or type errors, mark verification insufficient.

## Required Verification Flags

Keep verification unresolved when the fix changes:
- schema or migration behavior
- API contracts
- auth or authorization rules
- transaction boundaries
- async side effects
- destructive actions

## Output Wording

Use:
- `sufficient` when evidence supports merge judgment
- `insufficient` when required evidence is missing
- `not verified` when no execution evidence exists
