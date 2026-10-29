#!/usr/bin/env python3
"""Claude Code親セッションと子agentのJSONLを集計します。"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# 子の記録(agent-*.meta.json)のagentTypeを、レビュー層の短い名前に対応づけます。
# 表にないagentTypeはそのままの名前で分け、メタ情報がないものは「不明」とします。推測で層を割り当てません。
LAYER_BY_AGENT_TYPE = {
    "code-quality-reviewer": "cr",
    "test-qa": "qa",
    "e2e-qa": "e2e",
    "adviser": "adv",
    "reviewer": "rev",
}
UNKNOWN_LAYER = "不明"

USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)


def read_records(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONLの解析に失敗: {path}:{line_no}") from exc


def layer_of(path: Path, session_path: Path) -> str:
    """トランスクリプトの層名を返します。親は「parent」です。"""
    if path == session_path:
        return "parent"
    meta_path = path.with_suffix(".meta.json")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return UNKNOWN_LAYER
    agent_type = meta.get("agentType") if isinstance(meta, dict) else None
    if not isinstance(agent_type, str) or not agent_type:
        return UNKNOWN_LAYER
    return LAYER_BY_AGENT_TYPE.get(agent_type, agent_type)


def summarize(session_path: Path) -> dict:
    if not session_path.is_file() or session_path.suffix != ".jsonl":
        raise ValueError("親セッションの.jsonlを指定してください")
    child_dir = session_path.with_suffix("") / "subagents"
    children = sorted(child_dir.glob("agent-*.jsonl")) if child_dir.is_dir() else []
    paths = [session_path, *children]

    tool_counts = Counter()
    parent_tool_counts = Counter()
    unique_tool_ids = set()
    usage_by_model = defaultdict(Counter)
    usage_by_layer = defaultdict(lambda: defaultdict(Counter))
    layer_transcripts = Counter()
    layer_responses = Counter()
    response_ids = set()
    parent_responses = 0
    child_responses = 0
    messages_by_file = {}
    send_recipients = set()

    for path in paths:
        layer = layer_of(path, session_path)
        layer_transcripts[layer] += 1
        responses = {}
        for record in read_records(path):
            if record.get("type") != "assistant":
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue

            # JSONLは同じAPI応答を複数行に分割する場合があります。
            message_id = message.get("id") or record.get("uuid")
            if message_id is None:
                continue
            key = (str(path), str(message_id))
            model = str(message.get("model") or "unknown")
            usage = message.get("usage") or {}
            if isinstance(usage, dict):
                prev = responses.setdefault(key, {"model": model, "usage": {}})
                for usage_key in USAGE_KEYS:
                    value = usage.get(usage_key)
                    if isinstance(value, (int, float)) and value >= 0:
                        prev["usage"][usage_key] = max(prev["usage"].get(usage_key, 0), value)

            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                tool_id = block.get("id")
                if not tool_id or (str(path), tool_id) in unique_tool_ids:
                    continue
                unique_tool_ids.add((str(path), tool_id))
                name = str(block.get("name") or "unknown")
                tool_counts[name] += 1
                if path == session_path:
                    parent_tool_counts[name] += 1
                if name == "SendMessage":
                    args = block.get("input") or {}
                    if isinstance(args, dict):
                        send_recipients.add(str(args.get("to") or "unknown"))

        messages_by_file[path.name] = len(responses)
        for key, response in responses.items():
            response_ids.add(key)
            usage_by_model[response["model"]].update(response["usage"])
            usage_by_layer[layer][response["model"]].update(response["usage"])
            layer_responses[layer] += 1
        if path == session_path:
            parent_responses += len(responses)
        else:
            child_responses += len(responses)

    totals = Counter()
    for counter in usage_by_model.values():
        totals.update(counter)
    return {
        "session_id": session_path.stem,
        "child_transcript_count": len(children),
        "api_responses": {"parent": parent_responses, "children": child_responses, "total": len(response_ids)},
        "agent_invocations": {"parent": parent_tool_counts["Agent"], "all": tool_counts["Agent"]},
        "send_message_invocations": {"parent": parent_tool_counts["SendMessage"], "all": tool_counts["SendMessage"]},
        "send_message_recipients": sorted(send_recipients),
        "tokens": {key: totals[key] for key in USAGE_KEYS},
        "tokens_by_model": {model: {key: counts[key] for key in USAGE_KEYS} for model, counts in sorted(usage_by_model.items())},
        "api_responses_by_transcript": messages_by_file,
        "tokens_by_layer": {
            layer: {
                "transcripts": layer_transcripts[layer],
                "api_responses": layer_responses[layer],
                "models": {
                    model: {key: counts[key] for key in USAGE_KEYS}
                    for model, counts in sorted(usage_by_layer[layer].items())
                },
            }
            for layer in sorted(layer_transcripts)
        },
    }


def cell(value) -> str:
    """Markdown表のセルに入れられる文字列にします。"""
    return str(value).replace("|", "/").replace("\n", " ").strip()


def ledger_row(summary: dict, args) -> str:
    """台帳(.claude/knowledge/token-usage-ledger.md)に貼り付ける1行を作ります。

    自動で埋まるのは、トークン、子の新規起動数、SendMessage数だけです。
    それ以外は引数で渡した値をそのまま使い、未指定なら空欄にします。
    """
    by_model = summary["tokens_by_model"]

    def tokens(key: str) -> str:
        return "<br>".join(f"{m}: {c[key]:,}" for m, c in by_model.items()) or "-"

    by_layer = summary["tokens_by_layer"]
    # 層ごとのモデルは、引数がなければ層別集計から自動入力します
    layer_models = args.layer_models or ", ".join(
        f"{layer}: {'/'.join(info['models']) or '-'}" for layer, info in by_layer.items()
    )
    layer_tokens = "層別 in/out/cacheR/cacheW: " + "; ".join(
        f"{layer} "
        + "/".join(
            f"{sum(m[key] for m in info['models'].values()):,}" for key in USAGE_KEYS
        )
        for layer, info in by_layer.items()
    )
    note = "; ".join(part for part in (args.note, layer_tokens) if part)
    cells = [
        args.date or date.today().isoformat(),
        args.workflow,
        args.repo_branch,
        args.snapshot,
        args.round,
        args.layers,
        layer_models,
        tokens("input_tokens"),
        tokens("output_tokens"),
        tokens("cache_read_input_tokens"),
        tokens("cache_creation_input_tokens"),
        summary["agent_invocations"]["all"],
        summary["send_message_invocations"]["all"],
        args.findings,
        args.verdict,
        note,
    ]
    return "| " + " | ".join(cell(c) for c in cells) + " |"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_jsonl", type=Path, help="親セッションの .jsonl ファイル")
    parser.add_argument("--ledger-row", action="store_true", help="JSONの代わりに台帳用のMarkdown表1行を標準出力へ出す(ファイルは書き換えません)")
    for name, help_text in (
        ("date", "日付(省略時は今日)"),
        ("workflow", "例: codex-claude-review / claude-codex-review / standalone cr"),
        ("repo-branch", "リポジトリとブランチ"),
        ("snapshot", "短いSHAと作業ツリーの有無"),
        ("round", "初回 / 再レビュー n"),
        ("layers", "実行した層。再確認だけの層は括弧で示す"),
        ("layer-models", "層ごとのモデル"),
        ("findings", "指摘件数(例: 0/1/2)"),
        ("verdict", "最終判定"),
        ("note", "備考(snapshotの変化、差分だけの再確認、計測方法)"),
    ):
        parser.add_argument(f"--{name}", default="", help=help_text + "(--ledger-row用)")
    args = parser.parse_args()
    summary = summarize(args.session_jsonl)
    if args.ledger_row:
        print(ledger_row(summary, args))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
