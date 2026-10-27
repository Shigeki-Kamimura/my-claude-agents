#!/usr/bin/env bash
# Why: upstream リポジトリを汚さずに個人用 agents/skills/settings を各プロジェクトへ展開するため。
# Scope: Claude/Copilot のリンクと Codex TOML の安全な実ファイル同期。.git/info だけで管理し upstream は変更しない。
# Usage: bash ~/.claude/setup.sh [-p|-profile personal|company] [TARGET_PROJECT_DIR...]

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: setup.sh [-p personal|company] [TARGET_PROJECT_DIR...]

Examples:
  setup.sh
  setup.sh ../guildboard-training-management
  setup.sh -p personal ../guild*
EOF
}

PROFILE="company"
TARGETS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    -p|--profile)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: -p には値が必要です" >&2
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
  echo "ERROR: -p には personal または company を指定してください: $PROFILE" >&2
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
SRC_KNOWLEDGE="$SRC_CLAUDE_ROOT/knowledge"
SRC_SETTINGS="$SRC_CLAUDE_ROOT/settings.json"
SRC_CLAUDE_MD="$SRC_CLAUDE_ROOT/CLAUDE.md"
SRC_SKILL_MD="$SRC_CLAUDE_ROOT/SKILL.md"
SRC_CODEX_AGENTS="$SELF_DIR/.codex/agents"
SRC_CODEX_INSTRUCTIONS="$SELF_DIR/.codex/AGENTS.md"
SRC_CODEX_CONFIG="$SELF_DIR/.codex/config.toml"
SRC_COPILOT_INSTRUCTIONS="$SELF_DIR/.copilot/copilot-instructions.md"
SRC_COPILOT_AGENTS="$SELF_DIR/.copilot/agents"

# 末尾のファイルが消えたリンクも、親ディレクトリとファイル名で照合します。
is_managed_codex_link() {
  local dest="$1"
  local expected="$2"
  local link_target link_parent expected_parent
  [ -L "$dest" ] || return 1
  link_target="$(readlink "$dest")" || return 1
  case "$link_target" in
    /*) ;;
    *) link_target="$(dirname "$dest")/$link_target" ;;
  esac
  [ "$(basename "$link_target")" = "$(basename "$expected")" ] || return 1
  link_parent="$(cd -P "$(dirname "$link_target")" 2>/dev/null && pwd -P)" || return 1
  expected_parent="$(cd -P "$(dirname "$expected")" 2>/dev/null && pwd -P)" || return 1
  [ "$link_parent" = "$expected_parent" ]
}

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
      echo "  [SKIP upstream] .claude/agents/$name"
      skipped_agents=$((skipped_agents + 1))
    else
      ln -sf "$src" "$dest"
      echo "  [LINK] .claude/agents/$name -> $src"
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
        echo "  [SKIP upstream] .claude/skills/$name/"
        skipped_skills=$((skipped_skills + 1))
      else
        ln -sfn "$src" "$dest"
        echo "  [LINK] .claude/skills/$name/ -> $src"
        linked_skills=$((linked_skills + 1))
      fi
    done
  fi

  # --- knowledge: ファイル単位でリンク（upstream 実ファイルは skip） ---
  mkdir -p "$claude_dir/knowledge"
  add_exclude ".claude/knowledge"

  local linked_knowledge=0
  local skipped_knowledge=0
  if [ -d "$SRC_KNOWLEDGE" ]; then
    for src in "$SRC_KNOWLEDGE"/*.md; do
      [ -e "$src" ] || continue
      name="$(basename "$src")"
      dest="$claude_dir/knowledge/$name"

      if [ -f "$dest" ] && [ ! -L "$dest" ]; then
        echo "  [SKIP upstream] .claude/knowledge/$name"
        skipped_knowledge=$((skipped_knowledge + 1))
      else
        ln -sf "$src" "$dest"
        echo "  [LINK] .claude/knowledge/$name -> $src"
        linked_knowledge=$((linked_knowledge + 1))
      fi
    done
  fi

  # --- CLAUDE.md: upstream が持っていれば触らない ---
  local claude_md_dest="$claude_dir/CLAUDE.md"
  if [ -f "$claude_md_dest" ] && [ ! -L "$claude_md_dest" ]; then
    echo "  [SKIP upstream] .claude/CLAUDE.md（upstream 優先）"
  else
    ln -sf "$SRC_CLAUDE_MD" "$claude_md_dest"
    add_exclude ".claude/CLAUDE.md"
    echo "  [LINK] .claude/CLAUDE.md -> $SRC_CLAUDE_MD"
  fi

  # --- SKILL.md: upstream が持っていれば触らない ---
  if [ -f "$SRC_SKILL_MD" ]; then
    local skill_md_dest="$claude_dir/SKILL.md"
    if [ -f "$skill_md_dest" ] && [ ! -L "$skill_md_dest" ]; then
      echo "  [SKIP upstream] .claude/SKILL.md（upstream 優先）"
    else
      ln -sf "$SRC_SKILL_MD" "$skill_md_dest"
      add_exclude ".claude/SKILL.md"
      echo "  [LINK] .claude/SKILL.md -> $SRC_SKILL_MD"
    fi
  fi

  # --- settings.json: upstream が持っていれば触らない ---
  local settings_dest="$claude_dir/settings.json"
  if [ -f "$settings_dest" ] && [ ! -L "$settings_dest" ]; then
    echo "  [SKIP upstream] .claude/settings.json（upstream 優先）"
  else
    ln -sf "$SRC_SETTINGS" "$settings_dest"
    add_exclude ".claude/settings.json"
    echo "  [LINK] .claude/settings.json -> $SRC_SETTINGS"
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

  # --- Codex TOML: 自分が管理するものだけ実ファイルとして同期 ---
# Codex の子エージェント定義は symlink 経由では起動時に拒否される場合があります。
# 管理履歴は git 管理外の .git/info に置き、既存の upstream ファイルは守ります。
mkdir -p "$codex_dir/agents"
local codex_state_file="$target/.git/info/codex-setup-managed.tsv"
local codex_copied=0 codex_current=0 codex_skipped=0 codex_conflicts=0

codex_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

codex_known_checksum() {
  local relative="$1"
  if [ -f "$codex_state_file" ]; then
    awk -F '\t' -v name="$relative" '$1 == name {print $2; exit}' "$codex_state_file"
  fi
}

codex_save_checksum() {
  local relative="$1" checksum="$2" old temp
  old="$(codex_known_checksum "$relative")"
  [ "$old" = "$checksum" ] && return 0
  temp="$(mktemp "$codex_state_file.tmp.XXXXXXXX")" || return 1
  if [ -f "$codex_state_file" ]; then
    awk -F '\t' -v name="$relative" '$1 != name {print}' "$codex_state_file" > "$temp"
  fi
  printf '%s\t%s\n' "$relative" "$checksum" >> "$temp"
  mv -f "$temp" "$codex_state_file"
}

sync_codex_toml() {
  local source="$1" relative="$2"
  local destination="$codex_dir/$relative"
  local previous current staged

  # git の追跡対象は、リンクであっても絶対に書き換えません。
  if git -C "$target" ls-files --error-unmatch -- ".codex/$relative" >/dev/null 2>&1; then
    echo "  [SKIP tracked] .codex/$relative"
    codex_skipped=$((codex_skipped + 1))
    return 0
  fi

  if [ -L "$destination" ]; then
    if ! is_managed_codex_link "$destination" "$source"; then
      echo "  [CONFLICT preserved] .codex/$relative（外部リンク）" >&2
      codex_conflicts=$((codex_conflicts + 1))
      return 0
    fi
  elif [ -e "$destination" ]; then
    if [ ! -f "$destination" ]; then
      echo "  [CONFLICT preserved] .codex/$relative（ファイルではありません）" >&2
      codex_conflicts=$((codex_conflicts + 1))
      return 0
    fi
    previous="$(codex_known_checksum "$relative")"
    current="$(codex_sha256 "$destination")"
    if [ -z "$previous" ] && ! cmp -s "$source" "$destination"; then
      echo "  [SKIP upstream] .codex/$relative（管理外の実ファイル）"
      codex_skipped=$((codex_skipped + 1))
      return 0
    fi
    if [ -n "$previous" ] && [ "$current" != "$previous" ] && ! cmp -s "$source" "$destination"; then
      echo "  [CONFLICT preserved] .codex/$relative（同期後に編集されています）" >&2
      codex_conflicts=$((codex_conflicts + 1))
      return 0
    fi
  fi

  # 手動で実ファイル化済みでも原本と一致すれば管理下へ引き継ぎます。
  if [ -f "$destination" ] && [ ! -L "$destination" ] && cmp -s "$source" "$destination"; then
    codex_save_checksum "$relative" "$(codex_sha256 "$destination")"
    echo "  [CURRENT] .codex/$relative"
    codex_current=$((codex_current + 1))
    return 0
  fi

  # コピー完了後に置き換えます。リンク先の原本へは書き込みません。
  staged="$(mktemp "$destination.tmp.XXXXXXXX")" || return 1
  if ! cp "$source" "$staged"; then
    rm -f "$staged"
    return 1
  fi
  if ! mv -f "$staged" "$destination"; then
    rm -f "$staged"
    return 1
  fi
  codex_save_checksum "$relative" "$(codex_sha256 "$destination")"
  echo "  [COPY] .codex/$relative"
  codex_copied=$((codex_copied + 1))
}

if [ ! -f "$SRC_CODEX_CONFIG" ]; then
  echo "ERROR: Codex の原本 config.toml が見つかりません: $SRC_CODEX_CONFIG" >&2
  return 1
fi
sync_codex_toml "$SRC_CODEX_CONFIG" "config.toml"

# 旧名は入力エイリアスだけに残し、旧TOMLの管理リンクは撤去します。
local retired_name
for retired_name in hq.toml pl.toml qa.toml; do
  dest="$codex_dir/agents/$retired_name"
  if git -C "$target" ls-files --error-unmatch -- ".codex/agents/$retired_name" >/dev/null 2>&1; then
    echo "  [CONFLICT preserved] .codex/agents/$retired_name（git追跡対象）" >&2
    codex_conflicts=$((codex_conflicts + 1))
  elif is_managed_codex_link "$dest" "$SRC_CODEX_AGENTS/$retired_name"; then
    rm "$dest"
    echo "  [REMOVE retired] .codex/agents/$retired_name"
  elif [ -e "$dest" ] || [ -L "$dest" ]; then
    echo "  [CONFLICT preserved] .codex/agents/$retired_name（独自ファイル・リンク）" >&2
    codex_conflicts=$((codex_conflicts + 1))
  fi
done

# 新しい *.toml が原本に増えれば、次の setup 実行で自動追加します。
if [ -d "$SRC_CODEX_AGENTS" ]; then
  for src in "$SRC_CODEX_AGENTS"/*.toml; do
    [ -f "$src" ] || continue
    name="$(basename "$src")"
    case "$name" in hq.toml|pl.toml|qa.toml) continue ;; esac
    sync_codex_toml "$src" "agents/$name"
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
  echo "  claude agents   : ${linked_agents} linked, ${skipped_agents} skipped (upstream)"
  echo "  claude skills   : ${linked_skills} linked, ${skipped_skills} skipped (upstream)"
  echo "  claude knowledge: ${linked_knowledge} linked, ${skipped_knowledge} skipped (upstream)"
  echo "  codex TOML      : $codex_copied copied/updated, $codex_current current, $codex_skipped skipped"
  echo "  copilot agents  : ${linked_copilot_agents} linked, ${skipped_copilot_agents} skipped (upstream)"
  if [ "$codex_conflicts" -gt 0 ]; then
    echo "  Codex同期: $codex_conflicts 件の競合が残っています。統合完了ではありません。" >&2
  fi
  echo ""
  echo "upstream を汚さないために .git/info/exclude を使用しています（.gitignore は変更していません）"
}

for target in "${TARGETS[@]}"; do
  setup_target "$target"
done
