# Claude Code子agent再開のA/B計測（2026-10-27）

## 比較対象
- A（従来）: exp/xml-agents
- B（再開を明示）: exp/claude-child-resume-benchmark-1027
- 対象: Codexが実装し、Claude CodeがCR→QA→E2E→ADVを担当するワークフロー
- 守ること: 西口さんのレビュー原則、happy/fail確認、🟢を含む全指摘、現行モデル・effort・権限、独立した4段階承認

Bは同一phaseの再レビューで、Claude親を--resumeし、子をSendMessageで再開する指示です。
公式ドキュメントでは、子の終了後も会話履歴を使って再開できると説明されています。
ただし、実行環境で動くか、利用量が減るかは未確認です。

## 1. 新しいProアカウントを既存環境から分離

WSLのターミナルで以下を実行します。

~~~bash
unset ANTHROPIC_API_KEY
export CLAUDE_CONFIG_DIR="$HOME/.claude-pro-resume-benchmark"
claude --version
claude auth login
claude auth status
~~~

Claude Code v2.1.304以降を使います。古い版は、終了直後に子agentを再開した場合の履歴欠落問題が報告されています。
CLAUDE_CONFIG_DIRは認証・設定・セッション履歴の保存先を分ける公式機能です。
コマンドを実行するCodexも、同じ環境変数を継承するWSLターミナルから起動してください。
VS Code拡張やデスクトップ版を別のプロセスから起動すると、この環境変数を継承しない場合があります。
認証情報や生の会話ログは共有しないでください。

## 2. 作業プロジェクトをA/Bで分ける

設定リポジトリ本体のブランチを切り替えないでください。
すでにシンボリックリンクがある通常案件にも影響するためです。

~~~bash
BASE="$HOME/claude-review-benchmark"
mkdir -p "$BASE/A" "$BASE/B"
git clone -b exp/xml-agents git@github.com:Shigeki-Kamimura/my-claude-agents.git "$BASE/A/config"
git clone -b exp/claude-child-resume-benchmark-1027 git@github.com:Shigeki-Kamimura/my-claude-agents.git "$BASE/B/config"

git clone git@github.com:k-platinum/guildboard-training-management.git "$BASE/A/project"
git clone git@github.com:k-platinum/guildboard-training-management.git "$BASE/B/project"
PIN_SHA="$(git -C "$BASE/A/project" rev-parse HEAD)"
git -C "$BASE/A/project" checkout --detach "$PIN_SHA"
git -C "$BASE/B/project" checkout --detach "$PIN_SHA"
bash "$BASE/A/config/setup.sh" --profile company "$BASE/A/project"
bash "$BASE/B/config/setup.sh" --profile company "$BASE/B/project"
~~~

両側へ同じコード差分を用意します。差分とbase SHAを記録し、実装済みの同じ変更をレビューさせます。
未コミットの実案件を直接使わず、検証用コピーを使います。

## 3. 最初はBで再開のスモークテスト

1. Bのprojectへ移動します。同じWSLターミナルからclaudeとCodexを起動します。
2. Claudeの親から、対象のカスタムagentを一度呼びます。親session_idと子agent_idを記録します。
3. 再依頼では、親を--resumeで開きます。同じ子agent_id宛のSendMessageで続行させます。
4. 新しいAgentの呼び出しが増えず、SendMessageが発行されたかをログで確認します。
5. SendMessageが使えない場合はBLOCKEDにします。新しいAgentで代替して再利用成功と報告しません。

CR、QA、E2E、ADVはそれぞれ独立した初回セッションと子agentが必要です。
再利用するのは同じphaseの担当だけです。後続phaseの修正による再承認も対象です。
以前の承認結果だけで新snapshotを承認することはできません。

## 4. A/B比較

AとBで同じプロンプト、同じsnapshot、同じモデル、同じCLI版を使います。
同じphase内で2回以上のレビューをさせることが必要です。指摘が出た場合は同じ修正を両側に適用してください。
結果を比較する際は、未確認範囲や指摘が適切に引き継がれていることも確認します。

計測項目:
- 親と子のAPI応答数
- 子Agent新規起動数、SendMessageによる再開数
- モデル別のinput・output・cache read・cache writeトークン数
- /usageまたはCLIの推定コスト
- CR/QA/E2E/ADVの確認範囲・指摘・最終判定

23回の子起動、540 API応答、36米ドルという前回の数字は参考値です。
今回のA/Bと条件が違うため、直接比較して削減率を出してはいけません。
比較の第一条件はレビューの品質を落とさないことです。

## 5. ログの集計

新アカウントのログは以下に保存されます。

- 親: $CLAUDE_CONFIG_DIR/projects/<project-key>/<session-id>.jsonl
- 子: $CLAUDE_CONFIG_DIR/projects/<project-key>/<session-id>/subagents/agent-<agent-id>.jsonl

セッションの終了後に、親JSONLのパスを指定して集計します。

~~~bash
python3 "$BASE/B/config/tools/summarize_claude_session.py" \
  "/absolute/path/to/parent-session-id.jsonl" \
  > "$BASE/B/measurement.json"
~~~

集計スクリプトは、同一API応答が複数行に分割されていてもmessage.idで重複計上を避けます。
プロンプトやコードの本文は出力しません。CR・QA・E2E・ADVの親セッションごとに実行してください。
JSONLはClaude Codeの内部形式です。将来のCLI更新では形式が変わる可能性があります。

Claude Proの/usageに表示されるドル額は、API定価に基づく見積りです。
サブスクリプションの実際の請求額と混同しないでください。

## 中止条件

BでSendMessageが使えない、agent IDが変わる、子の履歴が失われる、レビュー義務が欠ける場合は中止します。
利用量の上限に達しても承認へ読み替えず、状態を保存してBLOCKEDとします。
まず子再開が機能することを確認し、その後に品質とトークン量を測ります。

## 参照資料
- Anthropic, Create custom subagents: https://code.claude.com/docs/en/sub-agents#resume-subagents
- Anthropic, CLI reference: https://code.claude.com/docs/en/cli-reference
- Anthropic, Environment variables: https://code.claude.com/docs/en/env-vars
- Anthropic, Manage costs effectively: https://code.claude.com/docs/en/costs
