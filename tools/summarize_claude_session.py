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


def read_records(path: Path, with_lines=False):
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError(f"JSONLの形式が不正: {path}:{line_no}")
                yield (line_no, record) if with_lines else record
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


def merge_response_usage(response: dict, usage: dict) -> None:
    """分割応答を重複除去し、通常応答に含まれないadvisor使用量も保持します。"""
    entries = [("main", response["model"], usage)]
    for index, iteration in enumerate(usage.get("iterations") or []):
        if isinstance(iteration, dict) and iteration.get("type") == "advisor_message":
            entries.append((f"advisor:{index}", str(iteration.get("model") or "unknown-advisor"), iteration))
    for key, model, values in entries:
        item = response.setdefault("components", {}).setdefault(key, {"model": model, "usage": {}})
        for name in USAGE_KEYS:
            value = values.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                item["usage"][name] = max(item["usage"].get(name, 0), value)


def review_boundary(paths: list[Path]) -> dict:
    """実ツールの公開と呼出しを検査します。レビューの合否は決めません。"""
    allowed = {"Read", "Glob", "Grep", "Agent", "SendMessage"}
    missing, violations, calls, agent_calls = [], [], {}, set()
    for path in paths:
        shape_seen = False
        for line, record in read_records(path, with_lines=True):
            names = []
            if record.get("type") == "api-request-shape":
                tools = record.get("shape", {}).get("tools")
                if isinstance(tools, list):
                    shape_seen = True
                    names.extend(t.get("name", "unknown") for t in tools if isinstance(t, dict))
            attachment = record.get("attachment") or {}
            if attachment.get("type") == "prompt_snapshot" and isinstance(attachment.get("tools"), list):
                names.extend(t.get("name", "unknown") for t in attachment["tools"] if isinstance(t, dict))
            if attachment.get("type") == "advisor_tool" and attachment.get("available") is True:
                names.append("advisor")
            content = record.get("message", {}).get("content", [])
            if record.get("type") == "assistant" and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") in ("tool_use", "server_tool_use"):
                        name = str(block.get("name") or "unknown")
                        names.append(name)
                        if name == "Agent":
                            agent_calls.add((str(path), block.get("id")))
                        if block["type"] == "server_tool_use":
                            key = (str(path), str(block.get("id") or f"line:{line}"))
                            calls[key] = {"source": path.name, "line": line, "name": name, "id": block.get("id")}
            for name in sorted(set(names) - allowed - {"DeferredToolPlaceholder"}):
                violations.append({"source": path.name, "line": line, "name": name})
        if not shape_seen:
            missing.append(path.name)
    if len(agent_calls) > len(paths) - 1:
        missing.append("child transcripts for Agent calls")
    return {"status": "BLOCKED" if violations else "UNCONFIRMED" if missing else "CHECKED",
            "violations": violations, "missing_tool_shapes": missing,
            "server_tool_calls": list(calls.values())}


def input_statistics(inputs):
    """重複除去済みの主応答入力から統計を求めます。"""
    values = sorted(inputs)
    count = len(values)
    return {"samples": count,
            "min_tokens": values[0] if count else None,
            "median_tokens": ((values[(count - 1) // 2] + values[count // 2]) / 2) if count else None,
            "max_tokens": values[-1] if count else None}


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
    context_inputs_by_file = {}
    compaction_boundaries = {}
    context_segments_by_file = {}
    source_reads_by_file = {}
    send_recipients = set()

    for path in paths:
        layer = layer_of(path, session_path)
        layer_transcripts[layer] += 1
        responses = {}
        compact_ids = set()
        segment_boundaries = [None]
        reads = {"read_calls": 0, "explicit_range_calls": 0, "missing_range_calls": 0}
        for index, record in enumerate(read_records(path)):
            if record.get("type") == "system" and record.get("subtype") == "compact_boundary":
                compact_id = record.get("uuid")
                compact_key = compact_id if isinstance(compact_id, str) and compact_id else index
                if compact_key not in compact_ids:
                    compact_ids.add(compact_key)
                    segment_boundaries.append(compact_id if isinstance(compact_id, str) and compact_id else None)
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
                # 分割応答は最初に現れた区間へまとめます。
                prev = responses.setdefault(key, {"model": model, "usage": {}, "segment": len(compact_ids)})
                merge_response_usage(prev, usage)

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
                if name == "Read":
                    args = block.get("input") or {}
                    bounded = isinstance(args, dict) and all(
                        type(args.get(key)) is int and args[key] > 0 for key in ("offset", "limit"))
                    reads["read_calls"] += 1
                    reads["explicit_range_calls" if bounded else "missing_range_calls"] += 1
                if path == session_path:
                    parent_tool_counts[name] += 1
                if name == "SendMessage":
                    args = block.get("input") or {}
                    if isinstance(args, dict):
                        send_recipients.add(str(args.get("to") or "unknown"))

        messages_by_file[path.name] = len(responses)
        # 出力やadvisorの別入力を足さず、主応答の入力だけを数えます。
        inputs = []
        segment_inputs = [[] for _ in segment_boundaries]
        segment_usage = [Counter() for _ in segment_boundaries]
        input_keys = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        for response in responses.values():
            usage = response.get("components", {}).get("main", {}).get("usage", {})
            count = sum(usage.get(name, 0) for name in input_keys)
            if count > 0:
                inputs.append(count)
                segment = response["segment"]
                segment_inputs[segment].append(count)
                segment_usage[segment].update({key: usage.get(key, 0) for key in input_keys})
        context_inputs_by_file[path.name] = input_statistics(inputs)
        context_segments_by_file[path.name] = [
            {"segment": index, "boundary_uuid": boundary, **input_statistics(values),
             "first_tokens": values[0] if values else None,
             "last_tokens": values[-1] if values else None,
             "total_input_tokens": sum(values),
             **{key: segment_usage[index][key] for key in input_keys}}
            for index, (boundary, values) in enumerate(zip(segment_boundaries, segment_inputs))]
        source_reads_by_file[path.name] = reads
        compaction_boundaries[path.name] = len(compact_ids)
        for key, response in responses.items():
            response_ids.add(key)
            for component in response.get("components", {}).values():
                usage_by_model[component["model"]].update(component["usage"])
                usage_by_layer[layer][component["model"]].update(component["usage"])
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
        "review_boundary": review_boundary(paths),
        "child_transcript_count": len(children),
        "api_responses": {"parent": parent_responses, "children": child_responses, "total": len(response_ids)},
        "agent_invocations": {"parent": parent_tool_counts["Agent"], "all": tool_counts["Agent"]},
        "send_message_invocations": {"parent": parent_tool_counts["SendMessage"], "all": tool_counts["SendMessage"]},
        "send_message_recipients": sorted(send_recipients),
        "tokens": {key: totals[key] for key in USAGE_KEYS},
        "tokens_by_model": {model: {key: counts[key] for key in USAGE_KEYS} for model, counts in sorted(usage_by_model.items())},
        "api_responses_by_transcript": messages_by_file,
        "context_inputs_by_transcript": context_inputs_by_file,
        "recorded_compaction_boundaries": compaction_boundaries,
        "context_inputs_by_compaction": context_segments_by_file,
        "source_reads_by_transcript": source_reads_by_file,
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
    ledger_options = (
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
    )
    for name, help_text in ledger_options:
        parser.add_argument(f"--{name}", default="", help=help_text + "(--ledger-row用)")
    parser.add_argument("--check-review-boundary", action="store_true", help="ツール違反は終了1、記録不足は終了2。レビュー承認とは別です")
    args = parser.parse_args()
    if args.check_review_boundary and args.ledger_row:
        parser.error("--check-review-boundary はJSON出力で使ってください")
    if not args.ledger_row:
        # JSON出力では台帳用の値を使わないため、黙って無視せず指定の誤りとして知らせる
        ignored = [f"--{name}" for name, _ in ledger_options if getattr(args, name.replace("-", "_"))]
        if ignored:
            parser.error(f"{', '.join(ignored)} は --ledger-row と一緒に指定してください")
    try:
        summary = summarize(args.session_jsonl)
    except (OSError, ValueError) as exc:
        print(json.dumps({"review_boundary": {"status": "UNCONFIRMED"}, "error": str(exc)}, ensure_ascii=False))
        return 2
    if args.ledger_row:
        print(ledger_row(summary, args))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.check_review_boundary:
        return {"CHECKED": 0, "BLOCKED": 1, "UNCONFIRMED": 2}[summary["review_boundary"]["status"]]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
