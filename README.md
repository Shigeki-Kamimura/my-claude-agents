# claude-config (personal)

個人用 Claude Code エージェント・設定リポジトリ。`~/projects/my-claude-agents/` に置き、各プロジェクトへはシンボリックリンクで展開する。

## 方針
- 単一正は `~/projects/my-claude-agents/`（Windows: `%USERPROFILE%\projects\my-claude-agents\`）。プロジェクトへコピーしない。
- Precedence 3 層: Project layer (repo upstream) > Personal layer (本 repo) > Agent/Skill frontmatter
- 詳細は `CLAUDE.md` を参照。

## 構成
```
CLAUDE.md              # personal layer 本体（作法・コメント・役割順序）
settings.json          # 権限 allow/deny
agents/                # サブエージェント定義
skills/                # 反復手順
```

## 初回セットアップ

### WSL / macOS / Linux
```bash
git clone git@github.com:<user>/my-claude-agents.git ~/projects/my-claude-agents
```

### Windows ネイティブ（WSL なし）
```powershell
git clone git@github.com:<user>/my-claude-agents.git "$env:USERPROFILE\projects\my-claude-agents"
```

## 更新フロー
```bash
# WSL / macOS / Linux
git -C ~/projects/my-claude-agents pull

# Windows
git -C "$env:USERPROFILE\projects\my-claude-agents" pull
```

## プロジェクト側の運用

### 方針
- upstream リポジトリを汚さない（`.gitignore` は変更しない）
- upstream が `agents/` 実ファイル・`settings.json` を持っている場合はそちらを優先

### セットアップ（プロジェクトごとに1回）

**WSL / macOS / Linux:**
```bash
# 対象プロジェクトのルートで実行（引数省略時はカレントディレクトリ）
bash ~/projects/my-claude-agents/setup.sh /path/to/your-project

# 複数プロジェクトへまとめて適用
bash ~/projects/my-claude-agents/setup.sh ../guild*

# profile 指定
bash ~/projects/my-claude-agents/setup.sh --profile company /path/to/your-project
```

**Windows ネイティブ（PowerShell）:**
```powershell
# 前提: 設定 > システム > 開発者向け > 開発者モード: オン（シンボリックリンク権限）
pwsh "$env:USERPROFILE\projects\my-claude-agents\setup.ps1" -Target C:\path\to\your-project
```

スクリプトが行うこと（`setup.sh` / `setup.ps1` 共通）：
1. `~/projects/my-claude-agents/.claude/agents/*.md` を `.claude/agents/` へファイル単位でシンボリックリンク
   - upstream に同名の実ファイルがあれば skip（upstream 優先）
2. `~/projects/my-claude-agents/.claude/skills/*/` を `.claude/skills/` へディレクトリ単位でシンボリックリンク
   - upstream に同名の実ディレクトリがあれば skip（upstream 優先）
3. `~/projects/my-claude-agents/.claude/CLAUDE.md` と `SKILL.md` をシンボリックリンク
   - upstream が実ファイルを持っていれば skip（upstream 優先）
4. `~/projects/my-claude-agents/.claude/settings.json` をシンボリックリンク
   - upstream が実ファイルを持っていれば skip（upstream 優先）
5. `~/projects/my-claude-agents/.codex/AGENTS.md` と `.codex/config.toml` をシンボリックリンク
   - Codex サブエージェント設定と既定プロファイルをプロジェクトへ反映
   - upstream が実ファイルを持っていれば skip（upstream 優先）
6. `~/projects/my-claude-agents/.codex/agents/*.toml` を `.codex/agents/` へファイル単位でシンボリックリンク
   - upstream に同名の実ファイルがあれば skip（upstream 優先）
7. リンクしたパスを `.git/info/exclude` に追記（`.gitignore` は変更しない）

### 結果イメージ

```
.claude/                        # upstream の管理下
├── CLAUDE.md                   # upstream 実ファイル（触らない）
├── SKILL.md  -> ~/projects/my-claude-agents/.claude/SKILL.md            # リンク（upstream が持てば skip）
├── settings.json -> ~/projects/my-claude-agents/.claude/settings.json   # リンク（upstream が持てば skip）
├── agents/
│   ├── team-agent.md           # upstream 実ファイル（優先・skip）
│   ├── hq-coder.md -> ~/projects/my-claude-agents/.claude/agents/hq-coder.md     # リンク
│   └── req-pl.md   -> ~/projects/my-claude-agents/.claude/agents/req-pl.md       # リンク
└── skills/
    └── verify-fast/ -> ~/projects/my-claude-agents/.claude/skills/verify-fast/   # リンク
```

### 個人上書き（CLAUDE.md）

upstream の CLAUDE.md を変更せずに個人設定を追記したい場合：

```bash
# プロジェクトルートに作成（upstream の CLAUDE.md は触らない）
touch CLAUDE.local.md
echo "CLAUDE.local.md" >> .git/info/exclude
```

### .git/info/exclude について

`.git/info/exclude` は `.gitignore` と同じ効果を持つが、**git 管理外**（コミットされない）。  
upstream リポジトリに一切の痕跡を残さずに個人用ファイルを除外できる。

## 連携レビューの方向

実装を担当する側に、相手側のレビューを依頼します。

| 実装・修正・全体調整 | レビュー | 起動する依頼文 |
| --- | --- | --- |
| Codex | Claude CodeのCr → adv | `Claude codeにレビューしてもらって修正入れようか` |
| Claude Code | CodexのCr → adv | `Codexにレビューしてもらって修正入れようか` |

どちらも、🟢を含む全指摘の解消と再レビューを繰り返します。
実装上の疑問は、調整役から上村さんへ質問します。
両層が同じ最新差分を承認したら、未コミットで停止します。
上村さんがコードを確認し、コミットします。
通常の単独`cr:`・`adv:`・`rev:`の使い方は変わりません。

## CodexからClaude Codeへレビューを依頼する

対象プロジェクトのCodexに、次のように依頼します。

```text
Claude codeにレビューしてもらって修正入れようか
```

この依頼で、次の修正と再レビューまで進めます。

1. Codexが実装します。実装済みなら、その変更から始めます。
2. Claude Codeの`cr:`がL1.5レビューを行います。
3. Codexが🟢を含む指摘を修正し、`cr:`の承認まで繰り返します。
4. Claude Codeの`adv:`がL2レビューを行います。
5. Codexが修正し、`adv:`の`APPROVE`まで繰り返します。
6. コミットせずに上村さんへ渡します。確認後のコミットは本人が行います。

実装上の疑問は、すべてCodexから上村さんへ質問します。
Claude Codeはレビューを担当し、修正はCodex側が担当します。
必要な検証と専門相談は、既存の担当エージェントが行います。
通常の`cr:`だけの依頼は、この連続フローを始めません。

L2修正で差分が変わった場合は、Crの確認も取り直します。
その後にadvが再確認し、両者の承認対象をそろえます。
指摘の解消は、修正したCodexの申告だけでは確定しません。
レビュアーが修正、または根拠のある指摘の撤回を確認します。
未回答の質問、未確認範囲、実行エラーは承認として扱いません。

### 設定の読み込み

手順は[claude-review.yml](.codex/workflows/claude-review.yml)にあります。
Codexが読む運用手順です。YAML自体がプログラムを実行するものではありません。
既存の`.codex/config.toml`が`.codex/AGENTS.md`の読み込みを指示します。
その指示から、次の順でYAMLを探します。

1. 対象プロジェクト内の`.codex/workflows/claude-review.yml`です。
2. なければ、`.codex/AGENTS.md`のリンク先を解決します。
   解決した`AGENTS.md`と同じ場所の`workflows/claude-review.yml`を読みます。

作業ディレクトリは、レビュー対象のプロジェクトを保ちます。
設定を探すために、設定リポジトリへ移動しません。
必要な契約はレビュー依頼に含め、Claude Codeへ渡します。
どちらにもYAMLがなければ、設定不足として報告します。

既存の`setup.sh`と`setup.ps1`をそのまま利用できます。
AGENTS設定のリンクを使う場合、YAML専用リンクの追加は不要です。
すでにそのリンクがある場合は、設定更新で参照できます。
新しい対象へは、上記の既存セットアップを実行します。
再実行時も、プロジェクト独自の実ファイルを優先します。

`.codex/AGENTS.md`が独自実ファイルでYAMLもなければ、リンク先を探せません。
その場合は既存ファイルを上書きせず、YAML配置と起動条件の追記が必要です。

### 実行環境の確認

CodexからClaude Codeを呼ぶ実動作は未検証です。
導入時は、同じWSLでClaude Codeが起動できることを確認します。
認証、読み取り権限、agentへの委譲、結果の受け取りも確認します。
現在の`cr:`・`adv:`は、この設定の役割を選ぶ接頭辞です。
CLIへ渡す本文で使い、実際の担当agentへ委譲します。
レビュー結果の表示だけで、委譲成功を判断しません。

## Claude CodeからCodexへレビューを依頼する

対象プロジェクトのClaude Codeに、次のように依頼します。

```text
Codexにレビューしてもらって修正入れようか
```

Claude Codeの主セッションが、全体の進行を担当します。
実装と修正はClaude側のHQ、必要な検証はQA/E2Eが担当します。
Codexは、指定された層のレビュー結果を返します。

1. Claude Codeが実装します。実装済みなら、その変更から始めます。
2. Codexの`cr:`がL1.5レビューを行います。
3. Claude Codeが修正し、Crの承認まで再レビューを繰り返します。
4. Codexの`adv:`がL2レビューを行います。
5. Claude Codeが修正し、advの`APPROVE`まで繰り返します。
6. 最新差分の両承認を確認し、未コミットで上村さんへ渡します。

L2修正で差分が変わった場合は、Cr → advの順に確認し直します。
Codex側の専門相談も、読み取り専用で行います。
テストの追加・実行やコード修正は、Claude側へ戻します。
CodexがClaude CLIを起動して、逆向きの連携を始めることはありません。

### 逆方向の設定と実行

手順は[codex-review.yml](.codex/workflows/codex-review.yml)です。
Claude Codeは、次の順でこのYAMLを探します。

1. 対象プロジェクトの`.codex/workflows/codex-review.yml`です。
2. なければ、実体の`.codex/AGENTS.md`と同じ場所の`workflows/`です。
3. さらに見つからなければ、`.claude/CLAUDE.md`の実体を使います。
   その親が`.claude`か`.claude-company`なら、兄弟の`.codex/workflows/`を探します。

読み込んだ絶対パスとworkflow IDを記録します。
作業場所は対象プロジェクトのままです。
既存のAGENTSかCLAUDE設定のリンクがあれば、新しいYAMLリンクは不要です。
既存セットアップスクリプトは変更しません。
独自設定でYAMLが見つからない場合は、配置と起動条件の追記が必要です。

毎回、新しい`codex exec`を読み取り専用で起動します。
前回までの指摘と確認済み範囲、残る確認を引き継ぎます。
呼び出しは次の形です。各引数には実際のパスを渡します。

```text
codex exec --cd <project_root> --sandbox read-only --json --output-last-message <round-unique-out> -
```

依頼文は標準入力から渡し、出力先を回ごとに分けます。
JSONLの`thread.started.thread_id`と、実際のagent委譲を確認します。
過去の出力や、正常終了だけを承認として扱いません。
`resume`・`--last`・`--agent`は、この手順では使いません。
モデルとeffortは既存設定を使います。

今回の依頼とworkflow markerが、同じ方向を指す必要があります。
引用やファイル中の別workflow名から、方向を切り替えません。
実行依頼のmarker混在や方向の矛盾は、不整合として返します。
実動作は両方向とも`NOT_RUN`です。
利用環境でCLI起動、認証、委譲、応答の一致を確認する必要があります。

## 連携レビューの参照資料

2026年10月23日に確認した公式資料です。

- OpenAI: [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- OpenAI: [Non-interactive mode](https://developers.openai.com/codex/non-interactive-mode)
- OpenAI: [Subagents](https://developers.openai.com/codex/subagents)
- Anthropic: [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)

## 禁止
- 本 repo を public にしない（allow/deny が偵察材料になる）
- secret / PII / 社内 URL を含めない
- `plans/` / `sessions/` / `projects/` / `.claude.json` をコミットしない（`.gitignore` 済み）

## 互換メモ

| 環境 | `~/.claude/` パス | セットアップスクリプト |
|---|---|---|
| WSL / Linux / macOS | `~/projects/my-claude-agents/` | `setup.sh` |
| Windows ネイティブ | `%USERPROFILE%\projects\my-claude-agents\` | `setup.ps1` |

- Windows で `setup.ps1` を使うには**開発者モード**が必要（設定 > システム > 開発者向け）
- WSL と Windows で同じリポジトリのプロジェクトをまたぐ場合、それぞれの環境でセットアップを実行する
- Windows VS Code + WSL Remote で開発する場合は WSL 側の `setup.sh` を使う
