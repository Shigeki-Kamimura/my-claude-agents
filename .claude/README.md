# claude-config (personal)

個人用 Claude Code 設定リポジトリ。WSL 上の `~/.claude/` として運用する。

## 方針
- 単一正は WSL 側 `~/.claude/`。プロジェクトへコピーしない。
- Precedence 3 層: Project layer (repo upstream) > Personal layer (本 repo) > Agent/Skill frontmatter
- 詳細は `CLAUDE.md` を参照。

## 構成
```
CLAUDE.md              # personal layer 本体（作法・コメント・役割順序）
settings.json          # 権限 allow/deny
agents/                # サブエージェント定義
skills/                # 反復手順
```

## 初回セットアップ（会社 PC / WSL）
```bash
# 既存 ~/.claude があれば退避
[ -d ~/.claude ] && mv ~/.claude ~/.claude.bak.$(date +%Y%m%d)

git clone git@github.com:<user>/claude-config.git ~/.claude
```

## 更新フロー
```bash
# 個人 repo 側で編集 → commit → push
git -C ~/.claude pull
```

## プロジェクト側の運用
- upstream 共有ルール: repo 直下 `CLAUDE.md` と `.claude/`（チーム合意分のみ）
- 個人上書き: repo 直下 `CLAUDE.local.md`（`.gitignore` 登録）
- 個人 agents/skills/settings は本 repo (`~/.claude/`) 側に置く。プロジェクトにはコピーしない。

プロジェクトの `.gitignore` に追加:
```
CLAUDE.local.md
.claude/settings.local.json
.claude/plans/
```

## 禁止
- 本 repo を public にしない（allow/deny が偵察材料になる）
- secret / PII / 社内 URL を含めない
- `plans/` / `sessions/` / `projects/` / `.claude.json` をコミットしない（`.gitignore` 済み）

## 互換メモ
- 対象環境: WSL (Linux filesystem)。Windows 側 `C:\Users\...\.claude\` は作らない。
- Windows VS Code を使う場合は WSL Remote 経由で開く。
