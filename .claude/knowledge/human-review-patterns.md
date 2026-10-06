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

---

## Frontend Suspense Query Pattern

### Finding
Ordinary GET data fetching used `useQuery` with manual `isLoading` / `error` rendering where the project rule requires Suspense.

### Why It Matters
Mixing manual loading/error branches into Suspense-based screens creates inconsistent user flows and bypasses the app's shared ErrorBoundary policy.

### Reject Condition
- changed frontend hook uses `useQuery` for ordinary GET/list/detail data without a conditional-fetch reason
- changed page/container manually renders `isLoading` and/or `error`
- project DESIGN.md or nearby implementation says ordinary GET data should use `useSuspenseQuery`

### Preferred Pattern
- use `useSuspenseQuery` for ordinary GET hooks
- delegate loading and error UI to the route's Suspense / ErrorBoundary
- keep `useQuery` only for conditional, dependent, or intentionally non-blocking background data

---

## API-to-UI Semantics

### Finding
A parallel API hook used incomplete filter selection and a separate mapper that lost fields preserved by the existing consumer.

### Why It Matters
A working endpoint and individually correct components do not establish that user input selects the right data source or that API data retains its meaning on screen.

### Trigger
- changed or new API hook, data-source selector, filter/URL synchronization, response mapper, or runtime discriminator handling

### Required Check
- trace the affected input/filter through data-source selection, request parameters, actual response, mapper, and renderer
- compare the affected existing consumer with the new path; check each independent selector, combined selection, clearing, URL restoration, callbacks, and pagination where changed
- preserve meaningful event kind, before/after values, delta, description/reason, and display labels required by the contract
- check legacy/unknown values against the actual producer; a TypeScript response annotation does not validate network data
- prefer a shared predicate or mapper when both consumers implement the same contract; do not require extraction merely because code looks similar

### Ownership
- review-planner: classify changed selection/filter/mapping/discriminator behavior as L2+ risk using coarse signals; choose the first route without tracing or producing findings
- code-quality-reviewer: inspect local unsafe lookup/type narrowing and nearest comparable mapping; hand off cross-layer semantics
- adviser: own the affected API-to-consumer trace and L2+ ticket; decide specialist necessity after obtaining boundary evidence
- React/Vue: inspect selector state, URL/callback synchronization, API-to-view mapping, and rendering consequences
- backend/data/security specialists: inspect only their assigned producer, persistence, or authorization boundary
- test-qa/e2e-qa: supply the corresponding component/API or browser regression evidence
- reviewer/escalation: apply only to supplied tickets, claimed fixes, or the single unresolved question

---

## Reachable Failure Evidence

### Finding
A review inferred a crash from an unsafe lookup without establishing that the selected request could return the problematic value.

### Why It Matters
An unsafe consumer can be real while the reported reproduction is blocked by an earlier selector or server filter. Incorrect reachability claims distort severity and merge decisions.

### Required Check
- identify the concrete user input, role, stored/legacy data, and request filters needed for the failure
- inspect actual producer normalization and filtering before claiming an omitted field becomes null or an unknown discriminator
- show that the problematic response survives the selected filters and reaches the mapper/renderer
- distinguish a reachable current defect, a conditional hazard, and a hazard exposed by the proposed fix
- when repairing a selector opens a previously unreachable path, verify that path's unknown-value and mapping behavior together
- mark unproven conditions explicitly; do not assign a blocker solely from a narrowed response type or unsafe lookup
- distinguish code-inspected evidence from an executed reproduction; do not claim execution from reading a test

---

## Cross-Layer Regression Cases

### Finding
Tests covered request metadata or prebuilt view models but omitted the API-to-screen boundary used by a new path.

### Why It Matters
Passing suites and aggregate coverage do not prove an untested combination. Mocks that assume the new implementation's narrowed response can conceal valid legacy or mixed data.

### Required Check
For the changed contract, select the applicable cases:
- each independent filter alone, combined filters, clearing, and URL restoration
- legacy/unknown response discriminators supported by the actual producer
- mixed result kinds with observable before/after, delta, reason, labels, and type-specific rendering
- request switching, callbacks, and pagination resets caused by selection changes

Use producer-faithful fixtures through the real mapper and renderer for component/integration tests. When browser/DB confidence is required, use stored legacy and mixed data through the actual endpoint and UI. Label API-only E2E and browser E2E separately. Do not count mocked checks as real-backend browser coverage or infer these cases from total test count.

Keep QA within assigned regression/test scope and E2E within changed user flows; do not turn this checklist into a full repository review.

---

## Scope and Unresolved Blockers

### Finding
A review listed prior unresolved blockers while declaring the new findings clean, producing an ambiguous overall LGTM.

### Why It Matters
A clean scoped pass is not proof that the PR's known merge blockers are resolved.

### Required Check
- state the review scope and immutable revision; separate local/scoped findings from overall merge readiness
- retain supplied, previously validated blockers with severity, owner, open/resolved/unverified status, and fix evidence; do not silently drop a blocker because another reviewer owns it
- validate imported claims before adopting their severity; contradictions or missing evidence require clarification or a bounded handoff
- resolve a blocker only with current-revision fix evidence and the relevant verification; a new commit or passing unrelated suite is insufficient
- a confirmed unresolved blocker keeps overall merge readiness at REQUEST_CHANGES; an unverified blocking claim keeps readiness deferred
- scoped reviewers may report their layer clean while explicitly retaining pending blockers or handoffs; they must not imply full PR approval
- convergence checks supplied tickets, claimed fixes, and regressions introduced by those fixes; do not rediscover unrelated issues

These are review-output rules. Editing agent instructions alone does not change a repository's CI verdict parser, candidate labels, branch protection, or merge automation.
