---
name: change-boundary
description: Use before editing to lock scope, touched files, non-goals, and rollback expectations for risky or multi-file changes.
allowed-tools: Read, Grep, Glob
---
Use this skill when a task touches multiple files, shared contracts, or risky boundaries.

Produce:
- Objective
- Non-goals
- Touch
- Do NOT touch
- Acceptance affected
- High-risk areas involved
- Rollback note if needed

Rules:
- choose the smallest safe scope
- split large changes into reversible chunks
- do not expand scope silently
