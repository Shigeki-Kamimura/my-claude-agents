# Claude × Codex 4層クロスレビュー比較: GuildBoard PR #1024

記録日: 2026-11-05 / 目的: 「Claudeだけが見ていた視点」「Codexだけが見ていた視点」を共有し、両側のレビュー品質を上げる。
位置づけ: 実験記録。ユーザー承認済みの運用補足(XREV-1)の根拠であり、西口さんの原則の引用でも、全社方針の確認でもない。

## 条件と限界

- 対象: GuildBoard PR #1024「組織に所属する人の非公開をサーバーでも拒否する（PATCH /me/visibility）」。マージコミット `80c900af`、ベース `1351a03b`、ヘッド `b4e5fe1b`、15ファイル +387/-10。固定スナップショットを隔離クローンで共有。
- 方式: Claude(test-qa / e2e-qa / code-quality-reviewer / adviser)と Codex(`codex exec -s read-only` で同4層)を、同じブリーフで独立に実行。方向ワークフロー(codex-claude-review / claude-codex-review)は使っていない。全員レビュー専用で、実行・編集なし。互いの出力は読んでいない。
- 限界:
  - PR 1件のみ(n=1)。指摘数や重みは、モデルの傾向よりこの PR の性質に左右される。
  - 各指摘のコード検証は本記録の作成者(コーディネーター)は行っていない。両モデルが一致した指摘のほうが、片側だけの指摘より信頼できる、という程度の扱い。
  - 実行確認なし。`urn:uuid:` による 500 とデッドロックは、どちらのモデルでも `UNCONFIRMED`。
  - 利用枠の消費は NOT_MEASURED。Claude 側サブエージェントのトークンは合計約56万(qa 111k / e2e 88k / cr 151k / adv 214k)。Codex 側は未取得。
  - Claude の4層は同じ会話内で動いたため、Claude 側はモデルとして独立でも、ブリーフと進行は共有している。

## 層ごとの判定

| 層 | Claude | Codex |
|---|---|---|
| qa | REQUEST_CHANGES(🟡1・Low4) | COMMENT(🟡3) |
| e2e | REQUEST_CHANGES(🟡2・Low2) | E2E_GAP(🟡2) |
| cr | L1.5_REQUEST_CHANGES(🟡4・Low3) | L1.5_REQUEST_CHANGES(🟡1・Low2) |
| adv | REQUEST_CHANGES(Blocker2・Should4・Low4・質問3) | REQUEST_CHANGES(🟡6・質問2) |

## 両方が見つけた指摘(信頼度が高い)

| 指摘 | Claude | Codex | 差 |
|---|---|---|---|
| 通知の `<Toaster>` が組織作成・招待受諾の画面に存在しない(hook テストは sonner をモックしており、呼び出ししか証明しない) | cr 🟡、adv Blocker | adv Blocker(qa は相談役経由で疑義のみ) | Codex の cr は handoff 止まり。Claude の qa・e2e は見落とし |
| 新しい生 SQL が `urn:uuid:` 表記で 500 になる(`::uuid` 直接キャスト) | cr 🟡、adv Should | cr 🟡、adv Blocker | Codex は権限仕様の行と PostgreSQL の入力処理を一次情報として引用し重く判定。Claude は未実行の知識として控えめ |
| 新しい 422 がフロントで「通信に失敗しました」と表示される | cr 🟡、adv Should | cr Low、adv Should | cr で重みが逆転 |
| openapi・権限仕様が未更新(422・`visibility_changed`) | cr 🟡、adv Blocker | adv のみ(重要度 Low・区分 Blocker) | Codex の cr は handoff 止まり |
| 参加後にプロフィールのキャッシュが古い `self` を表示し得る | adv Low、qa handoff | adv Should | Codex が重め |
| E2E: `PATCH /members/:id` の 422、自動昇格(`visibility_changed`・監査)が未証明 | e2e 🟡2 | e2e 🟡2 | ほぼ一致 |
| 既存 `self` の組織所属者への再送が通る点の契約確認 | adv・qa | adv・qa | 共通の質問 |
| 古いコメントが事実と食い違う | cr・adv Low | cr Low | 一致 |
| 昇格処理の `public` 維持の対照テストがない | qa Low | qa 🟡 | 重みの差 |

## 片方だけが見つけた指摘

| 側 | 指摘 | 備考 |
|---|---|---|
| Claude のみ | 既存の「組織所属で `self`」行が救われず、backfill の migration もない(OPS-1 の rollout 行) | Codex は質問に回しただけで指摘にしなかった |
| Claude のみ | `POST /admin-members` で組織所属者に `self` を登録できる抜け道。権限の正本が登録時の `self` を認めていることまで追跡 | Codex は同じ事実に気づいたが「基底にもある」として起票しなかった |
| Claude のみ | 同じ不変条件が `me` と `members` の2サービスに別実装で重複(no-op の扱いも不一致) | cr |
| Claude のみ | 監査ログの `source` 語彙(`self_service` 等)が履歴表示の正規化と合わない | cr・adv |
| Claude のみ | 状態遷移とロック順が逆(users→guild と guild→users)でデッドロックの可能性 | adv Low |
| Claude のみ | 自動で公開範囲が広がることを参加前に告知するか(製品判断の質問) | adv Q1 |
| Claude のみ | 422 のテストが `users.updateMany` 非呼び出しや複合 payload を見ていない、mutation 失敗時の通知なし確認がない | qa Low |
| Claude のみ | 並行実行の E2E での再現難度、422 の本文確認 | e2e Low |
| Codex のみ | 監査 INSERT の外部キー検査(`KEY SHARE`)を介した、`/me` と `/members` の保存同士のロック循環。`FOR NO KEY UPDATE` を提案 | 永続化の相談役。Claude の adv は data-platform を `NOT_APPLICABLE` とし見落とし |
| Codex のみ | `/me` が root client を transaction callback に渡しており、ロック対象 ID が未検証 | qa 🟡 |
| Codex のみ | 昇格の更新・監査が失敗したとき所属処理が握りつぶさず reject するか、のテストがない | qa 🟡 |
| Codex のみ | `CLAUDE.md`(Repository 経由)と DESIGN(Service のデータアクセスを許容)の食い違い | `NEEDS_CONFIRMATION` として保持。Claude は既存パターンとして `COMPLIANT` と判断 |
| Codex のみ | E2E の証拠種別の切り分け(HTTP / 画面 / モック化した controller e2e)、403・404・428 を新しい 422 の証拠に数えない、操作者と対象者の所属を分ける | e2e |

## 進め方の差(品質の観点)

- 読み込み: Codex の e2e は関連 E2E 8本を全文確認。Claude の e2e は1本を全文、他は grep のみで、`CLAUDE.md` も未読のまま判定した。Claude の qa・cr・adv は `CLAUDE.md` を実読。
- 相談役: Claude の adv は React・Nest を実起動、data-platform は `NOT_APPLICABLE`。Codex の adv は React・Nest・永続化の3つを起動。Claude の qa は相談役なし、Codex の qa は React・Nest を使用。
- 重み付け: 同じ事実でも、一次情報を引用して重く扱う(Codex)か、未実行として控えめに扱う(Claude)かの差が出た。
- 質問の整理: Claude の adv はユーザー向けの判断質問(Q1〜Q3)を明確に切り出した。

## 学び(XREV-1 の根拠)

レンズの本文は `.claude/knowledge/engineering-governance.md`(`.claude-company` に同一の複製あり)の `### XREV-1: Cross-model review calibration lenses` を参照。トリガーされた場合のみ使う点検補助で、新しい層・承認ゲート・自動連鎖・実行権限は加えない。要点は、モックされた境界は呼び出しを証明するだけで到達は証明しないこと、全書き込み経路の列挙、既存データの扱い、新しい行ロックの互換性確認、入力表記の契約、プロジェクト規則の実読、一次情報の引用。

## レビュー後のユーザー判断(handoffの重み)

- 利用者の判断(2026-11-05): 実際に修正されるのは🟢 Low以上の指摘であり、handoffは自動の層連鎖がないため誰も実行しない。handoffを軽く扱いすぎているので、重みを持たせる。
- 根拠はこのPR 1件(n=1)の比較だけ。CodexのCRは Toaster 欠落と openapi 未更新を handoff のみに載せ、ClaudeのCRは同じ事実を🟡の指摘として報告した。
- HND-1: ①ソース証拠(path:line)で欠陥・仕様不一致を示せるなら、他層の領域でも自層の指摘(最低🟢 Low)にして修正担当を明記する。②handoffは自層の証拠で確定できないこと(実行・他層の判断・製品判断)に限り、必ず🔴/🟡/🟢の重みと一行理由を付け、担当の解消・撤回証拠なしに下げない。
- ③🟢 Low の1層1回5件の上限は維持する。超過分は🟢重みの handoff として追跡し、Info にしない。④🟡/🔴の未解決 handoff がある間は、その層は `APPROVE` 系(`L1.5_APPROVE`/`L1.5_APPROVE_WITH_NOTES`/L2 `APPROVE`/workflow `decision: APPROVE`)を返さず、`NEEDS_CONFIRMATION` で止める。🟢のみなら従来どおり。
- 本文は governance の `XREV-1` 内 `HND-1`。ツール側(`tools/review_receipts.py`)では、新規 handoff の `weight` 必須、未解決行の重み引下げ拒否、🟡/🔴未解決時の承認拒否を機械検証する。
- 利用者の判断(2026-11-05・承認ラベルの境界): Info だけが残る(未解決の指摘も handoff もない)場合は清浄な承認(CR は `L1.5_APPROVE`、ADV は `APPROVE`)。`L1.5_APPROVE_WITH_NOTES`(CR のみ)は、未解決の指摘がなく、残りが根拠付きで他層へ割り当てた🟢重みの handoff だけの場合に限る。ADV に notes ラベルは設けない。
- 未解決の🟢 Low は(`DEFER` と分類していても)承認系ラベルを返さず、`L1.5_REQUEST_CHANGES` / `REQUEST_CHANGES` にする。Low は追跡・修正・再レビューする指摘であり、`DEFER` は修復サイクル内の修正の優先度・時期を表すだけである。ツール側(`validate()`)は承認時に `open_item_ids` が空であることを既に要求しており、変更しない。
- Info は一度 Info と分類したら Low に格上げ・付け替えしない。分類は初回報告の証拠で1回だけ行い、証拠付きの欠陥・不一致は Info にしない(上限超過分を🟢 handoff にするのは Info の格上げではない)。修正で新たに生じた Low は新規の分類で `Origin: FIX_INDUCED` とする(Origin と再レビュー上限は従来どおり)。
