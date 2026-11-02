#!/usr/bin/env python3
"""規則やソースを、出力量と行境界を守って読みます。"""

import argparse
import json
import sys
from pathlib import Path


def read_chunk(path, start_line=1, max_chars=12000):
    with path.open(encoding="utf-8", newline="") as stream:
        lines = stream.readlines()
    if start_line < 1 or start_line > max(1, len(lines)):
        raise ValueError("開始行がファイルの範囲外です")
    result = {"path": str(path), "start_line": start_line,
              "end_line": start_line - 1, "total_lines": len(lines),
              "next_line": start_line if lines else None,
              "complete": not lines, "text": ""}
    encoded = json.dumps(result, ensure_ascii=False) + "\n"
    if len(encoded) > max_chars:
        raise ValueError("出力上限がメタ情報より小さいです")
    for number in range(start_line, len(lines) + 1):
        candidate = {**result, "end_line": number,
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--start-line", type=int, default=1)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args(argv)
    try:
        output = read_chunk(args.path, args.start_line, args.max_chars)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
