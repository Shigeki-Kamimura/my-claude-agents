#!/usr/bin/env python3
"""規則やソースを、出力量と行境界を守って読みます。"""

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path


def read_chunk(path, start_line=1, max_chars=12000, end_line=None):
    data = path.read_bytes()
    lines = io.StringIO(data.decode("utf-8"), newline="").readlines()
    if start_line < 1 or start_line > max(1, len(lines)):
        raise ValueError("開始行がファイルの範囲外です")
    if end_line is not None and (end_line < start_line or end_line > len(lines)):
        raise ValueError("終了行がファイルの範囲外です")
    result = {"path": str(path), "start_line": start_line,
              "end_line": start_line - 1, "total_lines": len(lines),
              "source_sha256": hashlib.sha256(data).hexdigest(),
              "requested_end_line": end_line,
              "range_complete": not lines,
              "next_range_line": start_line if lines else None,
              "next_line": start_line if lines else None,
              "complete": not lines, "text": ""}
    encoded = json.dumps(result, ensure_ascii=False) + "\n"
    if len(encoded) > max_chars:
        raise ValueError("出力上限がメタ情報より小さいです")
    for number in range(start_line, (end_line or len(lines)) + 1):
        candidate = {**result, "end_line": number,
                     "range_complete": number == (end_line or len(lines)),
                     "next_range_line": number + 1 if number < (end_line or len(lines)) else None,
                     "next_line": number + 1 if number < len(lines) else None,
                     "complete": number == len(lines),
                     "text": result["text"] + f"{number}: {lines[number - 1]}"}
        candidate_json = json.dumps(candidate, ensure_ascii=False) + "\n"
        if len(candidate_json) > max_chars:
            if number == start_line:
                raise ValueError(f"{number}行目が収まりません。--max-charsを増やし、同じ行から再開してください")
            break
        result, encoded = candidate, candidate_json
    return encoded


def read_batch(path, max_chars):
    """指定範囲を公平に分け、JSON全体を一つの上限に収めます。"""
    requests = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(requests, list) or not requests:
        raise ValueError("batchには空でないJSON配列を指定してください")
    results = []
    for index, request in enumerate(requests):
        if (not isinstance(request, dict) or not isinstance(request.get("path"), str)
                or not request["path"] or set(request) - {"path", "start_line", "end_line"}):
            raise ValueError("各範囲はpathと任意のstart_line、end_lineで指定してください")
        for key in ("start_line", "end_line"):
            if key in request and type(request[key]) is not int:
                raise ValueError("行番号は整数で指定してください")
        used = len(json.dumps({"reads": results}, ensure_ascii=False)) + 1
        allowance = (max_chars - used) // (len(requests) - index) - 2
        chunk = read_chunk(Path(request["path"]), request.get("start_line", 1),
                           allowance, request.get("end_line"))
        results.append(json.loads(chunk))
    encoded = json.dumps({"reads": results}, ensure_ascii=False) + "\n"
    if len(encoded) > max_chars:
        raise ValueError("batchの出力上限が不足しています")
    return encoded


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--batch", type=Path, help="独立した読取り範囲のJSON配列です")
    parser.add_argument("--start-line", type=int, default=1)
    parser.add_argument("--end-line", type=int)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args(argv)
    if (args.path is None) == (args.batch is None):
        parser.error("pathか--batchを一つ指定してください")
    if args.batch and (args.start_line != 1 or args.end_line is not None):
        parser.error("batchの行番号はJSON内で指定してください")
    try:
        output = (read_batch(args.batch, args.max_chars) if args.batch else
                  read_chunk(args.path, args.start_line, args.max_chars, args.end_line))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
