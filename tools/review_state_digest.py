#!/usr/bin/env python3
"""新規担当へ渡すreview_state_digestと、前担当の文脈サイズ読取を行います。

state/MD/前回の実記録だけから決定的に作り、モデルを起動せず、判定や承認は含めません。
"""

import hashlib
import json
from pathlib import Path

LEDGER_MAX = 200
TAIL_BYTES = 262144
POLICY = ("前担当の承認・判定は引き継がれません。全open IDを今回のdeltaと必要な原本で独立に再判定してください。",
          "unchangedの規則は、前担当が読んだとrecordされた範囲だけをSupplied根拠として扱えます(自分の承認ではありません)。",
          "Readするのは、shaが変わった/追加された規則、manifestにない節でdeltaが必要とするもの、delta、各open IDの再判定に必要な原本です。",
          "files_readは前担当のRead要求の記録で、本文が届いた証明ではありません。")


def child_transcript(receipts, project, owner):
    parent = receipts.claude_transcript(project, owner["parent_session_id"])
    return parent.with_suffix("") / "subagents" / ("agent-" + owner["reviewer_id"] + ".jsonl")


def _rows(path, tail=False):
    """転記を読みます。tailは末尾だけで、壊れた行は無視します。"""
    if not path.is_file() or path.is_symlink():
        return []
    with path.open("rb") as stream:
        if tail:
            size = path.stat().st_size
            stream.seek(max(0, size - TAIL_BYTES))
            data = stream.read().split(b"\n", 1)[-1] if size > TAIL_BYTES else stream.read()
        else:
            data = stream.read()
    rows = []
    for line in data.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def context_tokens(path):
    """子転記の最後のassistant応答に記録されたinput規模(入力+cache読込+cache作成)。不明ならNone。"""
    for row in reversed(_rows(path, tail=True)):
        message = row.get("message")
        usage = message.get("usage") if isinstance(message, dict) else None
        if row.get("type") == "assistant" and isinstance(usage, dict):
            parts = [usage.get(k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")]
            if all(type(p) is int for p in parts if p is not None) and any(p is not None for p in parts):
                return sum(p or 0 for p in parts)
    return None


def read_requests(path):
    """前担当のRead要求を path -> [[offset, limit], ...] にします。重複なし・決定的な順序です。"""
    found = {}
    for row in _rows(path):
        message = row.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if row.get("type") != "assistant" or not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Read":
                args = block.get("input") if isinstance(block.get("input"), dict) else {}
                target = args.get("file_path")
                if isinstance(target, str):
                    pair = [args.get("offset") if type(args.get("offset")) is int else None,
                            args.get("limit") if type(args.get("limit")) is int else None]
                    found.setdefault(target, [])
                    if pair not in found[target]:
                        found[target].append(pair)
    return {p: sorted(v, key=lambda r: (r[0] is not None, r[0] or 0, r[1] is not None, r[1] or 0)) for p, v in found.items()}


def snapshot_delta(old, new):
    """前回と今回のsnapshot記録から、変更したworktree pathと規則pathを求めます。"""
    before = {p: (mode, sha) for p, view, mode, sha in old["paths"] if view == "worktree"}
    after = {p: (mode, sha) for p, view, mode, sha in new["paths"] if view == "worktree"}
    old_rules, new_rules = dict(old["rules"]), dict(new["rules"])
    return (sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p)),
            sorted(p for p in old_rules.keys() | new_rules.keys() if old_rules.get(p) != new_rules.get(p)))


def build(project, old, new_rules, new_snapshot_id, changed_paths, rule_changes, reads, predecessor,
          result_reference, open_ids, handoffs):
    """決定的なdigestを返します。(本文, sha256)。new_rulesは [[path, sha], ...] です。"""
    old_rules, current = dict(old["rules"]), dict(new_rules)
    manifest = []
    for path in sorted(old_rules.keys() | current.keys()):
        status = ("added" if path not in old_rules else "removed" if path not in current
                  else "unchanged" if old_rules[path] == current[path] else "changed")
        requests = reads.get(path, []) if status == "unchanged" else []
        manifest.append({"path": path, "status": status, "sha256_at_predecessor": old_rules.get(path),
                         "sha256_now": current.get(path), "predecessor_read_requests": requests,
                         "credit": "predecessor_read_supplied" if requests else "none_read_in_full"})
    worktree = {p: sha for p, view, _mode, sha in old["paths"] if view == "worktree"}
    root = str(Path(project)) + "/"
    files = []
    for target, requests in sorted(reads.items()):
        if target in old_rules:
            continue
        relative = target[len(root):] if target.startswith(root) else target
        files.append({"path": target, "blob_sha256_at_predecessor_snapshot": worktree.get(relative),
                      "read_requests": requests})
    digest = {"kind": "review_state_digest", "version": 1, "predecessor": predecessor,
              "predecessor_result_reference": result_reference,
              "rules_manifest": manifest, "files_read": files[:LEDGER_MAX], "files_read_truncated": len(files) > LEDGER_MAX,
              "delta": {"previous_snapshot_id": old.get("snapshot_id"), "snapshot_id": new_snapshot_id,
                        "changed_paths": changed_paths, "rule_changes": rule_changes,
                        "callers": "not derived; use the git_diff delta view and read direct callers as needed"},
              "open_items": {"finding_ids": sorted(open_ids),
                             "handoffs": {k: {f: v.get(f) for f in ("owner", "status", "weight")} for k, v in sorted(handoffs.items())}},
              "policy": list(POLICY)}
    text = json.dumps(digest, ensure_ascii=False, sort_keys=True, indent=2)
    return text, hashlib.sha256(text.encode()).hexdigest()
