#!/usr/bin/env bash
# Why: upstream リポジトリを汚さずに個人用 agents/skills/settings を各プロジェクトへ展開するため。
# Scope: シンボリックリンク作成と .git/info/exclude への登録のみ。CLAUDE.md / upstream ファイルは変更しない。
# Usage: bash ~/.claude/setup.sh [TARGET_PROJECT_DIR]

set -euo pipefail

# --- パス解決 ---
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_AGENTS="$SELF_DIR/.claude/agents"
SRC_SKILLS="$SELF_DIR/.claude/skills"
SRC_SETTINGS="$SELF_DIR/.claude/settings.json"

TARGET="${1:-$(pwd)}"
TARGET="$(cd "$TARGET" && pwd)"
CLAUDE_DIR="$TARGET/.claude"
EXCLUDE_FILE="$TARGET/.git/info/exclude"

# gitリポジトリかチェック
if [ ! -d "$TARGET/.git" ]; then
  echo "ERROR: $TARGET は git リポジトリではありません" >&2
  exit 1
fi

# 自分自身への展開を防止（循環シンボリックリンクになるため）
if [ "$SELF_DIR" = "$TARGET" ]; then
  echo "ERROR: ソースリポジトリ自身には展開できません" >&2
  exit 1
fi

echo "=== claude-config セットアップ: $TARGET ==="

# --- .git/info/exclude にエントリを追加（重複しない） ---
add_exclude() {
  local pattern="$1"
  if ! grep -qxF "$pattern" "$EXCLUDE_FILE" 2>/dev/null; then
    echo "$pattern" >> "$EXCLUDE_FILE"
    echo "  [exclude] $pattern"
  fi
}

# --- agents: ファイル単位でリンク（upstream 実ファイルは skip） ---
mkdir -p "$CLAUDE_DIR/agents"
add_exclude ".claude/agents"

linked_agents=0
skipped_agents=0
for src in "$SRC_AGENTS"/*.md; do
  [ -e "$src" ] || continue
  name="$(basename "$src")"
  dest="$CLAUDE_DIR/agents/$name"

  if [ -f "$dest" ] && [ ! -L "$dest" ]; then
    # upstream に実ファイルが存在 → 上書き禁止
    echo "  [SKIP upstream] agents/$name"
    skipped_agents=$((skipped_agents + 1))
  else
    ln -sf "$src" "$dest"
    echo "  [LINK] agents/$name -> $src"
    linked_agents=$((linked_agents + 1))
  fi
done

# --- skills: ディレクトリ単位でリンク（upstream 実ディレクトリは skip） ---
mkdir -p "$CLAUDE_DIR/skills"
add_exclude ".claude/skills"

linked_skills=0
skipped_skills=0
if [ -d "$SRC_SKILLS" ]; then
  for src in "$SRC_SKILLS"/*/; do
    [ -d "$src" ] || continue
    name="$(basename "$src")"
    dest="$CLAUDE_DIR/skills/$name"

    if [ -d "$dest" ] && [ ! -L "$dest" ]; then
      echo "  [SKIP upstream] skills/$name/"
      skipped_skills=$((skipped_skills + 1))
    else
      ln -sf "$src" "$dest"
      echo "  [LINK] skills/$name/ -> $src"
      linked_skills=$((linked_skills + 1))
    fi
  done
fi

# --- settings.json: upstream が持っていれば触らない ---
SETTINGS_DEST="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS_DEST" ] && [ ! -L "$SETTINGS_DEST" ]; then
  echo "  [SKIP upstream] settings.json（upstream 優先）"
else
  ln -sf "$SRC_SETTINGS" "$SETTINGS_DEST"
  add_exclude ".claude/settings.json"
  echo "  [LINK] settings.json -> $SRC_SETTINGS"
fi

# --- サマリ ---
echo ""
echo "=== 完了 ==="
echo "  agents : ${linked_agents} linked, ${skipped_agents} skipped (upstream)"
echo "  skills : ${linked_skills} linked, ${skipped_skills} skipped (upstream)"
echo ""
echo "upstream を汚さないために .git/info/exclude を使用しています（.gitignore は変更していません）"
