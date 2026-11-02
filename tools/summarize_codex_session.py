#!/usr/bin/env python3
"""明示したCodexログと期間から、親子別の使用量を集計します。"""

import argparse
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

KEYS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
        "output_tokens", "reasoning_output_tokens", "total_tokens")


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("日時にはタイムゾーン付きISO 8601を指定してください") from exc
    if parsed.tzinfo is None:
        raise ValueError("日時にはタイムゾーンが必要です")
    return parsed


def checked_usage(values):
    if not isinstance(values, dict) or not {"input_tokens", "output_tokens", "total_tokens"} <= values.keys():
        raise ValueError("応答別の使用量が不足しています")
    usage = {key: values.get(key, 0) for key in KEYS}
    if any(type(v) is not int or v < 0 for v in usage.values()):
        raise ValueError("使用量は0以上の整数である必要があります")
    if (usage["input_tokens"] + usage["output_tokens"] != usage["total_tokens"]
            or usage["cached_input_tokens"] > usage["input_tokens"]
            or usage["reasoning_output_tokens"] > usage["output_tokens"]):
        raise ValueError("使用量の合計または内数が一致しません")
    return usage


def summarize(path, since=None, until=None):
    responses, calls, malformed = {}, Counter(), 0
    completed, final = None, None
    last_record = None
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("行がオブジェクトではありません")
                stamp = timestamp(row.get("timestamp"))
                payload = row.get("payload", {})
                if not isinstance(payload, dict):
                    raise ValueError("payloadが不正です")
            except (ValueError, TypeError):
                malformed += 1
                continue
            if (since and stamp < since) or (until and stamp > until):
                continue
            kind, subkind = row.get("type"), payload.get("type")
            if kind == "token_usage_record":
                response_id = payload.get("response_id")
                if not isinstance(response_id, str) or not response_id:
                    raise ValueError("応答識別子がありません")
                usage = checked_usage(payload.get("usage"))
                if response_id in responses and responses[response_id] != usage:
                    raise ValueError("同じ応答識別子に異なる使用量があります")
                responses[response_id] = usage
                last_record = row["timestamp"]
            elif kind == "response_item":
                if subkind in ("function_call", "custom_tool_call"):
                    calls[str(payload.get("name", "unknown"))] += 1
                elif (subkind == "message" and payload.get("role") == "assistant"
                      and (payload.get("phase") == "final" or payload.get("channel") == "final")
                      and payload.get("phase") not in ("analysis", "summary")
                      and payload.get("channel") not in ("analysis", "summary")):
                    final = payload.get("content")
            elif kind == "event_msg" and subkind == "task_complete":
                if payload.get("last_agent_message") is not None:
                    completed = payload["last_agent_message"]
    totals = None
    if responses:
        totals = {key: sum(value[key] for value in responses.values()) for key in KEYS}
        totals["uncached_input_tokens"] = totals["input_tokens"] - totals["cached_input_tokens"]
    return {"tokens": totals, "model_responses": len(responses),
            "top_level_tool_calls": dict(calls),
            "final_message": completed if completed is not None else final,
            "malformed_lines": malformed,
            "status": "PARTIAL" if malformed else ("AVAILABLE" if responses else "NOT_AVAILABLE"),
            "latest_usage_timestamp": last_record}


def renderer():
    spec = importlib.util.spec_from_file_location("review_record", Path(__file__).with_name("render_review_record.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--child", action="append", default=[], metavar="LABEL=PATH")
    parser.add_argument("--since", type=timestamp)
    parser.add_argument("--until", type=timestamp)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.since and args.until and args.since > args.until:
            raise ValueError("開始日時が終了日時より後です")
        paths = {"parent": args.parent}
        for child in args.child:
            label, separator, path = child.partition("=")
            if not separator or not label or not path or label in paths:
                raise ValueError("子は重複のないLABEL=PATHで指定してください")
            paths[label] = Path(path)
        real_paths = [path.resolve() for path in paths.values()]
        identities = [(path.stat().st_dev, path.stat().st_ino) for path in real_paths]
        if len(set(identities)) != len(identities):
            raise ValueError("同じ入力ログが複数回指定されています")
        if args.out and args.out.exists() and any(args.out.samefile(path) for path in real_paths):
            raise ValueError("出力先が入力と同じです")
        sources = {label: summarize(path, args.since, args.until) for label, path in paths.items()}
        rr = renderer()
        redact = rr.Redactor()
        for source in sources.values():
            if source["final_message"] is not None:
                source["final_message"] = redact(rr.text_of(source["final_message"]))
        combined = None
        if all(source["tokens"] is not None for source in sources.values()):
            combined = {key: sum(s["tokens"][key] for s in sources.values())
                        for key in (*KEYS, "uncached_input_tokens")}
        result = {"sources": sources, "combined_tokens": combined, "actual_cost": None,
                  "window": {"since": args.since.isoformat() if args.since else None,
                             "until": args.until.isoformat() if args.until else None},
                  "limitations": ["キャッシュと推論は内数です。実請求額や削減率を示しません。",
                                  "応答別token_usage_recordだけを集計し、累計イベントで代用しません。",
                                  "PARTIALは読めない行があります。保存後の応答は含みません。"]}
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            rr.ensure_safe_output(args.out)
            args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            rr.write_atomic(args.out, output.encode("utf-8"))
            print(f"保存しました: {args.out}")
        else:
            sys.stdout.write(output)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
