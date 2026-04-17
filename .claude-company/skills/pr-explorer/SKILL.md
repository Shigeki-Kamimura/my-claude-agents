---
name: pr-explorer
description: Read-heavy exploration before editing. Use when the codebase is unfamiliar or when you need evidence files, entry points, and a bounded plan.
allowed-tools: Read, Grep, Glob, Bash
---
Use this skill before editing when the workspace or impact area is not yet clear.

Goals:
- identify evidence files (<=5)
- identify entry points / affected modules
- infer stack from repo files if needed
- produce a short plan (<=3 steps)
- declare change boundaries (Touch / Do NOT touch)
- flag high-risk areas early

Output shape:
- Evidence files
- Entry points / affected modules
- Inferred stack and assumptions
- Plan (<=3 steps)
- Change boundaries
- Risk note if high-risk areas are involved

Prefer read-only commands and deterministic inspection.
Avoid premature implementation details.
