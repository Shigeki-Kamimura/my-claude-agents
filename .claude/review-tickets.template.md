# L2+ Initial Review

## Scope
- <機能/変更の要点を3〜6行で>
- boundaries: <DB / auth / API / async など該当のみ列挙>

## Review Tickets
# 形式: ID | Status | Severity | Route | Location | Short label

- DB-1 | open | high | Decision | migrations/.../migration.sql:1 | citext拡張: 本番権限+rollback未定
- DB-2 | open | high | Implementation | awards.service.ts:386-428 | assignAward重複INSERT競合
- SEC-1 | accepted-risk | low | Decision | awards.controller.ts:66-70 | getMyAwards trust boundary
- SEC-2 | accepted-risk | low | Decision | awards.service.ts:430-441 | revokeUserAward IDOR
- TZ-1 | defer | low | Decision | awards.service.ts:55-62,87-89 | JST固定未来日判定

## Required Now
- DB-1: 本番DBで `CREATE EXTENSION citext` 可否確認 + rollback手順確定
- DB-2: `INSERT ... ON CONFLICT DO NOTHING RETURNING` に変更

## Stop Condition
- unresolved high/medium = 0
- `pnpm --dir backend test`
- `pnpm --dir backend typecheck`