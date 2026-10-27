#!/usr/bin/env python3
"""Claude Code親セッションと子agentのJSONLを集計します。"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

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
    response_ids = set()
    parent_responses = 0
    child_responses = 0
    messages_by_file = {}
    send_recipients = set()

    for path in paths:
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
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_jsonl", type=Path, help="親セッションの .jsonl ファイル")
    args = parser.parse_args()
    print(json.dumps(summarize(args.session_jsonl), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
