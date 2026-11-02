#!/usr/bin/env python3
"""明示したCodexログを固定採取し、使用量と会話HTMLを一括保存します。"""

import argparse
import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import re
import sys
import tempfile


def summary_module():
    spec = importlib.util.spec_from_file_location(
        "codex_summary", Path(__file__).with_name("summarize_codex_session.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def redacted_json(value, redact):
    """値を伏せてから符号化し、JSONの引用符と型を保ちます。"""
    def clean(item):
        if isinstance(item, str):
            return redact(item)
        if isinstance(item, dict):
            return {key: clean(child) for key, child in item.items()}
        if isinstance(item, list):
            return [clean(child) for child in item]
        return item
    return json.dumps(clean(value), ensure_ascii=False, indent=2) + "\n"


def freeze(source, target, since, until, parse_timestamp):
    """期間外を除き、不正行は不完全な証拠として残します。"""
    with source.open(encoding="utf-8") as incoming, target.open("w", encoding="utf-8") as outgoing:
        for line in incoming:
            try:
                row = json.loads(line)
                stamp = parse_timestamp(row.get("timestamp"))
            except (ValueError, AttributeError):
                outgoing.write(line)
                continue
            if since <= stamp <= until:
                payload = row.get("payload", {})
                if (row.get("type") == "response_item" and isinstance(payload, dict)
                        and payload.get("type") == "message"
                        and (payload.get("phase") in {"analysis", "summary"}
                             or payload.get("channel") in {"analysis", "summary"})):
                    continue
                outgoing.write(line)


def main(argv=None):
    summary = summary_module()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--child", action="append", default=[], metavar="LABEL=PATH")
    parser.add_argument("--since", required=True, type=summary.timestamp)
    parser.add_argument("--until", required=True, type=summary.timestamp)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--redact-personal", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.since > args.until:
            raise ValueError("開始日時が終了日時より後です")
        paths = {"parent": args.parent}
        for child in args.child:
            label, sep, path = child.partition("=")
            if not sep or not re.fullmatch(r"[A-Za-z0-9_-]+", label) or not path or label in paths:
                raise ValueError("子は重複しない英数字等のLABEL=PATHで指定してください")
            paths[label] = Path(path)
        identities = [(p.stat().st_dev, p.stat().st_ino) for p in paths.values()]
        if len(set(identities)) != len(identities):
            raise ValueError("同じ入力ログが複数回指定されています")
        rr = summary.renderer()
        rr.ensure_safe_output(args.out_dir / "index.html")
        if args.out_dir.exists() or args.out_dir.is_symlink():
            raise ValueError("出力先には未使用のフォルダーを指定してください")
        files, sources, audit = {}, [], {}
        redact = rr.Redactor(personal=args.redact_personal)
        with tempfile.TemporaryDirectory(prefix="codex-review-capture-") as folder:
            frozen = []
            for label, original in paths.items():
                copy = Path(folder) / f"{label}.jsonl"
                freeze(original, copy, args.since, args.until, summary.timestamp)
                frozen.append((label, copy))
                audit[label] = {"source": str(original.resolve()),
                                "window_sha256": hashlib.sha256(copy.read_bytes()).hexdigest()}
            usage_path = Path(folder) / "usage.json"
            command = ["--parent", str(frozen[0][1]), "--since", args.since.isoformat(),
                       "--until", args.until.isoformat(), "--out", str(usage_path)]
            for label, copy in frozen[1:]:
                command += ["--child", f"{label}={copy}"]
            # stdoutを増やさず、既存集計の検証と伏せ処理を使います。
            with redirect_stdout(io.StringIO()):
                if summary.main(command):
                    raise ValueError("使用量の集計に失敗しました")
            usage = json.loads(usage_path.read_text(encoding="utf-8"))
            for label, copy in frozen:
                src = rr.read_source(label, copy, omit_thinking=True)
                src.events = [ev for ev in src.events if ev[2] not in {"thinking", "reasoning", "system"}]
                sources.append(src)
                files[f"chat-{label}.jsonl"] = "".join(json.dumps(
                    {"timestamp": ts, "kind": kind, "role": who, "text": redact(text)},
                    ensure_ascii=False) + "\n" for ts, _, kind, who, text in src.events)
                result = usage["sources"][label]["final_message"]
                if result is not None:
                    files[f"{label}-result.md"] = redact(result) + "\n"
            files["conversation.html"] = rr.build(sources, None, redact)
        files["usage.json"] = redacted_json(usage, redact)
        rows = ["| 担当 | 応答数 | 合計 tokens | 状態 |", "|---|---:|---:|---|"]
        for label, value in usage["sources"].items():
            total = value["tokens"]["total_tokens"] if value["tokens"] else "不明"
            rows.append(f"| {label} | {value['model_responses']} | {total} | {value['status']} |")
        files["usage.md"] = "\n".join(rows) + "\n\n" + "\n".join(usage["limitations"]) + "\n"
        files["audit.json"] = redacted_json(
            {"sources": audit, "window": usage["window"], "redactions": dict(redact.counts)},
            redact)
        result_links = "".join(f'<li><a href="{label}-result.md">{label}の最終返答</a></li>'
                               for label in paths if f"{label}-result.md" in files)
        files["index.html"] = ('<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<title>Codexレビュー記録</title><h1>Codexレビュー記録</h1>'
            '<p><a href="usage.md">使用量</a> / <a href="usage.json">使用量JSON</a> / '
            '<a href="conversation.html">会話</a> / <a href="audit.json">採取条件</a></p>'
            f'<ul>{result_links}</ul><p>最終返答がない担当の判定は未記録です。'
            '実請求額・改善率は未確定です。</p></html>')
        args.out_dir.mkdir(parents=True, mode=0o700)
        for name, content in files.items():
            rr.write_atomic(args.out_dir / name, content.encode("utf-8"))
        print(f"保存しました: {args.out_dir / 'index.html'}")
        print(f"合計tokens: {usage['combined_tokens']['total_tokens'] if usage['combined_tokens'] else '不明'}")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
