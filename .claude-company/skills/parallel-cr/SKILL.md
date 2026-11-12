---
name: parallel-cr
description: Explicit opt-in parallel L1.5 trial with two independent code-quality-reviewer tasks and bounded finding/coverage validation. Do not activate for an ordinary cr request or a mere mention of this file.
---

# parallel-cr

Read the active project's `.claude/knowledge/parallel-cr-review.md` (PCR-1) before dispatch. In the configuration repository use the selected profile's `.claude/knowledge/` or `.claude-company/knowledge/` copy; verify identity and never replace conflicting project-local rules silently. Missing contract/source/tool availability is BLOCKED, not parent impersonation.

This skill is an on-demand entry, not a registered agent or executable orchestrator. The host must use actual installed agents and preserve all active permissions and workflow contracts. Do not change models, default `cr:` routing, CI, deployment, setup or ignore files. Existing child roles remain self-contained. A full trial is an explicitly requested host-coordinated multi-owner task, not a single standalone `cr:` dispatch; never give the entire fan-out request to one child. If the active dispatcher cannot honor this assignment, report BLOCKED rather than silently changing its routing or pretending to run multiple owners.

For an explicit PCR-1 trial, freeze base/head/merge-base and requirements/rules. Dispatch two fresh `code-quality-reviewer` owners with common mandatory checks and PCR-1 section 4 emphases. Keep peer results and prior verdicts out of discovery. After freezing both reports, dispatch one fresh owner to validate their candidates AND mandatory-coverage gaps, limited by PCR-1 section 6. No implicit QA/E2E/ADV or repair loop. The initial user trial request, never child output, authorizes this bounded sequence.

For an explicit candidate-only completion check, dispatch only one owner for the supplied IDs and missing obligations; do not run the two discovery tasks. Enforce original-rule/exception intake even when facts are already confirmed. Preserve source/owner identity, separate fact/scope/severity/closure, and return non-approval for missing mandatory evidence. Do not override prior verdicts or close another owner's findings.

Use concise polite Japanese. Invocation examples and the PR #1278 unfinished-validation checklist are in `docs/parallel-cr-review.md` in the configuration repository. Loading this skill alone is not evidence that any review ran.
