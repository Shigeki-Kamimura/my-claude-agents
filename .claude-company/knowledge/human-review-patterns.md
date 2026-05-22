# Human Review Patterns

## Responsibility Separation

### Finding
Approval screens contained award-grant logic directly.

### Why It Matters
UI/request flows should not own unrelated domain workflows.
Mixing responsibilities increases review complexity and future maintenance cost.

### Reject Condition
- approval/request UI directly performs award-grant workflow
- unrelated domain workflows mixed into same service/component

### Preferred Pattern
- approval flow delegates to dedicated award service
- workflows separated by domain responsibility

---

## Exception Handling

### Finding
Unnecessary try/catch blocks existed with empty or meaningless catch logic.

### Why It Matters
Redundant exception handling hides true error boundaries and duplicates global policy.

### Reject Condition
- empty catch
- catch that only rethrows
- catch without recovery, mapping, cleanup, or logging context

### Preferred Pattern
- rely on common exception handling
- add try/catch only when behavior changes

---

## Type Safety

### Finding
Broad `as` assertions weakened TypeScript safety.

### Why It Matters
Unsafe casts hide DTO/domain mismatch and reduce refactor safety.

### Reject Condition
- broad casting
- `unknown as Xxx`
- bypassing narrowing

### Preferred Pattern
- explicit DTO types
- narrowing
- type guards
- schema validation

---

## Refactoring Scope

### Finding
Feature PR included unrelated refactoring.

### Why It Matters
Large mixed diffs increase human review cost and regression risk.

### Reject Condition
- unrelated cleanup inside feature PR
- formatting churn mixed with logic changes

### Preferred Pattern
- smallest safe diff
- isolated refactoring PR when necessary

---

## Design Document Alignment

### Finding
Implementation did not sufficiently follow DESIGN.md intent.

### Why It Matters
Ignoring established project rules causes architectural drift.

### Reject Condition
- implementation contradicts DESIGN.md
- exception policy ignored
- layering constraints bypassed

### Preferred Pattern
- verify relevant DESIGN.md before implementation
- explain intentional deviations