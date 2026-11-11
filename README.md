# my-claude-agents

Claude Code、Codex、Copilotで使うエージェントと設定を管理します。

## エージェント一覧

依頼文の先頭に接頭辞を付けると、担当を指定できます。
たとえば `pl: 応募画面の要件を整理してください` と依頼します。

| エージェント | 接頭辞 | 担当すること |
| --- | --- | --- |
| [`req-pl`](.codex/agents/req-pl.toml) | `p:` / `pl:` | 実装前に目的、対象範囲、完了条件を整理します。 |
| [`hq-coder`](.codex/agents/hq-coder.toml) | `h:` / `hq:` | 設計と要件に沿って実装・修正し、変更を検証します。 |
| [`review-planner`](.codex/agents/review-planner.toml) | `rp:` / `plan:` | 差分とリスクを見て、最初に依頼するレビュー担当を決めます。 |
| [`code-quality-reviewer`](.codex/agents/code-quality-reviewer.toml) | `cr:` | 変更箇所の正しさ、開発ルール、保守しやすさを確認します。 |
| [`adviser`](.codex/agents/adviser.toml) | `a:` / `adv:` | 設計と責務の分担を確認し、変更が他の処理に及ぼす影響を調べます。 |
| [`reviewer`](.codex/agents/reviewer.toml) | `r:` / `rev:` | 以前の指摘が解消したか、修正による不具合がないかを確認します。 |
| [`test-qa`](.codex/agents/test-qa.toml) | `q:` / `qa:` | 単体テストなどの過不足を確認し、正常時と失敗時のテストを設計します。 |
| [`e2e-qa`](.codex/agents/e2e-qa.toml) | `e:` / `e2e:` | ブラウザーでの操作やAPIをまたぐテストを設計・検証します。 |
| [`ux-qa`](.codex/agents/ux-qa.toml) | `ux:` / `ux-qa:` | 起動済みの非本番アプリを操作し、結果をHTMLにまとめます。 |
| [`ci-reviewer`](.codex/agents/ci-reviewer.toml) | `ci:`（Codex） | GuildBoardのGitHub Actions実行前に、差分と検証結果を確認します。 |

Codexでは、通常の実装依頼を現在のチャットが `hq-coder` の役割で進めます。
Claude Codeでは `hq-coder` を子エージェントとして呼び出します。

専門分野の判断が必要なときは、次の担当に相談できます。

| エージェント | 担当すること |
| --- | --- |
| [`react-ui-flow`](.codex/agents/react-ui-flow.toml) | Reactの状態管理、フォーム、APIデータの表示を確認します。 |
| [`vue-frontend`](.codex/agents/vue-frontend.toml) | Vueの状態管理、コンポーネント間のやり取り、SSRを確認します。 |
| [`nestjs-backend`](.codex/agents/nestjs-backend.toml) | NestJSの責務分担、入力検証、認可、エラー応答を確認します。 |
| [`spring-boot`](.codex/agents/spring-boot.toml) | Spring Bootのサービス設計、トランザクション、認可を確認します。 |
| [`sec-arch`](.codex/agents/sec-arch.toml) | 認証・認可、権限の範囲、機密データの扱いを確認します。 |
| [`data-platform`](.codex/agents/data-platform.toml) | データ保存、再試行、二重実行、ロールバックのリスクを確認します。 |
| [`sol-escalation`](.codex/agents/sol-escalation.toml) | Lunaの専門担当が判断できなかった1件を引き継ぎます。Codexでの接頭辞は `sol:` です。 |
| [`opus-escalation`](.codex/agents/opus-escalation.toml) | Sonnetで判断が残った計画上の1件などを扱います。Claude Codeでの接頭辞は `o:` / `opus:` です。 |

Claude Codeの定義は [personal](.claude/agents) と [company](.claude-company/agents) にあります。

Copilotには、要件整理の `req-pl`、実装の `hq`、指摘を修正する `minimal-fix` があります。
レビューの `reviewer`、修正後の再確認を行う `convergence`、テスト不足を調べる `qa-audit` も使えます。 [Copilotの定義](.copilot/agents)

操作テストの依頼方法は [UX QAガイド](.claude/knowledge/ux-qa-guide.md) を参照してください。
CodexとClaude Codeを組み合わせる場合は、使う方向の手順を参照してください。 [Codex実装・Claudeレビュー](.codex/workflows/claude-review.yml) / [Claude実装・Codexレビュー](.codex/workflows/codex-review.yml)

## 対象リポジトリに反映する

この設定リポジトリを手元にクローンし、そのルートで実行します。
更新時は原本を更新してから、利用中のプロファイルでセットアップを再実行します。
`company` は会社用、`personal` は個人用のClaude Code設定です。

**WSL・Linux・macOS**

```bash
bash ./setup.sh --profile company /path/to/project
```

**Windowsネイティブ（PowerShell）**

```powershell
pwsh -File .\setup.ps1 -Profile company -Target C:\path\to\project
```

セットアップは、対象リポジトリに設定へのリンクを作ります。
Windowsでリンクを作れない場合は、開発者モードを確認してください。
既存の通常ファイルは `SKIP upstream` と表示され、そのファイルが残ります。

Codex Desktopで、リンクになっているエージェントが `agent type is currently not available` になる場合があります。
GuildBoardの `ux-qa` は、プロジェクト側のTOMLを同じ内容の通常ファイルに置き換えると起動しました。
通常ファイルに置き換えた定義は、原本を更新したときに個別に反映します。

## Codex Desktopアプリに反映する

Desktopが使う `CODEX_HOME` の `agents/` に、TOMLを通常ファイルとしてコピーします。
プロジェクトのセットアップとは別に、Python 3.11以上で同期スクリプトを使います。

設定リポジトリのルートで、まず差分を確認します。以下はWSLでの例です。
パスは、Desktopが実際に使う `CODEX_HOME` に置き換えてください。

```bash
desktop_codex_home='/mnt/c/Users/<Windowsユーザー名>/.codex'
python3 ./sync_codex_desktop.py --source "$PWD" --destination "$desktop_codex_home" --dry-run
```

差分を確認したら、同じシェルで `--apply` を実行します。

```bash
python3 ./sync_codex_desktop.py --source "$PWD" --destination "$desktop_codex_home" --apply
```

更新後は、Desktopの新しいチャットで対象エージェントの起動を確認します。
PowerShellからの実行方法と、バックアップからの復元手順も確認できます。 [Desktop同期の詳細](desktop-subagent-sync.md)
