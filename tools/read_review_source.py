#!/usr/bin/env python3
"""規則やソースを、出力量と行境界を守って読みます。"""

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path


class _SourceRange:
    def __init__(self, path, start_line, end_line, limit):
        data = path.read_bytes()
        lines = io.StringIO(data.decode("utf-8"), newline="").readlines()
        total = len(lines)
        if start_line < 1 or start_line > max(1, total):
            raise ValueError("開始行がファイルの範囲外です")
        if end_line is not None and (end_line < start_line or end_line > total):
            raise ValueError("終了行がファイルの範囲外です")

        self.last = end_line if end_line is not None else total
        self.value = {"path": str(path), "start_line": start_line,
                      "end_line": start_line - 1, "total_lines": total,
                      "source_sha256": hashlib.sha256(data).hexdigest(),
                      "requested_end_line": end_line,
                      "range_complete": not lines, "next_range_line": start_line if lines else None,
                      "next_line": start_line if lines else None, "complete": not lines, "text": ""}
        self.size = len(json.dumps(self.value, ensure_ascii=False))
        if self.size > limit:
            raise ValueError("出力上限がメタ情報より小さいです")

        # 他の範囲への配分中は、出力し得る行だけを保持します。
        self.lines = []
        remaining = limit
        for number in range(start_line, self.last + 1):
            line = lines[number - 1]
            length = len(str(number)) + 2 + len(line)
            if length > remaining:
                break
            self.lines.append(f"{number}: {line}")
            remaining -= length
        if total and (not self.lines or not self._append(0, limit)):
            raise ValueError(f"{start_line}行目が収まりません。--max-charsを増やし、同じ行から再開してください")

    def _append(self, offset, limit):
        number = self.value["start_line"] + offset
        total = self.value["total_lines"]
        candidate = {**self.value, "end_line": number,
                     "range_complete": number == self.last,
                     "next_range_line": number + 1 if number < self.last else None,
                     "next_line": number + 1 if number < total else None,
                     "complete": number == total, "text": self.value["text"] + self.lines[offset]}
        size = len(json.dumps(candidate, ensure_ascii=False))
        if size > limit:
            return False
        self.value, self.size = candidate, size
        return True

    def extend(self, available):
        """行を追加した分の文字数を返します。"""
        initial = self.size
        if available > 0:
            start = self.value["end_line"] + 1 - self.value["start_line"]
            for offset in range(start, len(self.lines)):
                if not self._append(offset, initial + available):
                    break
        return self.size - initial


def read_chunk(path, start_line=1, max_chars=12000, end_line=None):
    limit = max_chars - 1  # 末尾の改行分です。
    page = _SourceRange(path, start_line, end_line, limit)
    page.extend(limit - page.size)
    return json.dumps(page.value, ensure_ascii=False) + "\n"


def read_batch(path, max_chars):
    """各範囲の先頭行を確保し、余った文字数を未完了の範囲に配ります。"""
    requests = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(requests, list) or not requests:
        raise ValueError("batchには空でないJSON配列を指定してください")
    available = max_chars - len('{"reads": []}\n') - len(", ") * (len(requests) - 1)
    pages = []
    for request in requests:
        if (not isinstance(request, dict) or not isinstance(request.get("path"), str)
                or not request["path"] or set(request) - {"path", "start_line", "end_line"}):
            raise ValueError("各範囲はpathと任意のstart_line、end_lineで指定してください")
        for key in ("start_line", "end_line"):
            if key in request and type(request[key]) is not int:
                raise ValueError("行番号は整数で指定してください")
        page = _SourceRange(Path(request["path"]), request.get("start_line", 1),
                            request.get("end_line"), available)
        pages.append(page)
        available -= page.size

    for index, page in enumerate(pages):
        available -= page.extend(available // (len(pages) - index))
    for page in pages:
        available -= page.extend(available)
    return json.dumps({"reads": [page.value for page in pages]}, ensure_ascii=False) + "\n"


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
