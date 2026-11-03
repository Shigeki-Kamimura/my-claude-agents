#!/usr/bin/env python3
"""指定した1層だけを一度実行し、終了した応答をMDへ追記します。"""

import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import uuid

spec = importlib.util.spec_from_file_location("md_review", Path(__file__).with_name("md_review.py"))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
receipt_spec = importlib.util.spec_from_file_location("review_receipts", Path(__file__).with_name("review_receipts.py"))
receipts = importlib.util.module_from_spec(receipt_spec)
receipt_spec.loader.exec_module(receipts)

BACKLOG_READ = ("get_issue", "get_issue_comments", "get_document", "get_document_comments",
                "get_project", "get_wiki", "get_wikis", "get_documents", "get_document_tree")
TOOLS = ["Read", "Glob", "Grep", "Agent", "SendMessage"]


def codex_mcp_overrides(project):
    """有効設定からserver名だけを使い、秘密入りの一覧は保存しません。"""
    result = subprocess.run(["codex", "mcp", "list", "--json"], cwd=project,
                            text=True, capture_output=True, timeout=30, check=True)
    inventory = json.loads(result.stdout)
    if not isinstance(inventory, list):
        raise ValueError("CodexのMCP有効設定を確認できません")
    overrides = ["-c", "features.apps=false"]
    for server in inventory:
        name = server.get("name") if isinstance(server, dict) else None
        if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
            raise ValueError("MCP名の安全な上書き方法を確認できません")
        if name == "md_review" or type(server.get("enabled")) is not bool:
            raise ValueError("予約したMCP名の衝突、または有効状態が未確認です")
        prefix = "mcp_servers." + name
        if name == "backlog" and server.get("enabled") is True:
            overrides += ["-c", prefix + ".enabled_tools=" + json.dumps(list(BACKLOG_READ))]
        else:
            overrides += ["-c", prefix + ".enabled=false"]
    checked = subprocess.run(["codex", *overrides, "mcp", "list", "--json"], cwd=project,
                             text=True, capture_output=True, timeout=30, check=True)
    effective = json.loads(checked.stdout)
    if (not isinstance(effective, list)
            or not all(isinstance(s, dict) for s in effective)
            or {s.get("name") for s in effective if isinstance(s, dict)} != {s["name"] for s in inventory}
            or any(s.get("enabled") is not False for s in effective if s.get("name") != "backlog")
            or any(s.get("enabled") != next(old["enabled"] for old in inventory if old["name"] == "backlog")
                   for s in effective if s.get("name") == "backlog")):
        raise ValueError("Codexの不要MCPを無効化できません")
    if any(s.get("name") == "backlog" and s.get("enabled") is True for s in effective):
        checked = subprocess.run(["codex", *overrides, "mcp", "get", "backlog", "--json"], cwd=project,
                                 text=True, capture_output=True, timeout=30, check=True)
        if set(json.loads(checked.stdout).get("enabled_tools") or []) != set(BACKLOG_READ):
            raise ValueError("Codex Backlogの読取tool制限を確認できません")
    return overrides


def command(config, phase, round_dir, resume=None):
    bridge = {"command": sys.executable, "args": ["-I", "-B", str(review.ROOT / "tools/md_review.py"), "--serve", str(round_dir)]}
    if config["direction"] == "claude-codex-review" or phase == "ci":
        if resume:
            raise ValueError("Codexは毎回fresh execです")
        return ["codex", "exec", "--cd", config["project"], "--sandbox", "read-only", "--json",
                *codex_mcp_overrides(config["project"]),
                "-c", 'mcp_servers.md_review.command=' + json.dumps(bridge["command"]),
                "-c", 'mcp_servers.md_review.args=' + json.dumps(bridge["args"]),
                "-c", "mcp_servers.md_review.enabled=true",
                "-c", 'mcp_servers.md_review.enabled_tools=["git_diff"]',
                "--output-last-message", str(round_dir / "result.md"), "-"]
    # Backlogの秘密値を引数やrun記録へ複製しません。
    settings = {"env": {"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}, "autoCompactWindow": 200000,
                "hooks": {"PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command":
                    __import__("shlex").join([sys.executable, "-I", "-B", str(review.ROOT / "tools/md_review_tool_gate.py")])}]}]}}
    backlog = {"command": "bash", "args": ["-lc", 'source "$HOME/.config/backlog-mcp/env" && exec npx -y backlog-mcp-server']}
    allowed = TOOLS + ["ToolSearch", "mcp__md_review__git_diff"] + ["mcp__backlog__" + n for n in BACKLOG_READ]
    args = ["claude", "--print", "--output-format", "stream-json", "--verbose", "--prompt-suggestions", "false", "--model", "sonnet", "--effort", "medium",
            "--settings", json.dumps(settings), "--strict-mcp-config", "--mcp-config",
            json.dumps({"mcpServers": {"md_review": bridge, "backlog": backlog}}),
            "--permission-mode", "dontAsk", "--tools", ",".join(TOOLS),
            "--allowedTools", *allowed, "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit"]
    if resume:
        args += ["--resume", resume]
    return args


def previous_source(folder, previous, round_dir, before):
    origin = folder / previous["round_id"]
    if origin.parent != folder or origin.is_symlink():
        raise ValueError("前回のsource参照が不正です")
    old = json.loads((origin / "snapshot.json").read_text())
    actual_id = review.digest(json.dumps({k: v for k, v in old.items() if k != "snapshot_id"}, sort_keys=True).encode())
    if actual_id != old.get("snapshot_id") or actual_id != previous.get("result", {}).get("snapshot_id"):
        raise ValueError("比較元snapshotが前回の実確認IDと一致しません")
    target_root = round_dir / "previous"
    target_root.mkdir(mode=0o700)
    old_rows = {p: (mode, sha) for p, view, mode, sha in old["paths"] if view == "worktree"}
    for name, (mode, sha) in old_rows.items():
        source = origin / "worktree" / review.safe_path(name)
        if sha is None:
            if source.exists() or source.is_symlink():
                raise ValueError("前回の空pathが変更されています")
            continue
        if source.is_symlink() or any(p.is_symlink() for p in source.parents if p.is_relative_to(origin)):
            raise ValueError("前回snapshotにsymlinkがあります")
        data = source.read_bytes()
        if review.digest(data) != sha or bool(source.stat().st_mode & 0o100) != (mode == "100755"):
            raise ValueError("前回の確認版が変更されています")
        target = target_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o700 if mode == "100755" else 0o600)
    current = {p: (mode, sha) for p, view, mode, sha in before["paths"] if view == "worktree"}
    changed = sorted(p for p in old_rows.keys() | current.keys() if old_rows.get(p) != current.get(p))
    old_rules, new_rules = dict(old["rules"]), dict(before["rules"])
    return {"previous_snapshot_id": old["snapshot_id"], "changed_paths": changed,
            "rule_changes": sorted(p for p in old_rules.keys() | new_rules.keys() if old_rules.get(p) != new_rules.get(p)),
            "previous_modes": [[p, *old_rows.get(p, (None, None))] for p in changed]}


def save_state(folder, state):
    review.atomic_text(folder / "state.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def child_result_matches(project, native, checked, provider, child_offset=0):
    child = checked["reviewer_id"]
    if provider == "claude":
        if not re.fullmatch(r"[A-Za-z0-9_-]+", child):
            raise ValueError("実子IDの形式が不正です")
        parent_path = receipts.claude_transcript(project, native["parent_session_id"])
        child_path = parent_path.with_suffix("") / "subagents" / ("agent-" + child + ".jsonl")
        messages = receipts.records(child_path, child_offset)
        texts = []
        for row in messages:
            message = row.get("message", {})
            content = message.get("content", []) if isinstance(message, dict) else []
            if row.get("type") == "assistant" and isinstance(content, list):
                text = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
                if text:
                    texts.append(text)
        body = texts[-1] if texts else ""
    else:
        body = native["completed"].get(child, "")
    child_result = receipts.workflow_result(body)
    evidence = child_result.get("invocation_evidence")
    if (not isinstance(evidence, dict) or evidence.get("parent_session_id") not in (None, native["parent_session_id"])
            or evidence.get("reviewer_id") not in (None, child)):
        raise ValueError("子原本が記した親子IDが実行記録と一致しません")
    if receipts.semantic_result(child_result) != receipts.semantic_result(checked["result"]):
        raise ValueError("親の判定欄が実子の最終判定欄と一致しません")


def bind_reviewer(project, native, result, provider, expected_role, child_offset=0, owner=None):
    matches = []
    for child, role in native["children"].items():
        if role not in (None, expected_role):
            continue
        try:
            child_result_matches(project, native, {"reviewer_id": child, "result": result}, provider,
                                 child_offset if owner and owner["reviewer_id"] == child else 0)
        except (ValueError, KeyError, OSError, TypeError):
            continue
        matches.append(child)
    if len(matches) != 1:
        raise ValueError("判定原本に一致する実担当を1人に確定できません")
    native["reviewer_id"] = matches[0]


def run(args):
    folder, config = review.load_run(args.run_dir)
    if args.phase != "ci" and args.phase not in config["layers"]:
        raise ValueError("利用者が選んでいない層は起動できません")
    # lockはホストだけが待ちます。AIの待機・ポーリングはありません。
    lock = os.open(folder / ".lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scope = review.check_scope(config)
        state_file = folder / "state.json"
        if state_file.is_symlink():
            raise ValueError("状態ファイルにsymlinkは使用できません")
        state = json.loads(state_file.read_text()) if state_file.exists() else {"version": 3, "phases": {}}
        if not isinstance(state, dict) or state.get("version") != 3 or not isinstance(state.get("phases"), dict):
            raise ValueError("状態ファイルの形式が未対応です")
        state.setdefault("handoffs", {})
        if not isinstance(state["handoffs"], dict):
            raise ValueError("handoff台帳の形式が不正です")
        phase_state = state["phases"].get(args.phase, {})
        previous = phase_state.get("last_valid")
        owner = phase_state.get("owner") or previous
        policy_id = review.digest(b"".join((review.ROOT / name).read_bytes() for name in (
            "tools/start_md_review.py", "tools/md_review.py", "tools/md_review_tool_gate.py", "tools/review_receipts.py", ".codex/workflows/md-review.md")))
        is_claude = config["direction"] == "codex-claude-review" and args.phase != "ci"
        if owner and is_claude:
            if owner["tool_contract_sha256"] != policy_id or args.resume and args.resume != owner["parent_session_id"]:
                raise ValueError("元の親子またはtool契約を確認できません")
            args.resume = owner["parent_session_id"]
        elif args.resume:
            raise ValueError("このrun/phaseの検証済みClaude親子を確認できません")
        round_dir = folder / str(uuid.uuid4())
        round_dir.mkdir(mode=0o700)
        for view in ("base", "head", "index", "worktree"):
            (round_dir / view).mkdir(mode=0o700)
        before = review.capture(config, round_dir)
        if before != review.capture(config):
            raise ValueError("snapshot取得中にソースが変わりました")
        review.private_write(round_dir / "snapshot.json", json.dumps(before, ensure_ascii=False))
        if args.phase == "ci":
            for selected in config["layers"]:
                approved = state["phases"].get(selected, {})
                if approved.get("status") != "APPROVED" or approved.get("snapshot_id") != before["snapshot_id"]:
                    raise ValueError("選択層の現snapshot承認とhandoff解消が未完了です: " + selected)
            if any(h["status"] not in receipts.CLOSED for h in state["handoffs"].values()):
                raise ValueError("未解決handoffがあるためCIレビューを起動できません")
        rereview = previous is not None and previous["result"]["coverage"] == "COMPLETE"
        comparison = previous_source(folder, previous, round_dir, before) if rereview else None
        if comparison:
            review.private_write(round_dir / "comparison.json", json.dumps(comparison, ensure_ascii=False))
        request = {"workflow_id": config["direction"], "phase": receipts.PHASES[args.phase],
                   "reviewer": review.LAYERS[args.phase], "review_kind": "rereview" if rereview else "continuation" if previous or owner else "initial",
                   "round_id": round_dir.name, "snapshot_file": str(round_dir / "snapshot.json"),
                   "contract_file": str(review.ROOT / ".codex/workflows/md-review.md"),
                   "workflow_file": str(review.ROOT / ".codex/workflows" / ("claude-review.yml" if config["direction"] == "codex-claude-review" else "codex-review.yml")),
                   "role_section": "review_entry.role_sections." + receipts.PHASES[args.phase],
                   "rule_source_files": config["rules"],
                   "policy_sections": ["Pinned source and reconciliation", "Source coverage and role scope",
                                       "User-directed execution permissions", "Rule loading across continuations",
                                       "Evidence and reporting", "Mandatory framework consultation"],
                   "review_role": "external_test_adequacy_reviewer" if args.phase in ("qa", "e2e") else "ci_rubric_reviewer" if args.phase == "ci" else "external_code_reviewer",
                   "scope_check": {"checked": True, "changed_path_count": len(scope["changed_paths"]),
                                   "secret_exclusions": scope["secret_exclusions"], "explicit_exclusions": scope["explicit_exclusions"]},
                   "required_diff_views": ["delta"] if rereview else ["branch", "staged", "unstaged"],
                   "comparison_file": str(round_dir / "comparison.json") if comparison else None,
                   "previous_result_file": str(folder / previous["round_id"] / "result.md") if previous else None,
                   "previous_attempt_file": str(folder / phase_state["latest_attempt"] / "execution.json") if phase_state.get("latest_attempt") else None,
                   "previous_owner": {k: owner[k] for k in ("parent_session_id", "reviewer_id")} if owner else None,
                   "phase_index": {p: {k: v.get(k) for k in ("status", "snapshot_id", "latest_attempt")} for p, v in state["phases"].items()}}
        request["handoff_index"] = state["handoffs"]
        fix_index = folder / "latest-fix.json"
        if fix_index.exists():
            request["latest_fix"] = json.loads(fix_index.read_text())
        review.current_request(folder, request)
        prompt = f"{folder / 'review.md'} を基に{'再レビュー' if previous or owner else 'レビュー'}してください。\n"
        review.private_write(round_dir / "request.txt", prompt)
        try:
            argv = command(config, args.phase, round_dir, args.resume)
        except (ValueError, OSError, subprocess.SubprocessError):
            meta = {"transport": "md-v2", "phase": args.phase, "snapshot_id": before["snapshot_id"],
                    "status": "BLOCKED", "failure": "CLI_CONFIGURATION_UNCONFIRMED", "artifacts": str(round_dir)}
            review.private_write(round_dir / "execution.json", json.dumps(meta, ensure_ascii=False))
            review.append(folder, f"{args.phase} / {round_dir.name}", json.dumps(meta, ensure_ascii=False))
            raise ValueError("CLIの読取制限を確認できないため起動しません")
        env = dict(os.environ)
        env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] = "1"
        failure = None
        transcript_offset = 0
        child_offset = 0
        if is_claude and args.resume:
            transcript = receipts.claude_transcript(config["project"], args.resume)
            if not transcript.is_file() or transcript.is_symlink():
                raise ValueError("再開先の親原本を確認できません")
            transcript_offset = transcript.stat().st_size
            child = transcript.with_suffix("") / "subagents" / ("agent-" + owner["reviewer_id"] + ".jsonl")
            if not child.is_file() or child.is_symlink():
                raise ValueError("再開先の実子原本を確認できません")
            child_offset = child.stat().st_size
        state["phases"][args.phase] = {**phase_state, "status": "PENDING", "snapshot_id": before["snapshot_id"], "latest_attempt": round_dir.name}
        save_state(folder, state)
        with open(round_dir / "stdout.jsonl", "x", opener=lambda p, f: os.open(p, f, 0o600)) as output:
            with open(round_dir / "stderr.log", "x", opener=lambda p, f: os.open(p, f, 0o600)) as errors:
                try:
                    with subprocess.Popen(argv, text=True, stdin=subprocess.PIPE, stdout=output, stderr=errors,
                                          cwd=config["project"], env=env, start_new_session=True) as process:
                        try:
                            process.communicate(prompt, timeout=args.timeout)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGTERM)
                            try:
                                process.communicate(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                process.communicate()
                            failure = "TIMEOUT"
                        exit_code = process.returncode
                except OSError:
                    exit_code, failure = None, "CLI_START_FAILED"
        try:
            review.check_scope(config)
            changed = before != review.capture(config)
        except (ValueError, OSError, subprocess.SubprocessError):
            changed = True
        meta = {"transport": "md-v3", "phase": args.phase, "snapshot_id": before["snapshot_id"], "exit_code": exit_code,
                "source_changed": changed, "resume": args.resume, "artifacts": str(round_dir),
                "failure": failure, "argv": argv, "tool_contract_sha256": policy_id,
                "status": "PENDING_RESULT_VALIDATION" if exit_code == 0 and not changed and not failure else "BLOCKED"}
        if is_claude:
            try:
                native = {}
                with (round_dir / "stdout.jsonl").open() as records:
                    for line in records:
                        record = json.loads(line)
                        if not isinstance(record, dict):
                            raise ValueError("CLI応答がobjectではありません")
                        if record.get("type") == "result":
                            native = record
                body = native.get("result", "")
                meta["session_id"] = native.get("session_id")
                if native.get("is_error") or not meta["session_id"] or not isinstance(body, str) or not body:
                    meta["status"] = "BLOCKED"
                    body = "Claudeの最終応答が欠落または失敗しました。原本ログを参照してください。"
                review.private_write(round_dir / "result.md", body)
            except (ValueError, TypeError):
                meta["status"] = "BLOCKED"
        result_path = round_dir / "result.md"
        if result_path.is_symlink():
            raise ValueError("最終応答がsymlinkです")
        body = result_path.read_text() if result_path.is_file() else "最終応答がありません。"
        if not result_path.is_file():
            meta["status"] = "BLOCKED"
        try:
            rows = receipts.records(round_dir / "stdout.jsonl")
            if is_claude and meta.get("session_id"):
                rows += receipts.records(receipts.claude_transcript(config["project"], meta["session_id"]), transcript_offset)
            native = receipts.identities(rows, "claude" if is_claude else "codex", review.LAYERS[args.phase], owner)
            meta["parent_session_id"] = native["parent_session_id"]
            candidates = [child for child, role in native["children"].items() if role == review.LAYERS[args.phase]]
            if len(candidates) == 1 and re.fullmatch(r"[A-Za-z0-9_-]+", candidates[0]):
                state["phases"][args.phase]["owner"] = {"parent_session_id": native["parent_session_id"],
                    "reviewer_id": candidates[0], "tool_contract_sha256": policy_id, "result": {"open_item_ids": []}}
            if meta["status"] == "BLOCKED":
                raise ValueError("CLI失敗、原本欠落またはsource変更です")
            result = receipts.workflow_result(body)
            bind_reviewer(config["project"], native, result, "claude" if is_claude else "codex",
                          review.LAYERS[args.phase], child_offset, owner)
            checked = receipts.validate(result, {**config, "reviewer": review.LAYERS[args.phase]}, args.phase,
                                        before["snapshot_id"], native, previous or owner, state["handoffs"])
            state["handoffs"] = receipts.update_handoffs(state["handoffs"], result, checked["reviewer_id"], round_dir.name)
            meta.update({k: checked[k] for k in ("parent_session_id", "reviewer_id", "approved")})
            meta["status"] = "APPROVED" if checked["approved"] else "REVIEWED"
            state["phases"][args.phase] = {"status": meta["status"], "snapshot_id": before["snapshot_id"],
                "latest_attempt": round_dir.name,
                "owner": {"parent_session_id": checked["parent_session_id"], "reviewer_id": checked["reviewer_id"],
                          "tool_contract_sha256": policy_id, "result": {"open_item_ids": []}},
                "last_valid": {**checked, "round_id": round_dir.name, "tool_contract_sha256": policy_id}}
        except (ValueError, KeyError, TypeError, OSError) as error:
            meta["status"] = "BLOCKED"
            meta["validation_error"] = str(error)
            state["phases"][args.phase]["status"] = "BLOCKED"
        save_state(folder, state)
        review.private_write(round_dir / "execution.json", json.dumps(meta, ensure_ascii=False, indent=2))
        review.append(folder, f"{args.phase} / {round_dir.name}",
                      "```json\n" + json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False, indent=2) + "\n```\n\n" + body)
        request["phase_index"] = {p: {k: v.get(k) for k in ("status", "snapshot_id", "latest_attempt")} for p, v in state["phases"].items()}
        request["handoff_index"] = state["handoffs"]
        request["execution_result_file"] = str(round_dir / "execution.json")
        review.current_request(folder, request)
        print(json.dumps(meta, ensure_ascii=False))
        return 0 if meta["status"] in ("APPROVED", "REVIEWED") else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=tuple(review.LAYERS), required=True)
    parser.add_argument("--resume", help="同phaseの検証済みClaude親session IDだけです")
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    try:
        return run(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
