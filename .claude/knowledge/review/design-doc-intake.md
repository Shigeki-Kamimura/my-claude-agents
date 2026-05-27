# Design Document Intake For Review

Use this knowledge only when a convergence ticket depends on project rules, API policy, DB design, auth policy, screen behavior, or exception handling.

## Intake Rules

- Do not read broad design documents by default.
- Enumerate actual design/spec paths in the target repository first.
- Grep exact endpoint, module, table, screen, or rule names before opening files.
- Read only the minimum section needed for the active ticket.
- Cite only rules personally inspected in the current review.

## When To Escalate

Return to `req-pl` when:
- the ticket cites a rule but no source path can be located
- merge judgment depends on a document rule that cannot be confirmed
- the source is too ambiguous to support a production-risk decision

## Evidence Standard

When citing a rule:
1. Identify the exact section or heading.
2. State the concrete code fact.
3. Explain the mismatch without expanding the rule by preference.

If the issue is only a design preference, do not turn it into `REQUEST_CHANGES`.
