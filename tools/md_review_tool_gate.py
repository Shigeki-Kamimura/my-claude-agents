#!/usr/bin/env python3
"""MDレビューの親子で、許可した読取tool以外を拒否します。"""
import json
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("start_md_review", Path(__file__).with_name("start_md_review.py"))
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def main():
    allowed = set(launcher.TOOLS) | {"ToolSearch"} | {"mcp__md_review__" + name for name in launcher.MD_TOOLS} | {"mcp__backlog__" + name for name in launcher.BACKLOG_READ}
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") not in allowed:
            print("MDレビューではこのtoolを許可していません。必要な実行は実装担当へ返してください。", file=sys.stderr)
            return 2
    except (ValueError, TypeError):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
