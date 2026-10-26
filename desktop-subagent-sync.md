# Desktop サブエージェントの更新

`sync_codex_desktop.py` は、設定リポジトリの `.codex/agents/*.toml` を、指定した Desktop の `CODEX_HOME/agents/` へコピーします。Python 3.11 以降の標準ライブラリだけで動きます。`setup.sh` / `setup.ps1` のプロジェクト単位リンク導入とは別の手順です。

## WSL で実行する

まず、使いたい更新が現在の原本にあることを確認します。スクリプトはブランチを切り替えず、`pull` もしません。未コミット変更も現在の原本として読み、状態とコミット番号を記録します。変更した定義と指示は必ず差分で確認してください。

PowerShell から、今回の環境で差分だけを見るコマンドです。`--destination` は `agents` ではなく、実際に Desktop が使う **Codex home** を指定します。

```powershell
wsl.exe -d Ubuntu-Preview -- python3 /home/shigeki/projects/my-claude-agents/sync_codex_desktop.py --source /home/shigeki/projects/my-claude-agents --destination /mnt/c/Users/ShigekiKamimura/.codex
```

初期動作は dry-run です。`--dry-run` を明示しても同じです。ロック、バックアップ、設定ファイルを作りません。出力する `Source`、`Destination`、`KEEP` と内容の差分を確認します。

確認後に、同じコマンドへ `--apply` を付けます。

```powershell
wsl.exe -d Ubuntu-Preview -- python3 /home/shigeki/projects/my-claude-agents/sync_codex_desktop.py --source /home/shigeki/projects/my-claude-agents --destination /mnt/c/Users/ShigekiKamimura/.codex --apply
```

ほかの環境では `--source` と `--destination` をその環境のパスへ置き換えます。スクリプトは Windows と WSL の両方へ自動展開しません。今回の環境では実行中の WSL app-server の `CODEX_HOME` が `/mnt/c/Users/ShigekiKamimura/.codex` であることを確認済みです。起動設定が変わった場合は読み込み先を確認し直します。

## 更新するもの・保持するもの

- 原本にある canonical 定義を対象にし、`name` とファイル名の一致、重複、TOML、必要な共有参照を検査します。`hq` / `pl` / `qa` などの入力エイリアスはルーティング指示で正規化します。別 TOML を作りません。重複や別名の衝突は、削除せず停止します。
- 原本にない独自定義（例：`reviewer-md-only.toml`）と、無関係なファイルは残します。廃止された原本の定義も自動削除しません。必要なら個別に整理します。
- 既存の `model` / effort 等の指定は保持します。原本と違う場合は `KEEP` を表示します。新しいモデルを採用したい場合は、更新とは分けて設定を確認します。
- 既存の sandbox 等の設定は、原本で省略されても保持します。原本と競合する権限・実行設定は停止します。新規ロールの `read-only` と機能無効化以外の実行設定も別途確認が必要です。`req-pl=read-only`、`test-qa=workspace-write` は現状どおり残ります。子定義の値が親設定を上書きできることを保証するものではありません。
- `CODEX_HOME/config.toml`、承認・信頼・認証・MCP 設定には書き込みません。明示的な `[agents.<role>]` 登録が元または先にある場合は、フォルダー探索との対応が曖昧なため停止します。
- 既知の `.Codex/knowledge/human-review-patterns.md` 参照は、実在する原本の `.claude/knowledge/human-review-patterns.md` の絶対パスへ、導入先だけで補正します。原本の定義や西口さんの指針を書き換えません。

## 共有ルールへの参照

導入する定義の指示と Desktop の `AGENTS.md` に、次の所有マーカーで囲んだ参照ブロックを管理します。

```text
<!-- codex-desktop-sync:begin -->
...
<!-- codex-desktop-sync:end -->
```

プロジェクトの規則・profile・設定済み参照を優先します。必要な共有リンクがない場合に、原本の `.codex/AGENTS.md`、`workflows/*.yml`、`.claude/knowledge/*.md` を読む補助参照です。実際のユーザー依頼なしにレビューやテストは開始しません。原本の指示本文を複製したり、レビュー方針を作り直したりしません。

共有の Markdown/YAML は原本を直接参照するため、原本更新後の内容を読みます。TOML 定義はコピーした時点の内容なので、再同期が必要です。

既存 `AGENTS.md` のマーカー外は保持します。以前の一回限りの導入で追記した `## Desktop independent QA and E2E review references` は、同梱の `desktop_sync_legacy.txt` と完全一致する末尾ブロックだけをマーカーへ移行します。編集済み・曖昧な旧ブロックは上書きせず停止します。利用者の文をマーカー内へ混ぜないでください。

定義の内容は TOML の意味を保って出力します。ファイルの書式は変わることがあります。表示する指示の差分は、長い一行ではなく内容を行単位で比較します。

## バックアップと復旧

変更がある apply では、次の場所へ変更前のファイルと検証用 `manifest.json` を保存します。

```text
<CODEX_HOME>/backups/desktop-agent-sync/<UTC日時>/
```

バックアップの内容を照合した後で、一時ファイルからファイル単位で置き換えます。複数ファイル全体を OS が同時に切り替えるわけではありません。apply の間は別の更新や対象ファイルの編集を避けてください。通常の書き込み失敗は、既に置き換えたファイルを元へ戻します。復旧も失敗した場合、またはプロセスが中断した場合はバックアップの状態を残します。後続更新は未完了の記録を検知して停止します。

復元もまず dry-run で確認します。`<UTC日時>` は実際に表示されたバックアップ名に置き換えます。

```powershell
wsl.exe -d Ubuntu-Preview -- python3 /home/shigeki/projects/my-claude-agents/sync_codex_desktop.py --destination /mnt/c/Users/ShigekiKamimura/.codex --restore /mnt/c/Users/ShigekiKamimura/.codex/backups/desktop-agent-sync/<UTC日時>
```

確認後に `--apply` を付けると復元します。現在の内容が記録済みの適用前／適用後ハッシュと違う場合、後からの編集を上書きせず停止します。バックアップ改変や管理外のパスも拒否します。途中で新規作成したファイルは、ハッシュが一致する場合だけ復元時に取り除きます。

ロックファイルが残った場合は、別の updater が動いていないことを確認してから扱ってください。未完了のバックアップがあれば先に復元します。ロックや記録を無条件に消して再実行しないでください。

## 検証と実行中セッション

```bash
cd /home/shigeki/projects/my-claude-agents
python3 -B -m unittest discover -s tests -p 'test_sync_codex_desktop.py' -v
```

テストは一時フォルダーだけを使います。独自定義保持、繰り返し時 no-op、権限差分、重複名、壊れた TOML・参照、リンク逸脱、同時変更、バックアップ、失敗時の復元を確認します。

スクリプトは Codex や WSL を再起動せず、テスト・レビュー・モデル呼び出しも実行しません。ファイルの導入成功は、既存セッションの再読込成功とは別です。更新後は新しいタスクで使用状況を確認してください。アプリの版ごとの reload 動作や再起動の要否は、このツールでは保証しません。
