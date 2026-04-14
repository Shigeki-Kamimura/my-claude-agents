---
name: verify-full
description: Run deeper validation for high-risk changes such as DB, auth, dependencies, build, or external side effects.
allowed-tools: Read, Grep, Glob, Bash
---
Use this skill for high-risk changes or before a merge when FAST is not enough.

Trigger FULL when any apply:
- DB schema / migration / backfill
- authn / authz / session / cookies
- dependency or lockfile changes
- build / CI / tooling changes
- external integrations
- public APIs with side effects
- background jobs / async workflows

Procedure:
1. Infer the stack and the risk area.
2. Prefer an existing single entrypoint such as `verify:full`.
3. Otherwise run the smallest deeper set available, such as integration tests, e2e smoke, or release-critical builds.
4. Report exact commands and outcomes.
5. If not run, explain why and give manual verification steps.

Output shape:
- Risk area
- FULL commands run
- Result summary
- Remaining risks
- Manual verification if needed
