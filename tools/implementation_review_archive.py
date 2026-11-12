"""公開会話だけを既存rendererへ渡し、実行単位のHTMLを保存します。"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from typing import Any

HIDDEN_ROLES = {"system", "developer", "analysis", "thinking", "reasoning"}
HIDDEN_CHANNELS = {"analysis", "thinking", "reasoning", "summary"}
VISIBLE_ROLES = {"user", "assistant", "tool"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_regular(path: Path) -> None:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("会話記録のsymlinkは使用できません")
    if not path.is_file():
        raise ValueError("会話記録がありません")


def atomic_write(path: Path, data: bytes) -> None:
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("保存先にsymlinkがあります")
    if path.exists() and path.stat().st_nlink != 1:
        raise ValueError("管理ファイルにhardlinkがあります")
    fd, temporary = tempfile.mkstemp(prefix=".record-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def renderer_from(path: Path | None = None):
    target = path or Path(__file__).with_name("render_review_record.py")
    safe_regular(target)
    spec = importlib.util.spec_from_file_location("loop_record_renderer", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def visible_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(visible_text(v) for v in value
                         if isinstance(v, dict) and v.get("type") in {"text", "input_text", "output_text"})
    if isinstance(value, dict) and isinstance(value.get("text"), str):
        return value["text"]
    return ""


def public_rows(row: dict) -> tuple[list[tuple[str, str, str]], str]:
    """正規化前に非公開のrole/channel/blockを除きます。"""
    if row.get("role") in HIDDEN_ROLES or row.get("channel") in HIDDEN_CHANNELS:
        return [], "omitted"
    if row.get("type") in {"user", "assistant"} and isinstance(row.get("message"), dict):
        role, message = row["type"], row["message"]
        if message.get("role") in HIDDEN_ROLES or message.get("channel") in HIDDEN_CHANNELS:
            return [], "omitted"
        content = message.get("content")
        if isinstance(content, str):
            return [("message", role, content)], "recognized"
        if not isinstance(content, list):
            return [], "unknown"
        events = []
        unknown = False
        for block in content:
            if not isinstance(block, dict):
                unknown = True
                continue
            kind = block.get("type")
            if kind in {"thinking", "reasoning", "redacted_thinking"}:
                continue
            if kind == "text":
                events.append(("message", role, visible_text(block)))
            elif kind == "tool_use":
                # 呼出し引数を全文出力しません。埋め込まれたsystem等を避けます。
                events.append(("tool_use", str(block.get("name", "tool")), "ツール呼出し。引数は安全のためHTMLでは省略しています。"))
            elif kind == "tool_result":
                events.append(("tool_result", "tool", visible_text(block.get("content"))))
            else:
                unknown = True
        return events, "unknown" if unknown else "recognized"
    # CLI失敗時にも、取得済みの公開応答だけを残します。
    if row.get("type") == "result" and isinstance(row.get("result"), str):
        return [("message", "assistant", row["result"])], "recognized"
    if row.get("type") == "item.completed" and isinstance(row.get("item"), dict):
        item = row["item"]
        if item.get("type") in {"reasoning", "thinking"} or item.get("channel") in HIDDEN_CHANNELS:
            return [], "omitted"
        if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
            return [("message", "assistant", item["text"])], "recognized"
        return [], "unknown"
    if row.get("type") in {"thread.started", "turn.started", "turn.completed"}:
        return [], "omitted"
    payload = row.get("payload")
    if isinstance(payload, dict):
        if payload.get("role") in HIDDEN_ROLES or payload.get("channel") in HIDDEN_CHANNELS:
            return [], "omitted"
        top, kind = row.get("type"), payload.get("type")
        if top in {"session_meta", "turn_context", "inter_agent_communication_metadata"}:
            return [], "omitted"
        if top == "response_item":
            if kind in {"reasoning", "thinking"}:
                return [], "omitted"
            if kind == "message" and payload.get("role") in VISIBLE_ROLES:
                return [("message", payload["role"], visible_text(payload.get("content")))], "recognized"
            if kind in {"function_call", "custom_tool_call"}:
                return [("tool_use", str(payload.get("name", "tool")), "ツール呼出し。引数は安全のためHTMLでは省略しています。")], "recognized"
            if kind in {"function_call_output", "custom_tool_call_output"}:
                return [("tool_result", "tool", visible_text(payload.get("output")))], "recognized"
        if top == "event_msg":
            if kind in {"user_message", "agent_message"} and isinstance(payload.get("message"), str):
                role = "user" if kind == "user_message" else "assistant"
                return [("message", role, payload["message"])], "duplicate_candidate"
            if kind in {"token_count", "task_started", "task_complete", "turn_aborted", "sub_agent_activity"}:
                return [], "omitted"
        return [], "unknown"
    if row.get("role") in VISIBLE_ROLES and isinstance(row.get("text"), str):
        return [("message", row["role"], row["text"])], "recognized"
    # 新形式は推測せず欠落として表示します。
    return [], "unknown"


def read_window(renderer, item: dict):
    label = item["label"]
    source = renderer.Source(label, Path("visible-transcript"))
    stats = {"owner_id": item["owner_id"], "label": label, "status": "COMPLETE", "sha256": None,
             "start": item.get("start"), "end": item.get("end"), "unknown_rows": 0,
             "unreadable_rows": 0, "omitted_rows": 0, "visible_events": 0}
    pending = []
    try:
        path = Path(item["path"])
        safe_regular(path)
        start, end = item.get("start"), item.get("end")
        if type(start) is not int or type(end) is not int or not 0 <= start <= end <= path.stat().st_size:
            raise ValueError("会話の固定範囲が不正です")
        with path.open("rb") as stream:
            if start:
                stream.seek(start - 1)
                if stream.read(1) != b"\n":
                    raise ValueError("会話の開始位置が行境界ではありません")
            stream.seek(start)
            data = stream.read(end - start)
        if len(data) != end - start or data and not data.endswith(b"\n"):
            raise ValueError("会話の固定範囲が途中で切れています")
        stats["sha256"] = digest(data)
        for number, line in enumerate(data.splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line.decode("utf-8"))
                if not isinstance(row, dict):
                    raise ValueError("object以外です")
            except (ValueError, UnicodeError):
                stats["unreadable_rows"] += 1
                continue
            events, status = public_rows(row)
            if status == "unknown":
                stats["unknown_rows"] += 1
            elif status == "omitted":
                stats["omitted_rows"] += 1
            timestamp = row.get("timestamp", "")
            timestamp = timestamp if isinstance(timestamp, str) else ""
            target = pending if status == "duplicate_candidate" else source.events
            for kind, who, body in events:
                target.append((timestamp, number, kind, who, body))
        seen = {(e[3], e[4].strip()) for e in source.events if e[2] == "message"}
        source.events.extend(e for e in pending if (e[3], e[4].strip()) not in seen)
        if stats["unknown_rows"] or stats["unreadable_rows"] or not source.events:
            stats["status"] = "PARTIAL"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        stats["status"] = "PARTIAL"
        stats["error"] = type(exc).__name__ + ": " + str(exc)
    source.unreadable = stats["unreadable_rows"]
    source.unrecognized = stats["unknown_rows"]
    source.format["visible_only"] += len(source.events)
    source.skipped["非公開欄の除外"] = stats["omitted_rows"]
    stats["visible_events"] = len(source.events)
    return source, stats


def save_record(folder: Path, revision: int, state: dict, sources: list[dict],
                expected_owners: set[str], renderer_path: Path | None = None) -> dict:
    """指定した会話だけを保存します。全セッション探索はしません。"""
    renderer = renderer_from(renderer_path)
    if any(p.is_symlink() for p in (folder, *folder.parents)):
        raise ValueError("記録先にsymlinkがあります")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    record_dir = folder / "records"
    record_dir.mkdir(exist_ok=True, mode=0o700)
    out = record_dir / f"record-{revision:06d}.html"
    manifest_path = record_dir / f"record-{revision:06d}.json"
    if out.exists() or manifest_path.exists():
        raise ValueError("既存の記録番号は上書きできません")
    parsed, metadata = [], []
    identifiers = set()
    for item in sources:
        if item["owner_id"] in identifiers:
            raise ValueError("会話記録のownerが重複しています")
        identifiers.add(item["owner_id"])
        source, stats = read_window(renderer, item)
        parsed.append(source)
        metadata.append(stats)
    missing = sorted(expected_owners - identifiers)
    complete = not missing and all(x["status"] == "COMPLETE" for x in metadata)
    manifest = {"schema_version": 1, "run_id": state.get("run_id"), "revision": revision,
                "status": "COMPLETE" if complete else "PARTIAL", "missing_owners": missing,
                "sources": metadata, "hidden_content": "EXCLUDED", "redaction": "pattern-based; manual check required"}
    summary = renderer.Source("進行記録", Path("workflow-status"))
    summary.format["generic"] = 1
    summary.events.append((state.get("updated_at", ""), 0, "message", "workflow",
        json.dumps({"stage": state.get("stage"), "status": state.get("status"),
                    "snapshot_id": state.get("snapshot_id"), "rules_id": state.get("rules_id"),
                    "stop_reason": state.get("stop_reason"), "archive": manifest}, ensure_ascii=False, indent=2)))
    ledger = [{"id": f.get("key"), "severity": f.get("severity"), "summary": f.get("summary"),
               "before": f.get("evidence"), "after": f.get("closure", {}).get("evidence"),
               "files": f.get("locations", []), "status": f.get("status")}
              for f in state.get("ledger", {}).values()]
    redactor = renderer.Redactor(personal=False)
    body = renderer.build([summary, *parsed], ledger, redactor)
    # JS、外部通信、リンク先の能動読込みを無効化します。
    csp = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
    body = body.replace("<head>", "<head>" + csp, 1)
    data = body.encode("utf-8", errors="replace")
    manifest["html_sha256"] = digest(data)
    manifest["html_path"] = str(out)
    atomic_write(out, data)
    atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2).encode())
    atomic_write(folder / "index.html", data)
    return manifest
