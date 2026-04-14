---
name: verify-fast
description: Run the fastest deterministic presubmit gate for the current stack and summarize exact commands and failures.
allowed-tools: Read, Grep, Glob, Bash
---
Use this skill after code changes or before review.

Mission:
Run or propose the smallest deterministic FAST gate for the current stack.

Preferred FAST contents:
- format-check
- lint
- typecheck
- stable unit tests
- build / compile

Procedure:
1. Infer the stack from repo files.
2. Prefer an existing single entrypoint such as `verify:fast`.
3. If absent, select the smallest concrete command set that matches repo conventions.
4. Run only deterministic checks.
5. Report exact commands and outcomes.

Output shape:
- Inferred stack
- FAST commands run
- Result summary
- Blocking failures
- Manual follow-up only if a command could not run
