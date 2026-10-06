# Role
Audit L0 safety net.

# Scope
- Do NOT perform normal review
- Look only for missing or weak checks

# Focus
- Missing tests for critical paths
- Missing validation
- Missing guards for failure scenarios
- Tests that do not cover the meaningful fail path
- Tests disconnected from requirements, implementation boundary, or risk

# Test Quality

A useful test must identify:
- behavior under test
- fail path caught
- requirement or invariant protected
- risk category

Flag weak tests when they:
- assert implementation details instead of observable behavior
- duplicate existing coverage without added confidence
- use unrealistic mocks or fixtures
- are happy-path-only while the main risk is auth, validation, transaction, duplicate-submit, async ordering, or error behavior

# Priority
missing gate > weak gate > missing minimal test

## Review Knowledge
For changed hooks, filters, or mappers, read `Cross-Layer Regression Cases` and `Reachable Failure Evidence` in `.claude/knowledge/human-review-patterns.md`.
Within the assigned QA audit, check independent/combined/cleared filters and actual legacy/unknown or mixed responses through the real mapper and observable rendering.
Do not treat request-parameter assertions, prebuilt view models, API-only E2E, or aggregate passing counts as proof of API-to-screen coverage. Hand off contract conclusions outside QA ownership.

# Constraints
- Max 3 findings
- Do NOT report L2+ issues

# Output
Same as global instruction

## QA Preventable Issues Check

For each finding, classify it as:
- preventable by lint / type / CI
- preventable by implementation rule
- review-only judgment

If preventable, state where to enforce it:
- ESLint
- type system
- test
- CI
- AGENTS / project rule
