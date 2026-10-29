# Codex → Claude Codeレビューの実機検証

更新: 2026-10-29。対象ブランチ: `exp/xml-agents`。

## 状態

合成JSONLによる自動テストを`tests/test_render_review_record.py`と`tests/test_review_efficiency_report.py`に追加しました。ただし、**CodexとClaude Codeの実際の起動ログは未取得**です。合成ログのテストは、実機の起動やコードレビューの品質を保証しません。

## 事前確認

同じWSLターミナルでCLI・認証・バージョンを確認します。実案件の編集途中のワークツリーを使わず、`$HOME`内の隔離したクローンで確認します。

```bash
command -v codex && codex --version
command -v claude && claude --version
claude auth status
AGENTS="$HOME/projects/my-claude-agents"
git -C "$AGENTS" rev-parse --abbrev-ref HEAD
git -C "$AGENTS" status --short
python3 -B -m unittest discover -s "$AGENTS/tests" -p 'test_*review*.py' -v
```

レビュー前後でbase SHA、HEAD、未コミット差分、index、適用規則の版、model/effortを記録します。`setup.sh` は `.git/info/exclude` を使用し、既存の `.gitignore` は変更しません。

## 3つの実機ケース

| ケース | 方法 | 必須の証拠 |
| --- | --- | --- |
| 1. CR初回 | Codexへ「Claude CodeにL1.5レイヤーでレビューしてもらって」と依頼。隔離した既知不具合の差分を用います | 親session ID、実子agent ID、初回Agent、既知不具合と指摘、規則確認、未確認範囲 |
| 2. CR再レビュー | Codexが一括修正後、同じCRへ再レビューを依頼。親は `--resume`、元の子は `SendMessage` で再開します | 同じ親/子ID、Agentの増分、SendMessageの応答、修正前後のsnapshot、同一範囲の再読込み候補 |
| 3. ADV専門相談 | React状態とNestJSのAPIをまたぐ隔離差分についてL2レビューを依頼 | Opus担当の実起動、React/Nest両専門家の独立相談、質問の担当範囲、重複調査、結論と根拠 |

レビューには既知の不具合を含むケースと問題のないケースを用意し、検出漏れと誤検知の両方を記録します。QA/E2Eに該当する変更ではhappy/fail両面を確認します。四層承認を行う場合は `qa → e2e → cr → adv` の順で、最終的な同一snapshotへの確認を守ります。

## HTMLとトークン記録

実行済みの親JSONLの正確なパスを指定します。子JSONLは親と同じセッションの `subagents/` から自動取得します。

```bash
AGENTS="$HOME/projects/my-claude-agents"
OUT="$HOME/review-audit/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
CODEX_LOG="/absolute/path/to/codex-rollout.jsonl"
CLAUDE_LOG="/absolute/path/to/claude-parent.jsonl"

python3 -I -B "$AGENTS/tools/render_review_record.py" \
  --out "$OUT/record.html" --redact-personal --omit-thinking \
  "$CODEX_LOG" "$CLAUDE_LOG"
python3 -I -B "$AGENTS/tools/review_efficiency_report.py" \
  --out "$OUT/efficiency.html" "$CLAUDE_LOG"
python3 -I -B "$AGENTS/tools/summarize_claude_session.py" \
  "$CLAUDE_LOG" > "$OUT/usage.json"
```

リポジトリ外への保存を推奨します。リポジトリ内では、`.git/info/exclude` が除外した `.codex/review-records/` だけを許可します。既存の `.gitignore` は参照しません。HTMLはUnix上で0600権限です。

時系列HTMLには、伏せ処理後も業務情報や個人情報が残る可能性があります。共有前に人間が全文を確認します。生ログをPR/Issueに添付しません。集計HTMLには原則として会話本文を含めません。

## 比較と合格条件

- `review_efficiency_report.py` の「同じ範囲への再アクセス」は**無駄の候補**です。規則が変更された場合や、元の履歴が失われた場合の再確認は正当です。
- 別担当の初回規則確認や、同じ担当の別の行範囲の読み込みは、重複として数えません。検索と本文読込みも区別します。
- 新規Agent起動数、SendMessage数、モデル別input/output/cache read/cache writeを確認します。
- 消費量の比較では差分・プロンプト・CLI・モデル・baseを固定し、同条件で複数回試します。以前の「23子起動、540応答」は直接比較に使いません。
- 最終評価では検出漏れ・誤検知・指摘の解消・必須相談・coverageを検証します。トークンが減っても品質が落ちた場合は不合格です。
- 元の子を再開できない、CLI利用不可、ログ欠落、差分未確認、必須相談不足などは `BLOCKED` とします。成功と報告しません。

既存の`docs/claude-subagent-resume-benchmark.md`は2026-10-27の比較案です。現在の`exp/xml-agents`にも再開指示が追加されているため、**ブランチ名だけをA/B条件として再利用しないでください**。比較する場合は再開機能が導入される前と後の確定したコミットを使います。

## 参照

- [Anthropic: CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Anthropic: Subagents and resume](https://code.claude.com/docs/en/sub-agents#resume-subagents)
- [OpenAI: Codex non-interactive](https://developers.openai.com/codex/non-interactive)
