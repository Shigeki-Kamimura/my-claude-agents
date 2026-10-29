# トークン使用量の台帳

**レビュー・実装時に読み込まない。コスト分析のときだけ読む。** エージェントは、この台帳を読んだり、追記を求められたりしません。
governance のようにエージェントの初回読み込みに混ざると、固定費が増えるためです。これはレビューの規則ではなく、人が後日使う記録です。

実測値を貯めて、固定費の削減施策の効果を後で判断するために使います。
秘密、個人情報、顧客名は書きません。リポジトリ名やブランチ名も、書いてよい範囲だけにします。

## 記録手順(任意の後処理)

1. 親セッションの JSONL を探します。通常は `~/.claude/projects/<プロジェクトのパスを - でつないだ名前>/<session_id>.jsonl` です。
   子 agent の記録は同じ場所の `<session_id>/subagents/agent-*.jsonl` にあり、集計に含まれます。
   `CLAUDE_CONFIG_DIR` を分けた環境では、その配下の `projects/` を見ます。
2. 次のコマンドで、表の1行を作って末尾へ追記します。台帳を読む必要はありません。
   ```bash
   python3 -I -B tools/summarize_claude_session.py <親セッション.jsonl> --ledger-row \
     --workflow "codex-claude-review" --repo-branch "<repo>@<branch>" --snapshot "<短いSHA>+作業ツリー" \
     --round "初回" --layers "cr,qa,e,adv" --layer-models "cr/qa/e:sonnet, adv:opus" \
     --findings "0/1/2" --verdict "REQUEST_CHANGES" --note "計測方法など" \
     >> .claude/knowledge/token-usage-ledger.md
   ```
   - 貼り付けだけにしたい場合は、`>>` 以降を外して標準出力を確認します。このスクリプトは台帳を書き換えません。
   - 自動で埋まるのは、日付、モデル別のトークン、子の新規起動数、`SendMessage` 数です。他の列は引数で渡した値になり、省略すると空欄です。
   - 層ごとのモデルと層別のトークンは、子の記録の `agent-*.meta.json` の `agentType` で分類して自動入力されます(`--layer-models` を渡すと上書き)。層別は備考に入ります。メタ情報がない子は「不明」です。ラウンド別には分けません。
3. 比較は、同じ snapshot と同じ層の組み合わせで行います。条件が違う行どうしで削減率を出しません。

## 列

| 列 | 内容 |
| --- | --- |
| 日付 | 記録した日 |
| ワークフロー | `codex-claude-review` / `claude-codex-review` / `standalone cr` など |
| リポジトリ/ブランチ | 対象 |
| snapshot | 短い SHA と、作業ツリーの未コミット変更の有無 |
| ラウンド | 初回、または再レビュー n |
| 実行した層 | `cr` / `qa` / `e` / `adv` / `rev`。再確認だけの層は括弧で示す |
| 層ごとのモデル | 自動(`--layer-models` で上書き) |
| input / output / cache read / cache write | モデル別のトークン数 |
| 子の新規起動 | `Agent` 呼び出しの数 |
| SendMessage | 子の再開の数 |
| 🔴/🟡/🟢 | 指摘件数 |
| 最終判定 | native verdict |
| 備考 | snapshot が変わったか、再確認で差分だけを見たか、計測方法 |

| 日付 | ワークフロー | リポジトリ/ブランチ | snapshot | ラウンド | 実行した層 | 層ごとのモデル | input | output | cache read | cache write | 子の新規起動 | SendMessage | 🔴/🟡/🟢 | 最終判定 | 備考 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-27(参考) | 旧運用(参考) | | | | cr,qa,e,adv | | | | | | 23 | | | | 旧運用・直接比較不可。API応答 540 回、約 36 米ドル(`docs/claude-subagent-resume-benchmark.md`)。 |
