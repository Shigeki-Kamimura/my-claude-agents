# 実装ループと会話HTMLの保存

## 現在の状態

これは `exp/xml-agents` の `c55bb5546dd931a7ed8d474a8020da56d20fd241` を基準にした試行版です。
制御処理、外部レビュー用の起動処理、HTML保存処理を追加しています。
実Codex・Claude Code、ユーザーのDesktopではまだ検証していません。
既存の単独CR、PCR-1、双方向レビューは変更せずに残します。

この版のテストは模擬結果・模擬ログを使います。
モデルの遵守、検出率、料金、所要時間を証明するものではありません。
公開操作は別の許可にします。コードにcommit/push/PR作成の経路はありません。

## 親への依頼例

```text
implementation-reviewで、指定したタスクを実装から修正確認まで進めてください。
実装はCodex、PCRはCodex、QAはClaude、E2EはCodexにしてください。
L2はClaudeで行い、必要な独立した専門担当の確認も残してください。
修正は最大3ラウンドです。要件を決められなければ停止してください。
親と全担当の公開チャットを、実行ごとのHTMLへ自動保存してください。
テストの追加・修正・実行は実装担当だけが行います。
commit、push、PR作成、CIの起動、権限設定の変更は行わないでください。
```

QAとE2Eの担当先は別々に選べます。
同系統のモデルなら、結果に `self_check` と記録します。
別モデル必須の指定を、同系統の確認で満たした扱いにはしません。

親は新しい `implementation-review` スキルを使います。
Desktopの共有原本を読む構成では、追加する親向けの入口を使います。
スキル一覧に表示されない場合も、設定原本のパスから読めます。
ただし、実際に読めたかと起動できたかは別々に確認します。
専用TOMLや新しいエージェント種別は作りません。

## 保存するもの

最終的な要約だけを保存する方式ではありません。
依頼、各担当の応答、差し戻し、修正後の確認を記録します。
親、HQ、PL、CR-A、CR-B、検証担当、QA、E2Eが対象です。
L2と専門担当を実行した場合は、その会話も含めます。

保存先は、対象リポジトリの外です。例です。

```text
~/.codex/review-runs/guildboard/implementation-<run-id>/
├── index.html
├── review.md
├── state.json
├── records/
│   ├── record-000001.html
│   ├── record-000001.json
│   └── ...
└── job-000001/
    └── ...
```

`index.html` は最新の保存結果です。
`records/` には、各段階の上書きしない記録を残します。
JSONには、入力範囲、ハッシュ、欠落した担当などを残します。
状態の確定より先にHTMLを保存します。
保存に失敗した場合、次の担当は起動しません。

内部の思考欄、システム指示、暗号化された内容は表示しません。
保護された内容を含み得るツール引数も、HTMLでは省略します。
認証情報は、既存rendererのパターンで伏せます。
伏せ漏れがない保証はないため、外部共有前の確認は必要です。
ログやHTMLをGitへ追加したり、自動公開したりはしません。

途中停止や利用制限でも、取得できた会話を保存します。
取得できない会話は `PARTIAL` と担当IDを残します。
要約から会話を作り直したり、保存済みと偽ったりはしません。

## 制御用コマンド

通常は親がこれらを使います。ユーザーが毎回転記する想定ではありません。
すべて、設定リポジトリのルートから実行する例です。
`--parent-log` は、この実行に対応する実ログです。
`--parent-start` は、依頼の先頭行のbyte位置です。
過去の別タスクを含めないため、親が実記録から固定します。

```bash
python3 -B tools/implementation_review.py init \
  --project /absolute/path/to/project \
  --base <actual-base-sha> \
  --run-dir "$HOME/.codex/review-runs/project/unique-run" \
  --policy docs/examples/implementation-review-policy.json \
  --request-file /absolute/path/to/authorized-request.md \
  --rules /absolute/path/to/project/CLAUDE.md \
          /absolute/path/to/config/.claude/knowledge/engineering-governance.md \
          /absolute/path/to/config/.claude/knowledge/parallel-cr-review.md \
          /absolute/path/to/config/.claude/knowledge/implementation-review.md \
  --parent-log /absolute/path/to/current-parent.jsonl \
  --parent-start <verified-byte-offset>
```

実際には、変更と担当に適用する規約も `--rules` に加えます。
例に書かれている4ファイルだけで十分とは限りません。
秘密情報を含むファイルは、既存のsnapshot規則に従って除外します。

次の依頼は `next`、起動の確保は `claim` です。

```bash
python3 -B tools/implementation_review.py next --run-dir <run>
python3 -B tools/implementation_review.py claim --run-dir <run> --job-id <job-id>
```

HQの実装後は、現在の対象を `snapshot` で取得します。
実装側の検証記録を添え、`finish-hq` で申告します。
申告は独立レビューの承認にはなりません。

```bash
python3 -B tools/implementation_review.py snapshot --run-dir <run>
python3 -B tools/implementation_review.py finish-hq \
  --run-dir <run> --job-id <job-id> --result-file <hq-result.json>
```

外部CLIでのレビューは、まず計画だけを表示します。

```bash
python3 -B tools/start_implementation_review_task.py \
  --run-dir <run> --job-id <job-id>
```

開始時の許可に含まれる担当だけ、`--apply` で実行します。
元のnative担当を再開する依頼を、外部の別担当に置き換えません。
Claudeの別層を追加する確認が必要な場合も、そのまま停止します。
許可なく `--confirm-more-claude-layers` を付けて回避してはいけません。

native担当の結果を取り込む場合は、実ログを指定します。

```bash
python3 -B tools/implementation_review.py finish \
  --run-dir <run> --job-id <job-id> \
  --owner-id <actual-child-id> \
  --invocation-log <actual-invocation.jsonl> \
  --review-parent-log <actual-review-parent.jsonl> \
  --child-log <actual-child.jsonl>
```

L2の専門担当には、`--support-log <id> <role> <path>` を追加します。
起動記録のID・担当と一致しないログは、証拠として受理しません。
外部launcherは、取得できた実IDから対象ログを限定して取り込みます。
見つからなければ、別セッションを探索して代用せず停止します。

## 失敗と復旧

```bash
python3 -B tools/implementation_review.py status --run-dir <run>
python3 -B tools/implementation_review.py halt \
  --run-dir <run> --reason BLOCKED --message '<observed reason>'
python3 -B tools/implementation_review.py archive --run-dir <run>
```

保存に失敗すると `pending-transition.json` が残ります。
この状態で、新しい担当を起動しません。
`archive` は会話記録を復旧します。モデルの再実行はしません。
利用制限、規約変更、対象変更も、勝手に解決済みにしません。

## 検証

```bash
python3 -B -m unittest discover -s tests -p 'test_implementation_review*.py' -v
```

確認するのは、担当先4通り、修正・差し戻し、原担当の解決確認です。
二重起動、対象不一致、未読規約、必須相談の欠落も確認します。
HTMLでは、非公開欄、認証情報、HTML注入、欠落、保存失敗を確認します。

この試行版の制限です。

- 実CLI・実アカウント・Desktopでの往復は未検証です。
- 未対応のログ形式では、推測せず `PARTIAL` で停止します。
- 跨層handoffは原文を保存して停止します。自動閉鎖しません。
- この制御は、モデルの意味判断が正しいことまでは証明しません。
- 別モデルのL2と、既存の人間による最終判断は残ります。
