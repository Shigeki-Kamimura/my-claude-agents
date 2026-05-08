#!/usr/bin/env bash
# Why: upstream リポジトリを汚さずに個人用 agents/skills/settings を各プロジェクトへ展開するため。
# Scope: .claude と .codex と .copilot のシンボリックリンク作成と .git/info/exclude への登録のみ。upstream ファイルは変更しない。
# Usage: bash ~/.claude/setup.sh [--profile personal|company] [TARGET_PROJECT_DIR...]

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: setup.sh [--profile personal|company] [TARGET_PROJECT_DIR...]

Examples:
  setup.sh
  setup.sh ../guildboard-training-management
  setup.sh --profile company ../guild*
EOF
}

PROFILE="personal"
TARGETS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --profile には値が必要です" >&2
        usage >&2
        exit 1
      fi
      PROFILE="$2"
      shift 2
      ;;
    --profile=*)
      PROFILE="${1#--profile=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TARGETS+=("$1")
      shift
      ;;
  esac
done

if [ "$PROFILE" != "personal" ] && [ "$PROFILE" != "company" ]; then
  echo "ERROR: profile は personal または company を指定してください: $PROFILE" >&2
  usage >&2
  exit 1
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
  TARGETS=("$(pwd)")
fi

# --- パス解決 ---
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$PROFILE" = "company" ]; then
  SRC_CLAUDE_ROOT="$SELF_DIR/.claude-company"
else
  SRC_CLAUDE_ROOT="$SELF_DIR/.claude"
fi

SRC_AGENTS="$SRC_CLAUDE_ROOT/agents"
SRC_SKILLS="$SRC_CLAUDE_ROOT/skills"
SRC_SETTINGS="$SRC_CLAUDE_ROOT/settings.json"
SRC_CLAUDE_MD="$SRC_CLAUDE_ROOT/CLAUDE.md"
SRC_SKILL_MD="$SRC_CLAUDE_ROOT/SKILL.md"
SRC_CODEX_AGENTS="$SELF_DIR/.codex/agents"
SRC_CODEX_INSTRUCTIONS="$SELF_DIR/.codex/AGENTS.md"
SRC_CODEX_CONFIG="$SELF_DIR/.codex/config.toml"
SRC_COPILOT_INSTRUCTIONS="$SELF_DIR/.copilot/copilot-instructions.md"
SRC_COPILOT_AGENTS="$SELF_DIR/.copilot/agents"

setup_target() {
  local target_input="$1"
  local target
  target="$(cd "$target_input" && pwd)"
  local claude_dir="$target/.claude"
  local codex_dir="$target/.codex"
  local copilot_dir="$target/.copilot"
  local exclude_file="$target/.git/info/exclude"

  # gitリポジトリかチェック
  if [ ! -d "$target/.git" ]; then
    echo "ERROR: $target は git リポジトリではありません" >&2
    return 1
  fi

  # 自分自身への展開を防止（循環シンボリックリンクになるため）
  if [ "$SELF_DIR" = "$target" ]; then
    echo "ERROR: ソースリポジトリ自身には展開できません" >&2
    return 1
  fi

  echo "=== claude-config セットアップ: $target ==="

  # --- .git/info/exclude にエントリを追加（重複しない） ---
  add_exclude() {
    local pattern="$1"
    if ! grep -qxF "$pattern" "$exclude_file" 2>/dev/null; then
      echo "$pattern" >> "$exclude_file"
      echo "  [exclude] $pattern"
    fi
  }

  # --- agents: ファイル単位でリンク（upstream 実ファイルは skip） ---
  mkdir -p "$claude_dir/agents"
  add_exclude ".claude/agents"

  local linked_agents=0
  local skipped_agents=0
  local src
  local name
  local dest
  for src in "$SRC_AGENTS"/*.md; do
    [ -e "$src" ] || continue
    name="$(basename "$src")"
    dest="$claude_dir/agents/$name"

    if [ -f "$dest" ] && [ ! -L "$dest" ]; then
      echo "  [SKIP upstream] agents/$name"
      skipped_agents=$((skipped_agents + 1))
    else
      ln -sf "$src" "$dest"
      echo "  [LINK] agents/$name -> $src"
      linked_agents=$((linked_agents + 1))
    fi
  done

  # --- skills: ディレクトリ単位でリンク（upstream 実ディレクトリは skip） ---
  mkdir -p "$claude_dir/skills"
  add_exclude ".claude/skills"

  local linked_skills=0
  local skipped_skills=0
  if [ -d "$SRC_SKILLS" ]; then
    for src in "$SRC_SKILLS"/*/; do
      [ -d "$src" ] || continue
      name="$(basename "$src")"
      dest="$claude_dir/skills/$name"

      if [ -d "$dest" ] && [ ! -L "$dest" ]; then
        echo "  [SKIP upstream] skills/$name/"
        skipped_skills=$((skipped_skills + 1))
      else
        ln -sfn "$src" "$dest"
        echo "  [LINK] skills/$name/ -> $src"
        linked_skills=$((linked_skills + 1))
      fi
    done
  fi

  # --- CLAUDE.md: upstream が持っていれば触らない ---
  local claude_md_dest="$claude_dir/CLAUDE.md"
  if [ -f "$claude_md_dest" ] && [ ! -L "$claude_md_dest" ]; then
    echo "  [SKIP upstream] CLAUDE.md（upstream 優先）"
  else
    ln -sf "$SRC_CLAUDE_MD" "$claude_md_dest"
    add_exclude ".claude/CLAUDE.md"
    echo "  [LINK] CLAUDE.md -> $SRC_CLAUDE_MD"
  fi

  # --- SKILL.md: upstream が持っていれば触らない ---
  if [ -f "$SRC_SKILL_MD" ]; then
    local skill_md_dest="$claude_dir/SKILL.md"
    if [ -f "$skill_md_dest" ] && [ ! -L "$skill_md_dest" ]; then
      echo "  [SKIP upstream] SKILL.md（upstream 優先）"
    else
      ln -sf "$SRC_SKILL_MD" "$skill_md_dest"
      add_exclude ".claude/SKILL.md"
      echo "  [LINK] SKILL.md -> $SRC_SKILL_MD"
    fi
  fi

  # --- settings.json: upstream が持っていれば触らない ---
  local settings_dest="$claude_dir/settings.json"
  if [ -f "$settings_dest" ] && [ ! -L "$settings_dest" ]; then
    echo "  [SKIP upstream] settings.json（upstream 優先）"
  else
    ln -sf "$SRC_SETTINGS" "$settings_dest"
    add_exclude ".claude/settings.json"
    echo "  [LINK] settings.json -> $SRC_SETTINGS"
  fi

  # --- Codex: AGENTS.md ---
  mkdir -p "$codex_dir"
  add_exclude ".codex"

  local codex_instructions_dest="$codex_dir/AGENTS.md"
  if [ -f "$codex_instructions_dest" ] && [ ! -L "$codex_instructions_dest" ]; then
    echo "  [SKIP upstream] .codex/AGENTS.md（upstream 優先）"
  else
    ln -sf "$SRC_CODEX_INSTRUCTIONS" "$codex_instructions_dest"
    echo "  [LINK] .codex/AGENTS.md -> $SRC_CODEX_INSTRUCTIONS"
  fi

  # --- Codex: config.toml ---
  local codex_config_dest="$codex_dir/config.toml"
  if [ -f "$codex_config_dest" ] && [ ! -L "$codex_config_dest" ]; then
    echo "  [SKIP upstream] .codex/config.toml（upstream 優先）"
  else
    ln -sf "$SRC_CODEX_CONFIG" "$codex_config_dest"
    echo "  [LINK] .codex/config.toml -> $SRC_CODEX_CONFIG"
  fi

  # --- Codex agents: ファイル単位でリンク ---
  mkdir -p "$codex_dir/agents"

  local linked_codex_agents=0
  local skipped_codex_agents=0
  if [ -d "$SRC_CODEX_AGENTS" ]; then
    for src in "$SRC_CODEX_AGENTS"/*.toml; do
      [ -e "$src" ] || continue
      name="$(basename "$src")"
      dest="$codex_dir/agents/$name"

      if [ -f "$dest" ] && [ ! -L "$dest" ]; then
        echo "  [SKIP upstream] .codex/agents/$name"
        skipped_codex_agents=$((skipped_codex_agents + 1))
      else
        ln -sf "$src" "$dest"
        echo "  [LINK] .codex/agents/$name -> $src"
        linked_codex_agents=$((linked_codex_agents + 1))
      fi
    done
  fi

  # --- Copilot: copilot-instructions.md ---
  mkdir -p "$copilot_dir"
  add_exclude ".copilot"

  local copilot_instructions_dest="$copilot_dir/copilot-instructions.md"
  if [ -f "$copilot_instructions_dest" ] && [ ! -L "$copilot_instructions_dest" ]; then
    echo "  [SKIP upstream] .copilot/copilot-instructions.md（upstream 優先）"
  else
    ln -sf "$SRC_COPILOT_INSTRUCTIONS" "$copilot_instructions_dest"
    echo "  [LINK] .copilot/copilot-instructions.md -> $SRC_COPILOT_INSTRUCTIONS"
  fi

  # --- Copilot agents: ファイル単位でリンク ---
  mkdir -p "$copilot_dir/agents"

  local linked_copilot_agents=0
  local skipped_copilot_agents=0
  if [ -d "$SRC_COPILOT_AGENTS" ]; then
    for src in "$SRC_COPILOT_AGENTS"/*.md; do
      [ -e "$src" ] || continue
      name="$(basename "$src")"
      dest="$copilot_dir/agents/$name"

      if [ -f "$dest" ] && [ ! -L "$dest" ]; then
        echo "  [SKIP upstream] .copilot/agents/$name"
        skipped_copilot_agents=$((skipped_copilot_agents + 1))
      else
        ln -sf "$src" "$dest"
        echo "  [LINK] .copilot/agents/$name -> $src"
        linked_copilot_agents=$((linked_copilot_agents + 1))
      fi
    done
  fi

  echo ""
  echo "=== 完了 ==="
  echo "  claude agents : ${linked_agents} linked, ${skipped_agents} skipped (upstream)"
  echo "  claude skills : ${linked_skills} linked, ${skipped_skills} skipped (upstream)"
  echo "  codex agents  : ${linked_codex_agents} linked, ${skipped_codex_agents} skipped (upstream)"
  echo "  copilot agents: ${linked_copilot_agents} linked, ${skipped_copilot_agents} skipped (upstream)"
  echo ""
  echo "upstream を汚さないために .git/info/exclude を使用しています（.gitignore は変更していません）"
}

for target in "${TARGETS[@]}"; do
  setup_target "$target"
done
