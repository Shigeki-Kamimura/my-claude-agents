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
    args = ["claude", "--print", "--output-format", "stream-json", "--verbose", "--model", "sonnet", "--effort", "medium",
            "--settings", json.dumps(settings), "--strict-mcp-config", "--mcp-config",
            json.dumps({"mcpServers": {"md_review": bridge, "backlog": backlog}}),
            "--permission-mode", "dontAsk", "--tools", ",".join(TOOLS),
            "--allowedTools", *allowed, "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit"]
    if resume:
        args += ["--resume", resume]
    return args


def run(args):
    folder, config = review.load_run(args.run_dir)
    if args.phase != "ci" and args.phase not in config["layers"]:
        raise ValueError("利用者が選んでいない層は起動できません")
    # lockはホストだけが待ちます。AIの待機・ポーリングはありません。
    lock = os.open(folder / ".lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        policy_id = review.digest(b"".join((review.ROOT / name).read_bytes() for name in (
            "tools/start_md_review.py", "tools/md_review.py", "tools/md_review_tool_gate.py", ".codex/workflows/md-review.md")))
        if args.resume:
            matches = []
            for path in folder.glob("*/execution.json"):
                if path.is_symlink() or path.parent.is_symlink():
                    continue
                previous = json.loads(path.read_text())
                if (previous.get("session_id") == args.resume and previous.get("phase") == args.phase
                        and previous.get("transport") == "md-v2" and previous.get("tool_contract_sha256") == policy_id
                        and previous.get("status") == "REQUIRES_OWNER_RESULT_CHECK"):
                    matches.append(previous)
            if not matches:
                raise ValueError("このrun/phaseの新方式で終了したClaude親sessionを確認できません")
        round_dir = folder / str(uuid.uuid4())
        round_dir.mkdir(mode=0o700)
        for view in ("base", "head", "index", "worktree"):
            (round_dir / view).mkdir(mode=0o700)
        before = review.capture(config, round_dir)
        if before != review.capture(config):
            raise ValueError("snapshot取得中にソースが変わりました")
        review.private_write(round_dir / "snapshot.json", json.dumps(before, ensure_ascii=False))
        prompt = (f"Workflow: {config['direction']}\nPhase: {args.phase}\n"
                  f"Review journal: {folder / 'review.md'}\nSnapshot: {round_dir / 'snapshot.json'}\n"
                  f"Contract: {review.ROOT / '.codex/workflows/md-review.md'}\n"
                  f"指定した実担当 {review.LAYERS[args.phase]} に委譲してください。"
                  "契約の適用節と絶対パス、利用者依頼、phaseとsnapshotを担当へ渡してください。"
                  "独立したGit差分はmd_review MCPのgit_diffで全3viewを末尾まで確認してください。"
                  "現在ソースとmode/状態も確認してください。実装サマリーはSuppliedです。"
                  "実担当の結果を変更せず最終応答へ返してください。"
                  "指摘がなければApproveと必須Workflow Resultを返してください。"
                  "必要な質問・証拠待ちもMD用の本文に残してください。"
                  "この1回を終えたら終了し、修正・CI・他AIの待機はしないでください。\n")
        if args.phase == "ci":
            # 自動判定で偽の承認を作らず、実担当がMDの前提証拠を点検します。
            prompt += "選択層の現snapshot承認と実装側local-ciの成功証拠が欠ける場合はBLOCKEDです。PRは作りません。\n"
        if args.resume:
            prompt += "同phaseの元の実childをSendMessageで再開してください。元の実IDが不明ならBLOCKEDです。\n"
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
        changed = before != review.capture(config)
        meta = {"transport": "md-v2", "phase": args.phase, "snapshot_id": before["snapshot_id"], "exit_code": exit_code,
                "source_changed": changed, "resume": args.resume, "artifacts": str(round_dir),
                "failure": failure, "argv": argv, "tool_contract_sha256": policy_id,
                "status": "REQUIRES_OWNER_RESULT_CHECK" if exit_code == 0 and not changed and not failure else "BLOCKED"}
        is_claude = config["direction"] == "codex-claude-review" and args.phase != "ci"
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
        review.private_write(round_dir / "execution.json", json.dumps(meta, ensure_ascii=False, indent=2))
        review.append(folder, f"{args.phase} / {round_dir.name}",
                      "```json\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n\n" + body)
        print(json.dumps(meta, ensure_ascii=False))
        return 0 if meta["status"] == "REQUIRES_OWNER_RESULT_CHECK" else 2


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
