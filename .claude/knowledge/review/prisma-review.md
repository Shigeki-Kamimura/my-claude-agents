# Prisma Review Notes

Use this file when convergence tickets touch Prisma schema, migrations, transactions, or seed behavior.

## Read In Order

1. schema or migration diff
2. write path in service or repository
3. transaction boundary
4. retry/idempotency assumptions
5. seed or backfill changes when touched

## Review Reminders

- `upsert` does not automatically make multi-step flows idempotent.
- Logical delete filters must stay aligned across read and write paths.
- Seed changes are merge-relevant only when they affect reproducibility or deploy safety.
- Migration correctness is not proven by generated file presence alone.

## Typical Merge Risks

- duplicate writes on retry
- missing transaction around coupled writes
- service assumptions drifting from schema nullability or uniqueness
- rollback or deploy sequencing risk left unverified
