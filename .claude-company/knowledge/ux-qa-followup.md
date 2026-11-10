# UX QA follow-up contract

Use for later human results supplied by the requester or caller in a new `ux:` request. Read only when the request includes a prior report path or human records.

Canonical: `.claude/knowledge/ux-qa-followup.md`; keep the company copy identical.
Human issue fields: [UX QA guide](ux-qa-guide.md), `Human feedback handoff`.

## Input

- Prior report's absolute path. If absent, ask the requester; never guess.
- Human records: recorder name/ID, timestamp, `case_id`/`step_id`, content.
- Requester answers with provenance: respondent and timestamp.

## Report continuity

- Keep the prior report read-only and unchanged.
- Write a new report to a new output directory. Show its own run ID near the start and reference the prior run ID.
- Reuse `case_id` for the same task. For changed tasks, record the old-to-new ID mapping in the new report.
- Keep records with unconfirmed mappings unresolved; never guess links.
- If requester answers make an adaptation `CONFIRMED`, attribute them as human statements with respondent and timestamp, never as AI inference.

## Execution boundary

This remains a normal `ux:` run; safety-gate step 5 still applies. If the app is not running, stop and ask. Do not create a record-only report.
