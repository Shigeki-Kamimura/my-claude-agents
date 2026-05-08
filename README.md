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
