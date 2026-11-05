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

効果の確認(2回目の再レビュー)の結果と、そこで見つかった弱点への対応は、末尾の「2回目の再レビュー(規則適用後の効果確認)」節を参照。

## レビュー後のユーザー判断(handoffの重み)

- 利用者の判断(2026-11-05): 実際に修正されるのは🟢 Low以上の指摘であり、handoffは自動の層連鎖がないため誰も実行しない。handoffを軽く扱いすぎているので、重みを持たせる。
- 根拠はこのPR 1件(n=1)の比較だけ。CodexのCRは Toaster 欠落と openapi 未更新を handoff のみに載せ、ClaudeのCRは同じ事実を🟡の指摘として報告した。
- HND-1: ①ソース証拠(path:line)で欠陥・仕様不一致を示せるなら、他層の領域でも自層の指摘(最低🟢 Low)にして修正担当を明記する。②handoffは自層の証拠で確定できないこと(実行・他層の判断・製品判断)に限り、必ず🔴/🟡/🟢の重みと一行理由を付け、担当の解消・撤回証拠なしに下げない。
- ③🟢 Low の1層1回5件の上限は維持する。超過分は🟢重みの handoff として追跡し、Info にしない。④🟡/🔴の未解決 handoff がある間は、その層は `APPROVE` 系(`L1.5_APPROVE`/`L1.5_APPROVE_WITH_NOTES`/L2 `APPROVE`/workflow `decision: APPROVE`)を返さず、`NEEDS_CONFIRMATION` で止める。🟢のみなら従来どおり。
- 本文は governance の `XREV-1` 内 `HND-1`。ツール側(`tools/review_receipts.py`)では、新規 handoff の `weight` 必須、未解決行の重み引下げ拒否、🟡/🔴未解決時の承認拒否を機械検証する。
- 利用者の判断(2026-11-05・承認ラベルの境界): Info だけが残る(未解決の指摘も handoff もない)場合は清浄な承認(CR は `L1.5_APPROVE`、ADV は `APPROVE`)。`L1.5_APPROVE_WITH_NOTES`(CR のみ)は、未解決の指摘がなく、残りが根拠付きで他層へ割り当てた🟢重みの handoff だけの場合に限る。ADV に notes ラベルは設けない。
- 未解決の🟢 Low は(`DEFER` と分類していても)承認系ラベルを返さず、`L1.5_REQUEST_CHANGES` / `REQUEST_CHANGES` にする。Low は追跡・修正・再レビューする指摘であり、`DEFER` は修復サイクル内の修正の優先度・時期を表すだけである。ツール側(`validate()`)は承認時に `open_item_ids` が空であることを既に要求しており、変更しない。
- Info は一度 Info と分類したら Low に格上げ・付け替えしない。分類は初回報告の証拠で1回だけ行い、証拠付きの欠陥・不一致は Info にしない(上限超過分を🟢 handoff にするのは Info の格上げではない)。修正で新たに生じた Low は新規の分類で `Origin: FIX_INDUCED` とする(Origin と再レビュー上限は従来どおり)。

## 2回目の再レビュー(規則適用後の効果確認)

実施日: 2026-11-05。条件は1回目と同じ(同じスナップショット `80c900af`、同じブリーフ、同じ8本)。違いは、`XREV-1`・`HND-1`・承認ラベルの境界が反映済みであること。1回目の出力は担当に読ませていない。IDの接頭辞は `CL2-` / `CX2-`。

### 効果の確認

| 確認項目 | 結果 |
|---|---|
| 規則の読み込み | 全8本が更新後のガバナンス(SHA-256 `8d238fde…`)を報告。古いプリロードのまま動いた層はない。 |
| 根拠のある不一致が指摘になるか(`HND-1` ルール1) | 効いた。1回目の Codex の cr は Toaster の欠落と仕様書の未更新を handoff のみにしたが、2回目は両方を 🟡 の指摘にした。Codex の qa も、Toaster・監査 `source`・仕様書を自分の指摘に加えた。 |
| handoff の重み | 全8本に 🔴/🟡/🟢 と理由が付いた(1回目の cr は重みなし)。 |
| 開いた Low と承認ラベル | 全8本が `REQUEST_CHANGES` 系。ただし全層に 🟡 以上の指摘があり、この規則だけを試験できてはいない。 |
| `XREV-1` の観点 | adv で顕著。Claude の adv は data-platform を起動し、監査ログの外部キー確認ロックが絡む循環待ちを指摘にした(1回目は `NOT_APPLICABLE` として見落とし)。Codex の adv は、1回目に「既存経路」として見送った `POST /admin-members` の抜け道を 🟡 の指摘にした。 |

### 指摘数の推移

| 層 | Claude 1回目 | Claude 2回目 | Codex 1回目 | Codex 2回目 |
|---|---|---|---|---|
| qa | 🟡1・Low4 | 🟡2・Low5・🟡 handoff1 | 🟡3 | 🟡4・Low3・🟡 handoff3 |
| e2e | 🟡2・Low2 | 🟡2・Low2 | 🟡2 | Low3・handoff(🟡1・🟢1) |
| cr | 🟡4・Low3 | 🟡3・Low4・handoff3 | 🟡1・Low2・handoff(重みなし) | 🟡4・Low2・🟡 handoff3 |
| adv | Blocker2・Should4・Low4 | 🟡3・Low5 | 🟡5・Low1 | 🟡4・Low5 |

### 効きが弱かった点と対応

1. Claude の e2e だけが、`OPS-1`/`XREV-1`/`HND-1` の本文を実読せず、作業コピーの `CLAUDE.md` も読まず、関連 E2E を全文ではなく grep で確認した。Claude の qa・cr・adv は本文を実読した。原因として、`HND-1` が常時適用の規則なのに Claude 側のプリロードに含まれず、定義の1文の参照に頼っている点が考えられる。対応: Claude の4層(test-qa / e2e-qa / code-quality-reviewer / adviser、両プロファイル)の定義の `XREV-1` の行に、判定前に `XREV-1` と `HND-1`(`HND-1` は常時適用で、トリガー式の観点ではない)をガバナンスから、あわせてプロジェクト規則の該当節(作業コピーの `CLAUDE.md` など)を実際に読み、定義だけに頼らず、読んだ内容を `Rules loaded` に書く旨を追記した。Codex の定義は変更していない(プリロードで受け取るため)。
2. 同じ事実の重みがモデル間でぶれた。e2e の「自動昇格の欠落」「super による `PATCH /members/:id` の 422 の欠落」は、Claude が 🟡、Codex が Low(1回目は両者とも 🟡)。cr の「422 が通信失敗文言に落ちる」は、Claude が 🟡 から Low に、Codex が Low から 🟡 に動いた。1回の実行では、規則の影響か実行ごとのばらつきかは区別できない。対応: `XREV-1` の qa・e2e の観点に、PR 自身が中心の変更と述べる振る舞い(新しい拒否分岐・副作用・応答項目など)を旧挙動と区別できるテストがない欠落は、少なくとも 🟡 とする観点を追加した。これは証拠に基づく下限であり、証拠なしに重みを上げる規則ではない。周辺の統制・文言・副次的な否定ケースの欠落は 🟢 Low でよい。理由は1行で記録する(共通規則「重みと Blocker/Should の区分が異なる場合は理由1行」に従う)。Codex 側は、再生成したプリロード経由で同じ文を受け取る(Codex の定義は変更していない)。

### 限界

- PR 1件、各条件1回ずつ(n=1)。モデルや規則の優劣は断定できない。
- 各指摘のコード検証は行っていない。両モデルが一致した指摘は信頼度が高く、片側だけの指摘は主張として扱う。
- Claude 側のサブエージェントのトークンは合計約64万(1回目は約56万)。Codex 側と利用枠の消費は NOT_MEASURED。
- 「Info のみなら `APPROVE`」「🟢 の handoff のみなら `L1.5_APPROVE_WITH_NOTES`」の境界は、全層に 🟡 以上の指摘があったため、今回も試験できていない。修正後の再レビューで試す(未実施)。
- D: 修正後の再レビューは未実施(GuildBoard 側に修正が入っていないため)

### GuildBoard 側の判断事項(両モデルの adv が独立に提起)

自動で公開範囲を広げる前の告知・同意の要否、既存の「組織所属かつ `self`」行の移行要否、`CLAUDE.md`(Repository 経由)と `DESIGN.md`(Service のデータアクセス許容)の優先順位。いずれもプロジェクト側の製品・規約の判断で、本リポジトリでは決めない。

## 3回目の再レビュー(修正差分 80c900af..c61b599ff)

実施日: 2026-11-05。利用者の依頼で hq-coder が指摘を修正し、その修正差分を、新しい8本(Claude と Codex それぞれの qa / e2e / cr / adv)が再レビューした。2回目までと同様、前回の出力は担当に読ませていない。

### 修正の内容と範囲

- 修正は隔離したクローンのブランチ `fix/pr1024-review-findings` で行った(7コミット・30ファイル・+1387/-149)。
- 実行したのは Biome のみ。tsc / jest / vitest / Playwright は NOT_RUN。E2E は書いたが NOT_RUN。
- 意図的に直していない項目: Q1(事前告知)、Q2(既存行・変更なしの自己更新)、Q3(admin-members の自己操作)、`CLAUDE.md` と `DESIGN.md` の優先順位、status-transitions のロック順序。

### 結果

| 層 | Claude 2回目 → 3回目 | Codex 2回目 → 3回目 |
|---|---|---|
| qa | 🟡2・Low5 → 🟡1・Low3 | 🟡4・Low3 → 🟡3 |
| e2e | 🟡2・Low2 → Low2 | Low3 → Low1 |
| cr | 🟡3・Low4 → 🟡1・Low1 | 🟡4・Low2 → 🟡4・Low1 |
| adv | 🟡3・Low5 → 🟡1・Low2 | 🟡4・Low5 → 🟡1・Low3 と 🟡 UNCONFIRMED 1 |

- 報告された指摘はすべて `FIX_INDUCED` で、前回の指摘が未解決と報告された例はない(`PRIOR_FINDING` なし)。
- 承認ラベルを返した層はない。全層に 🟡 または Low が残ったため。したがって「Info のみなら `APPROVE`」「🟢 の handoff のみなら `L1.5_APPROVE_WITH_NOTES`」の境界は今回も試験できていない。一方「未解決の Low があれば承認系ラベルを返さない」は全8本で守られた。Claude の e2e は Low のみで `REQUEST_CHANGES` を返した。

### 両モデルが見つけた指摘(信頼度が高い)

- `CreateOwnOrganizationPage` の完了画面が、`fetchCurrentUser` で利用者が staff に変わった後に、`AuthGuard` の「アクセス権がありません」表示に置き換わる。cr と adv が両モデルで発見した(qa / e2e は未発見)。修正側のテストは AuthContext をモックしていたため、この経路を検出できなかった。
- `fetchCurrentUser` をミューテーションの外へ移したことで生じた再送信の窓(二重送信)。
- 参加時のキャッシュ無効化のテストがない。
- 手動の `updated_at` 更新が `DESIGN` の禁止事項に反する。
- ブラウザ水準の E2E がない。

### 片方だけが見つけた指摘

- Codex のみ:
  - テストコードの欠陥2件。`member-visibility-policy.spec` が `toThrow(日本語の文字列)` で検証しているが、`UserVisibleError.message` は固定ラベル `Displayable error`(クラスを読んで確認)。`InviteAcceptPage.visibilityNotice.test` が、`clearMocks:false` の vitest 設定下でモジュール単位の `vi.fn` の呼び出し履歴を共有している(設定を読んで確認)。どちらも実行はしていない。
  - 画面仕様書の README が未更新。
  - メールアドレスの同時変更によるロック昇格の疑い(UNCONFIRMED)。Claude の adv は「新しい窓はない」と判断しており、判断が割れたまま残る。
- Claude のみ:
  - `/me/visibility` が `updated_at` を更新せず、ETag 契約の別の書き込み経路になっている。
  - `ProfileVisibilityControl.test` に、起こり得ない文言への否定アサーションが残り空振りしている。
  - `fetchCurrentUser` の通知以外の失敗経路にテストがない。

### 進め方

- 全8本が同じガバナンス(SHA-256 `d627fe4c…`)を報告した。
- Claude の e2e は、今回も作業コピーの `CLAUDE.md` を十分に読まなかった。

### 学びと反映

上記の「片方だけ」の指摘を、トリガー式の観点として `engineering-governance.md` の `XREV-1` 表に追加した(両 profile 同一)。

- 既存の行に統合: ADV「不変条件」の行に ETag/版管理の契約の全書き込み経路の列挙を、ADV「行ロック」の行にロックモード変更と昇格・不一致の記録を含めた。
- 新しい行: QA + CR(カスタムエラー型のマッチャー、共有モックのリセット)、QA(陳腐化した既存テスト、置き換えたプロバイダ)、E2E(ブラウザ経路の欠落)、CR + ADV(認可状態の更新とガード)、ADV(画面仕様書)。

### 限界

- PR 1件、各条件1回(n=1)。各側に見落としがあり、どちらのモデルが一般に優れているとは言えない。
- 実行による検証はしていない。テストコードの欠陥2件のみ、クラスと設定を読んで確認した。それ以外の指摘は主張として扱う。
- Claude 側のサブエージェントのトークンは合計約65万。Codex 側と利用枠の消費は NOT_MEASURED。

## XREV-1/HND-1 の見直し条件(A/B)

### 判断(ユーザー)

- XREV-1 の層別の観点は今のまま残す(方針A)。ただし効果は未証明の実験扱いとし、別の PR で観点あり・なしを比べて見直す。
- HND-1 は承認ラベル・handoff の契約なので A/B の対象外ではなく、基準側に含めない形で一緒に比べる。基準 `38bdf27` は XREV-1・HND-1・承認ラベル境界のいずれも含まない。したがって比較するのは「XREV-1+HND-1+承認ラベル境界のまとまり」と基準の差であり、XREV-1 単体の効果ではない。

### 対象と実行範囲

- 対象 PR: GuildBoard PR #1025(マージコミット `2b3a607c`、ベース `cdb03927`)。frontend のみ 7ファイル +83/-7(AuthGuard・Layout・Breadcrumb・routes)。
- Codex(ユーザー選択): 観点あり4本・なし4本。該当コミットを別ディレクトリに展開して読ませた(観点あり=`01728a3`、なし=`38bdf27`)。
- Claude: 観点ありの4本のみ。観点なしは、古い定義がサブエージェントとして読み込まれることを確認できていないため作っていない。合計12本。

### 比べる点と判断基準(事前に固定)

- 比べる点: 見つけた欠陥の数と重み、片方だけが見つけた欠陥、承認ラベルの境界が働いたか、トークン使用量、規則の読み飛ばしの有無。
- 観点ありのほうが有効な欠陥を多く見つけ、誤検知やトークン増に見合うなら残す。差が見えなければ、費用に見合う行だけに絞る。効果が見えない行は削除する。
- 1件の PR(n=1)なので、結果だけで断定せず、さらに別の PR で再確認する。

### 限界(事前に記録)

- Claude に観点なしの対照がない。PR 1件・各条件1回。
- 指摘のコード検証は行わない。両条件で一致した指摘のみ信頼度高とする。
- Codex の2条件は同一モデル・同一ブリーフだが、実行ごとのばらつきがあり得る。
- 結果は「A/B の結果」として末尾に追記する。未追記の間は未実施。

### A/B の結果(PR #1025)

#### 条件と実行の事実

- 観点あり=`01728a3`(ガバナンス SHA `8a2641c6…`)、観点なし=`38bdf27`(同 `2a9593ae…`)。Codex は両条件を別ディレクトリの写しから読ませた。Claude は観点ありのみ。
- 全員が作業コピーの CLAUDE.md を実読したと報告した。例外は Claude の e2e で、CLAUDE.md を読まず、XREV-1/HND-1 の本文も自分では読んでいない。
- 承認ラベルの境界(開いた Low があれば承認系ラベルを出さない)は観点あり側のみに存在する。

#### 層ごとの結果

| 実行 | qa | e2e | cr | adv |
| --- | --- | --- | --- | --- |
| Codex 観点あり | COMMENT / 🟡1(ギルドボードのルートに `requireOrganization` が付いたことを区別するテストがない) | REQUEST_CHANGES / 🟡1(同じ配線を実ルートで拒否するブラウザ経路がない)+🟢1(Layout→Breadcrumb の実結合) | L1.5_APPROVE(指摘・handoff なし) | REQUEST_CHANGES / 🟢Low1(無所属の本人プロフィールの戻りボタンが開けない画面に向かう) |
| Codex 観点なし | APPROVE(指摘なし) | COMMENT / 🟡1(同じ配線を実ルートで拒否するブラウザ経路がない) | L1.5_APPROVE_WITH_NOTES(未解決 handoff 2件 PENDING) | DEFER / Low1(戻りボタン。観点ありの adv と同一) |
| Claude 観点あり | REQUEST_CHANGES / 🟡1(ルート配線のテスト欠落。XREV-1 の中心変更の下限を根拠に明記)+Low1 | 🟡1(同じ)+🟢1 | L1.5_REQUEST_CHANGES / 🟡2(同上、画面仕様・権限仕様 `PERMISSION_MANAGEMENT.md` と `screens/README.md` の未更新)+Low3(戻りボタン、無所属判定の4箇所重複、AuthGuard のコメントが旧い範囲) | REQUEST_CHANGES / 🟡2(同上)+Low3(戻りボタン、1段だけのパンくずの重複表示、AuthGuard のコメント) |

Claude は e2e を含む全4層に 🟡 以上があった。

#### 量

- Claude サブエージェントのトークン: e2e 約8.3万、qa 約12.0万、cr 約12.9万、adv 約18.6万、合計約51.7万。#1024 の3回目は約65万だが、PR の大きさが違うので単純比較しない。Codex は NOT_MEASURED。
- 出力量の目安(参考値のみ): Codex 観点あり4本 約29.6KB、なし4本 約26.8KB。

#### 読み取り(断定しない)

- 差が見えた点
  - Codex qa は、なしでは APPROVE(指摘なし)、ありでは XREV-1 の中心変更の下限により 🟡 としてルート配線のテスト欠落を指摘した。ただし同じ欠落は、なしの e2e も 🟡 で見つけている。したがって「観点あり側が新しい欠陥を見つけた」のではなく、「同じ欠陥を担当の層(qa)が拾うようになった」差である。
  - adv が Low だけを残したとき、なしは DEFER、ありは REQUEST_CHANGES だった。承認ラベルの境界が働いたと見える。
  - cr は、なしが APPROVE_WITH_NOTES(未解決 handoff 2件)、ありが APPROVE(指摘・handoff なし)で、ありのほうが指摘が少なかった。
- 差が見えなかった点
  - 戻りボタンの導線は、両条件の Codex adv と Claude の cr・adv が一致して見つけた。
  - Codex は観点あり・なしとも、画面仕様・権限仕様の未更新を指摘にしなかった(XREV-1 の「画面仕様の文書を確認する」観点があっても)。Claude は cr・adv の2層が 🟡 で指摘した。
- 注意: Codex の観点あり cr は指摘なしで L1.5_APPROVE を出したが、Claude の cr は同じスナップショットに 🟡2・Low3 を挙げている。どちらが正しいかは検証していない。この差は観点の有無ではなくモデル差である可能性があり、観点あり側の承認を「正しい承認」とは扱わない。

#### 判定

- 事前に固定した判断基準に照らすと、観点ありが「有効な欠陥を多く見つけた」とはまだ言えない。Codex の2条件で見つけた欠陥の集合に新しいものは増えていない(観点ありの e2e の 🟢1 は未検証の観察で、欠陥とは扱わない)。一方、承認ラベルの境界と、中心変更の下限による担当層の振り分けは働いたように見える。
- 判定: 観点は削除しない。ただし効果は未確認のまま継続し、別の PR(バックエンドを含むもの)でもう1回比べて決める。

#### 限界

- n=1・各条件1回。Claude に観点なしの対照なし。指摘のコード検証なし。
- 基準 `38bdf27` は XREV-1+HND-1+承認ラベルの境界をまとめて含まないので、効果を行ごとに切り分けられない。
- frontend のみの PR で、backend 用の観点(ロック、監査、非同期)は試せていない。
