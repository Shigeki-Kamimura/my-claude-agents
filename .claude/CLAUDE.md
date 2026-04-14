# CLAUDE.md (single source of truth)

## Precedence
3 層構成。衝突時は上位が勝つ。

1. **Project layer**: repo upstream `CLAUDE.md` / `docs/coding-rules.md`
   - 対象: 検証コマンド、スタック規約、リポジトリ固有方針
   - upstream が明示的に上書きした項目のみ Personal layer を無効化する
2. **Personal layer (本ファイル)**: Output language / Evidence citation / Mandatory comments / Change protocol / Hard rules
   - upstream が明示的に触れていない限り常時適用
3. **Agent / skill frontmatter**: 最下位。上位 2 層に従う

運用: upstream は「検証・スタック固有のこと」、本ファイルは「作法・コメント・役割順序」を担う。重複は upstream を正とする。

## Mission
Maximize L0–L1 quality during coding. L2+ は specialist agent に委譲。

## Core priorities
Accuracy > reproducibility > maintainability > ease > speed
Clarity > cleverness / Small diffs > large rewrites / Explicit errors > silent failure / Validated progress > theoretical perfection

Never weaken: type safety, lint rules, tests.

## Output language
- 対人応答: 日本語（です・ます調）
- コード・識別子: 英語
- コメント / docstring: 簡潔な日本語
- コミットメッセージ: 英語（命令形）

## Evidence citation
参照時は相対パス + 行番号で示す。例: `src/foo.ts:42-58`
推測で埋めない。不明点は 1 問だけ確認する。

## Change protocol
1. `pr-explorer` でエビデンスと影響範囲を把握
2. `change-boundary` で Touch / Do NOT touch を確定
3. `hq-coder` で最小差分を実装
4. `verify-fast` を通す
5. 高リスク領域なら `verify-full` + `sec-arch` / `data-platform` / スタック別 L2 で契約・trust boundary を確定
6. `test-qa` で回帰観点 + コメント品質（Why / Contract / Side effects / 自動挿入コメントの妥当性）を同時チェック
   - 低リスク変更は 5 を省略し、3 → 4 → 6 の軽量パスを許容

## Hard rules
- 未使用依存追加禁止
- 広域 refactor 禁止（スコープ外変更は別 PR）
- lint / typecheck / test の緩和禁止
- secret / PII をログ・コミット・URL に出さない
- 破壊的操作（rm, force push, reset --hard, migration rollback）は都度承認

## High-risk areas
DB schema / migration、authn/authz、public API、依存・lockfile、CI/tooling、secret/PII、外部連携、非同期副作用。
→ 影響範囲・rollback・失敗時挙動・検証手段を明記。

## Failure behavior (必須カバー)
validation error / 401 / 403 / timeout / 429 / 5xx / 重複実行 / 部分書込 / retry

## Validation entrypoints
- FAST: format-check, lint, typecheck, stable unit test, build
- FULL: integration / e2e smoke / release build / migration dry-run
単一エントリ（`verify:fast` / `verify:full`）が無ければ最小構成を提案し bundling する。

## Role trigger
ユーザーメッセージが以下のプレフィックスで始まる場合、対応する agent に委譲する。

| Prefix | Agent |
|--------|-------|
| `p:` / `pl:` | req-pl |
| `h:` / `hq:` | hq-coder |
| `q:` / `qa:` | test-qa |

プレフィックスなしの場合はメインセッションが直接応答する。

## Role map
- req-pl: WHAT / WHY（要件不明時）
- hq-coder: HOW（実装）
- test-qa: 回帰・契約固定 + コメント品質（L2 後にチェック）
- sec-arch / data-platform: L2+ 横断レビュー
- spring-boot / nestjs-backend / react-ui-flow / vue-frontend: スタック別 L2+

## Mandatory comments (必須コメント)
### ファイル先頭
全ソースファイルの先頭に、その言語の標準コメント構文でヘッダブロックを必ず付与する。
必須項目:
- Why: このファイル / モジュールが存在する理由（ビジネス or 技術的動機）
- Scope: 取り扱う責務と取り扱わない責務（non-goals）
- Depends: 重要な外部依存（任意）

例（TypeScript / Java / C 系）:
```
/*
 * Why: 注文確定時の在庫引当を単一トランザクションで保証するため。
 * Scope: 引当・取消のみ。支払い処理は orders/payment に委譲。
 * Depends: InventoryRepository, OrderEventPublisher
 */
```

### 関数 / メソッド先頭
public / exported なもの、および非自明な private にも必ず付与する。
必須項目:
- Why: なぜこの関数が必要か（呼び出し側の要求・制約）
- Contract: 入力前提 / 出力保証 / 例外条件
- Side effects: 副作用の有無（DB / IO / 外部呼び出し / グローバル状態）

自明な getter / setter / 1 行委譲は省略可。省略判断に迷う場合は付ける。

### 自動挿入ルール（可読性コメント）
実装時は以下を hq-coder が自動で差し込む:
- 分岐の意図が非自明な箇所に「なぜこの条件か」1 行コメント
- ループの不変条件 / 終了条件が非自明な場合に 1 行コメント
- マジックナンバー / ハードコード値の根拠を 1 行コメント
- 早期 return / ガード節の守っている前提を 1 行コメント
- 非同期境界・トランザクション境界・trust boundary の明示コメント

### 禁止
- 「何をしているか」だけを繰り返すコメント（コードで自明なもの）
- 古くなった TODO / FIXME の放置（期限または issue 番号必須）
- secret / PII / 内部 URL のコメント記載
- 1 コメント内での言語混在（コードは英語、コメントは簡潔な日本語で統一。既存コードは触る時に適用し、一括書き換えはしない）

### レビュー観点
test-qa と sec-arch / data-platform は「Why が欠落している関数 / ファイル」を指摘対象に含める。欠落は lint 相当の差し戻し理由とする。

## File layout
- 共有ルール: repo 直下 `CLAUDE.md`（upstream）/ 本ファイル（global）
- 個人上書き: `CLAUDE.local.md` または `~/.claude/`
- 反復手順: `skills/` 配下の SKILL.md
- 長大チェックリストを本ファイルに詰め込まない
