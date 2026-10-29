#!/usr/bin/env python3
"""Claude Code の親/子セッション JSONL から効率確認用HTMLを生成します。"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from html import escape
import json
from pathlib import Path
import re
import sys
import subprocess
import os
import tempfile

USAGE_KEYS = (
    "input_tokens", "output_tokens", "cache_read_input_tokens",
    "cache_creation_input_tokens",
)
RULES = {
    "engineering-governance.md": "engineering-governance.md",
    "human-review-patterns.md": "human-review-patterns.md",
    "claude-review.yml": "claude-review.yml",
    "coding-guidelines/README.md": "coding-guidelines/README.md",
}
READ_TOOLS = {"Read", "read_file", "read_text_file", "mcp__filesystem__read_file"}
SHELL_TOOLS = {"Bash", "bash", "execute", "functions.run"}
SHELL_READ_WORDS = re.compile(r"(?:^|[;|&\n]\s*|\b)(?:cat|sed|head|tail|awk)\s", re.I)
SHELL_SEARCH_WORDS = re.compile(r"\b(?:grep|rg|git\s+show|git\s+diff)\b", re.I)


def get_rule_label(value: str) -> str | None:
    candidate = value.replace("\\", "/").lower()
    for fragment, label in RULES.items():
        if fragment.lower() in candidate:
            return label
    return None


def read_jsonl(path: Path):
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                yield {"_unreadable_line": line_number}
                continue
            if isinstance(obj, dict):
                yield obj


def agent_label(path: Path, parent: Path) -> str:
    if path == parent:
        return "parent"
    try:
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        if isinstance(meta, dict) and isinstance(meta.get("agentType"), str):
            return f"{meta['agentType']} ({path.stem})"
    except (ValueError, OSError):
        pass
    return f"unknown ({path.stem})"


def scan_session(parent: Path) -> dict:
    if not parent.is_file() or parent.suffix != ".jsonl":
        raise ValueError(f"親JSONLがありません: {parent}")
    subdir = parent.with_suffix("") / "subagents"
    files = [parent, *(sorted(subdir.glob("agent-*.jsonl")) if subdir.is_dir() else [])]
    totals = Counter()
    access = Counter()
    agent_access = Counter()
    exact_read_access = Counter()
    repeated_slices = Counter()
    first_reads = Counter()
    search_access = Counter()
    roles = []
    tools_count = Counter()
    errors = 0
    unknown_messages = 0
    usage_by_agent = {}
    model_set = set()
    send_targets = set()
    sent_ids = {}
    send_results_ok = 0
    send_results_error = 0
    for path in files:
        label = agent_label(path, parent)
        roles.append(label)
        responses = {}
        seen_tool_use = set()
        observed_results = []
        for obj in read_jsonl(path):
            if "_unreadable_line" in obj:
                errors += 1
                continue
            if obj.get("type") != "assistant" and obj.get("type") != "user":
                continue
            msg = obj.get("message")
            if not isinstance(msg, dict):
                unknown_messages += 1
                continue
            if obj.get("type") == "assistant":
                msg_id = msg.get("id") or obj.get("uuid")
                if msg_id:
                    r = responses.setdefault(str(msg_id), {"usage": {}, "model": "unknown"})
                    r["model"] = msg.get("model") or r["model"]
                    usage = msg.get("usage")
                    if isinstance(usage, dict):
                        for key in USAGE_KEYS:
                            v = usage.get(key)
                            if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
                                r["usage"][key] = max(r["usage"].get(key, 0), v)
            blocks = msg.get("content", [])
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "tool_result":
                    observed_results.append((str(block.get("tool_use_id") or ""), block.get("is_error", False)))
                    continue
                if block_type != "tool_use" or obj.get("type") != "assistant":
                    continue
                tool_id = str(block.get("id") or "")
                if not tool_id or tool_id in seen_tool_use:
                    continue
                seen_tool_use.add(tool_id)
                tool = str(block.get("name") or "")
                args = block.get("input") or {}
                if not isinstance(args, dict):
                    args = {}
                tools_count[(label, tool)] += 1
                if tool == "SendMessage":
                    sent_ids[tool_id] = str(args.get("to") or "unknown")
                    send_targets.add(sent_ids[tool_id])
                # Readとシェルによる規則参照のみ計測。検索と再読は区別して扱う。
                if tool in READ_TOOLS:
                    value = str(args.get("file_path") or args.get("path") or "")
                    kind = "read"
                    # 同じ行範囲の再参照だけを重複候補とします。
                    slice_key = (args.get("offset"), args.get("limit"), args.get("start_line"), args.get("end_line"))
                elif tool in SHELL_TOOLS:
                    value = str(args.get("command") or "")
                    kind = "shell-read" if SHELL_READ_WORDS.search(value) else ("search" if SHELL_SEARCH_WORDS.search(value) else "other")
                    slice_key = value.strip()
                else:
                    value, kind, slice_key = "", "other", None
                rule = get_rule_label(value)
                if rule and kind in ("read", "shell-read"):
                    access[(label, rule, kind)] += 1
                    agent_access[(label, rule)] += 1
                    fingerprint = (label, rule, kind, str(slice_key))
                    exact_read_access[fingerprint] += 1
                    if exact_read_access[fingerprint] == 1:
                        first_reads[(label, rule)] += 1
                    else:
                        repeated_slices[(label, rule)] += 1
                elif rule and kind == "search":
                    search_access[(label, rule)] += 1
        for msg in responses.values():
            totals.update(msg["usage"])
            model_set.add(str(msg["model"]))
        usage_by_agent[label] = sum(v["usage"].get("input_tokens", 0) + v["usage"].get("output_tokens", 0) for v in responses.values())
        for tool_use_id, is_error in observed_results:
            if tool_use_id in sent_ids:
                if is_error:
                    send_results_error += 1
                else:
                    send_results_ok += 1
    rerereads = sum(repeated_slices.values())
    return {
        "session_id": parent.stem,
        "parent_file": parent.name,
        "children": len(files) - 1,
        "agents": roles,
        "usage": {key: totals[key] for key in USAGE_KEYS},
        "models": sorted(model_set),
        "new_agent_calls": sum(n for (actor, name), n in tools_count.items() if name == "Agent"),
        "send_calls": sum(n for (actor, name), n in tools_count.items() if name == "SendMessage"),
        "send_targets_count": len(send_targets),
        "send_result_ok": send_results_ok,
        "send_result_error": send_results_error,
        "access": access,
        "access_per_agent": agent_access,
        "read_fingerprint_count": first_reads,
        "exact_read_repeat_per_agent": repeated_slices,
        "search_per_agent": search_access,
        "same_agent_rule_repeat_accesses": rerereads,
        "errors": errors,
        "unknown_messages": unknown_messages,
        "usage_by_agent": usage_by_agent,
    }


def td(text: object) -> str:
    return f"<td>{escape(str(text))}</td>"


def html_report(results: list[dict]) -> str:
    css = """
    :root{color-scheme:light;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}
    body{margin:32px auto;padding:0 20px;max-width:1150px;color:#23313f;line-height:1.65;background:#fbfcff}
    h1{letter-spacing:-.03em} h2{margin-top:32px;border-bottom:1px solid #ccd6df;padding-bottom:6px}
    table{width:100%;border-collapse:collapse;font-size:.91rem} th,td{border-bottom:1px solid #dce3e9;text-align:left;padding:9px}
    th{background:#eef2f6} code{background:#e9eef3;padding:2px 4px;border-radius:4px}
    .meta{color:#536777}.notice{border-left:3px solid #8c98a8;padding:10px 14px;background:#f0f3f7}
    .ok{font-weight:600}.small{font-size:.86rem;color:#526273}
    """
    parts = [f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Claudeレビュー効率計測</title><style>{css}</style></head><body>',
        '<h1>Claudeレビュー効率計測</h1>',
        '<p class="notice">実際のローカルJSONLから数えた参考指標です。規則への再アクセスは必ずしも無駄ではありません。認証情報・本文・コードは出力していません。</p>',
        '<h2>セッション別集計</h2>',
        '<table><thead><tr><th>セッションID</th><th>子</th><th>Agent呼出</th><th>SendMessage</th><th>input</th><th>output</th><th>cache read</th><th>cache write</th><th>同一担当の規則再アクセス</th></tr></thead><tbody>']
    for s in results:
        cells = [s["session_id"], s["children"], s["new_agent_calls"], s["send_calls"], *(f'{s["usage"][k]:,}' for k in USAGE_KEYS),s["same_agent_rule_repeat_accesses"]]
        parts.append("<tr>" + "".join(td(c) for c in cells) + "</tr>")
    parts.append('</tbody></table><p class="small">各モデル応答はmessage.idで重複計上を避けています。モデル別の正確な集計には設定リポジトリ内のsummarize_claude_session.pyを使用してください。</p>')
    for s in results:
        parts.append(f'<h2>{escape(s["session_id"])} の詳細</h2>')
        parts.append(f'<p>担当: {escape(", ".join(s["agents"]))}</p>')
        parts.append(f'<p>モデル: {escape(", ".join(s["models"]))} ／ SendMessage結果のうちエラーなし: {s["send_result_ok"]}件、エラー: {s["send_result_error"]}件（成功判定には元ログの確認が必要です）</p>')
        parts.append('<table><thead><tr><th>担当</th><th>規則ファイル</th><th>本文参照</th><th>別の読み取り範囲</th><th>同じ読み取り範囲の再アクセス候補</th><th>検索</th></tr></thead><tbody>')
        for (agent, rule), count in sorted(s["access_per_agent"].items()):
            parts.append('<tr>' + ''.join(td(c) for c in (agent, rule, count,
                s["read_fingerprint_count"][(agent, rule)], s["exact_read_repeat_per_agent"][(agent, rule)],
                s["search_per_agent"][(agent, rule)])) + '</tr>')
        parts.append('</tbody></table>')
        parts.append(f'<p class="small">読み取れないJSONL行: {s["errors"]}件。形式不一致のメッセージ: {s["unknown_messages"]}件。Readと一部のBash参照のみ対象です。本文の変更、キャッシュ効果、再参照の必要性は判定できません。</p>')
    parts.append('<h2>判定方法</h2><p>担当ごとに独立して数え、別担当の初回読み込みは再読込みに含めません。さらに同じ担当でも異なる行範囲の読込みは重複と判定しません。検索は本文の読込みと分けます。ただし同じ範囲の再読込みでも規則変更・履歴欠落など正当な理由があり得るため、候補として目視確認します。SendMessageの成功や指摘の品質は元ログと変更したコードで判断します。</p>')
    parts.append('<p class="meta">このHTMLには生ログを含みません。生ログの全会話記録は設定リポジトリの <code>tools/render_review_record.py</code> で別途作成してください。</p>')
    parts.append('</body></html>')
    return '\n'.join(parts)


def safe_output(path: Path) -> None:
    """未除外のGit作業ツリー内へのHTML保存を禁止します。"""
    parent = path.resolve().parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    probe = subprocess.run(["git", "-C", str(parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
    if probe.returncode != 0:
        return
    root = Path(probe.stdout.strip()).resolve()
    try:
        rel = str(path.resolve().relative_to(root))
    except ValueError:
        return
    # .gitignoreには頼りません。setup.sh が設定した .git/info/exclude だけを確認します。
    info = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"], capture_output=True, text=True, check=False)
    if info.returncode != 0:
        raise ValueError("Gitの除外設定を確認できません")
    exclude = Path(info.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    try:
        entries = {line.strip().rstrip("/") for line in exclude.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.lstrip().startswith("#")}
    except OSError:
        entries = set()
    allowed = rel.startswith(".codex/review-records/") and bool({".codex", ".codex/review-records"} & entries)
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", rel], capture_output=True, check=False)
    if tracked.returncode == 0 or not allowed:
        raise ValueError("Git内へのHTML保存は、.git/info/excludeで除外済みの .codex/review-records/ のみ許可します。その他はリポジトリ外へ保存してください")


def private_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(value)
        os.replace(temp_path, path)
        path.chmod(0o600)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sessions", nargs="+", type=Path, help="Claude親セッションJSONL（複数指定可）")
    ap.add_argument("--out", required=True, type=Path, help="出力先HTML")
    args = ap.parse_args()
    try:
        results = [scan_session(p) for p in args.sessions]
        safe_output(args.out)
        private_write(args.out, html_report(results))
    except (OSError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 2
    print(f"完了: {args.out} ({len(results)} セッション)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())