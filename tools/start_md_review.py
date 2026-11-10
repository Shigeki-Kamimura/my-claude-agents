#!/usr/bin/env python3
"""指定した1層だけを一度実行し、終了した応答をMDへ追記します。"""

import argparse
import datetime
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

digest_spec = importlib.util.spec_from_file_location("review_state_digest", Path(__file__).with_name("review_state_digest.py"))
sdigest = importlib.util.module_from_spec(digest_spec)
digest_spec.loader.exec_module(sdigest)
provenance = review.provenance

BACKLOG_READ = ("get_issue", "get_issue_comments", "get_document", "get_document_comments",
                "get_project", "get_wiki", "get_wikis", "get_documents", "get_document_tree")
TOOLS = ["Read", "Glob", "Grep", "Agent", "Task", "SendMessage"]
MD_TOOLS = ("git_diff", "review_context")


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
                "-c", 'mcp_servers.md_review.enabled_tools=' + json.dumps(list(MD_TOOLS)),
                "--output-last-message", str(round_dir / "result.md"), "-"]
    # Backlogの秘密値を引数やrun記録へ複製しません。
    settings = {"env": {"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}, "autoCompactWindow": 200000,
                "hooks": {"PreToolUse": [{"matcher": "", "hooks": [{"type": "command", "command":
                    __import__("shlex").join([sys.executable, "-I", "-B", str(review.ROOT / "tools/md_review_tool_gate.py")])}]}]}}
    backlog = {"command": "bash", "args": ["-lc", 'source "$HOME/.config/backlog-mcp/env" && exec npx -y backlog-mcp-server']}
    allowed = TOOLS + ["ToolSearch"] + ["mcp__md_review__" + n for n in MD_TOOLS] + ["mcp__backlog__" + n for n in BACKLOG_READ]
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


def reading_context(folder, config, phase_state, phase, retained):
    previous = phase_state.get("last_valid")
    count = previous.get("update_count", 0) if previous else 0
    updates = config.get("updates", [])
    if type(count) is not int or not 0 <= count <= len(updates):
        raise ValueError("前回確認後の追記範囲を確定できません")
    sections = {"summary": [config["summary_reference"]], "updates": updates[count:]}
    required = ["current"]
    if not retained:
        required.append("summary")
    if previous:
        sections["previous_result"] = [review.result_reference(folder, previous, phase, config)]
        if not retained:
            required.append("previous_result")
    if sections["updates"]:
        required.append("updates")
    if phase_state.get("latest_reference") and phase_state.get("latest_attempt") != (previous or {}).get("round_id"):
        sections["previous_attempt"] = [phase_state["latest_reference"]]
        required.append("previous_attempt")
    # 間違った参照をモデルへ渡す前に停止します。
    for references in sections.values():
        for reference in references:
            review.journal_read(folder, reference)
    plan = {"tool": "md_review.review_context", "required_sections": required,
            "available_sections": ["current", *sections], "retained_owner_context": retained,
            "update_count": len(updates) - count,
            "pending_item_ids": (previous or {}).get("result", {}).get("open_item_ids", []),
            "history": "必要欄をnext_offset=nullまで読みます。過去履歴の全文は再読しません。失われた根拠、未確認範囲、変更した規則・テストと影響先は追加確認します。"}
    return plan, sections


BRIEFING_PRIORITY = ("previous_result", "updates", "summary")
BRIEFING_IDENTITY = ("workflow_id", "phase", "reviewer", "review_kind", "round_id", "project", "base", "head", "snapshot_id",
                     "previous_snapshot_id", "layers", "rule_source_files", "role_section", "workflow_file", "contract_file",
                     "required_diff_views", "previous_owner", "owner_continuity", "fresh_owner_notice")

FRESH_OWNER_NOTICE = ("新規担当です。前担当の承認・判定は引き継がれません。全ての未解決IDを今回のdeltaと必要な原本で独立に再判定してください。"
                      "review_state_digestがある場合、現shaがmanifestと一致する規則のうち前担当が読んだと記録された範囲は、Supplied根拠として扱えます(自分の承認ではありません)。"
                      "shaが変わった規則、manifestにない節でdeltaが必要とするもの、delta、各未解決IDの再判定に必要な原本はReadしてください。")
# 既定は継続(resume)です。TTL(秒)による新規化は0以下で無効の任意設定、文脈サイズ(token)の上限が既定の新規化条件です。
FRESH_AFTER_SECONDS = 0
FRESH_ABOVE_TOKENS = 150000


def utc_now():
    """テストで差し替え可能な時計です。"""
    return datetime.datetime.now(datetime.timezone.utc)


def owner_finished_at(folder, phase_state):
    """前担当の最後の実行の終了時刻を返します。記録がなければNone（推測しません）。"""
    last = (phase_state.get("last_valid") or {}).get("round_id")
    for round_id in (phase_state.get("latest_attempt"), last):
        if not isinstance(round_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", round_id):
            continue
        try:
            meta = json.loads((folder / round_id / "execution.json").read_text())
            if round_id != last and meta["owner_continuity"]["decision"] == "fresh":
                continue  # 失敗した新規担当の試行は、記録済み担当のcacheを温めていません
            return datetime.datetime.fromisoformat(meta["finished_at"]).astimezone(datetime.timezone.utc)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


def owner_context_tokens(project, owner):
    """前担当の子転記に記録された直近のinput規模。読めなければNone(推測しません)。"""
    try:
        return sdigest.context_tokens(sdigest.child_transcript(receipts, project, owner))
    except (ValueError, OSError):
        return None


def decide_continuity(folder, phase_state, owner, threshold, context_tokens=None, token_cap=0):
    """resume / fresh を決めます。既定はresumeで、記録済みの文脈が上限を超える場合、
    または任意のTTL閾値(秒、正の値のとき)を超える場合だけfreshです。不明な値は推測せずresumeです。"""
    ids = {k: owner[k] for k in ("parent_session_id", "reviewer_id")}
    info = {"mode": "resumed", "decision": "resume", "gap_seconds": None, "threshold_seconds": threshold, "previous_owner": ids,
            "context_tokens": context_tokens, "context_cap_tokens": token_cap}
    if type(token_cap) is int and token_cap > 0 and type(context_tokens) is int and context_tokens > token_cap:
        return {**info, "mode": "fresh_over_context_cap", "decision": "fresh"}
    if not isinstance(threshold, int) or threshold <= 0:
        return {**info, "mode": "resumed_ttl_disabled"}
    finished = owner_finished_at(folder, phase_state)
    gap = (utc_now() - finished).total_seconds() if finished else None
    if gap is None or gap < 0:
        return {**info, "mode": "resumed_gap_unknown"}
    info["gap_seconds"] = round(gap, 3)
    if gap > threshold:
        return {**info, "mode": "fresh_after_ttl", "decision": "fresh"}
    return info


def build_dispatch(folder, request):
    """親が子へ渡す依頼の先頭ブロックをホストが決定的に作ります。判定・根拠は空欄のままです。"""
    if request.get("workflow_id") != "codex-claude-review" or request.get("phase") == "ci":
        return None
    wf = request["workflow_id"]
    skeleton = {"workflow_id": wf, "phase": request["phase"], "reviewer": request["reviewer"],
                "snapshot_id": request.get("snapshot_id") or "<実snapshot_id>",
                "native_verdict": "<子が記入>", "coverage": "<COMPLETE|PARTIAL|BLOCKED のいずれか1語>",
                "decision": "<APPROVE|REQUEST_CHANGES|NEEDS_USER_INPUT|BLOCKED|CONTINUE_REVIEW のいずれか1語>",
                "open_item_ids": [], "questions": [], "handoffs": [],
                "invocation_evidence": {"platform": "Claude Code", "model": "<子が記入>"}}
    lines = [f"Workflow: {wf} / phase {request['phase']} / review_kind {request.get('review_kind')}"
             + (f" / round_id {request['round_id']}" if request.get("round_id") else ""),
             f"Direction: {wf}", f"review.md: {folder / 'review.md'}",
             f"Workflow file: {review.ROOT / '.codex/workflows/claude-review.yml'} (role_section: review_entry.role_sections.{request['phase']})",
             f"Contract: {review.ROOT / '.codex/workflows/md-review.md'}"]
    if request.get("snapshot_id"):
        lines.append(f"snapshot_id: {request['snapshot_id']}")
    lines += ["最終メッセージは日本語レポートの後ろに、次の info-string `workflow-result` のfenced blockをちょうど1つだけ置いて終えてください。",
              "11項目すべてが必須で、値の<...>は子が実際の結果で埋めます。ホストは判定・根拠を事前記入しません。Infoは省略します。",
              "coverageとdecisionは列挙語1語だけです(範囲の説明は日本語レポートへ)。open_item_idsとquestionsは文字列の配列です。",
              'handoffsは各要素が {"id","owner","status"(open|pending|fix_candidate),"weight"(🔴|🟡|🟢),"question","evidence"} のobjectです。',
              "weightは未解決のまま放置した場合の影響の重さです(新規は必須、後から下げられません)。🟡/🔴の未解決handoffが残る間は承認できません。",
              "```workflow-result", json.dumps(skeleton, ensure_ascii=False), "```"]
    body = "\n".join(lines)
    return body, review.digest(body.encode())


def build_briefing(folder, request, plan, sections, cap, digest=None):
    """ホストが保持する原本だけを逐語で並べます。要約・言い換えはしません。
    全文を入れた欄は読取計画のrequired_sectionsから外し、入らない欄はNOT_INLINEDとして残します。"""
    identity = {k: request[k] for k in BRIEFING_IDENTITY if request.get(k) is not None}
    dispatch = build_dispatch(folder, request)
    dispatch_text = f"<<CHILD_DISPATCH sha256={dispatch[1]}>>\n{dispatch[0]}\n<<END CHILD_DISPATCH>>\n\n" if dispatch else ""
    head = ("## Identity\n```json\n" + json.dumps(identity, ensure_ascii=False, indent=2) + "\n```\n\n" + dispatch_text +
            "## Open item IDs\n```json\n" + json.dumps(plan["pending_item_ids"], ensure_ascii=False) + "\n```\n\n"
            "## Handoffs (ledger, verbatim)\n```json\n" + json.dumps(request.get("handoff_index", {}), ensure_ascii=False, indent=2) + "\n```\n")
    if digest:
        head += (f"\n## review_state_digest (host-built from state/MD/prior records; Supplied, not an approval)\n"
                 f"<<REVIEW_STATE_DIGEST sha256={digest[1]}>>\n{digest[0]}\n<<END REVIEW_STATE_DIGEST>>\n")
    used, blocks, inlined, skipped = len(head), [], [], []
    manifest = [("identity+open_ids+handoffs", len(head), "INLINED")]
    for name in BRIEFING_PRIORITY:
        if name not in plan["required_sections"] or name not in sections:
            continue
        text = "\n\n".join(review.journal_read(folder, ref) for ref in sections[name])
        block = f"\n<<SECTION {name} chars={len(text)}>>\n{text}\n<<END SECTION {name}>>\n"
        if used + len(block) <= cap:
            used += len(block)
            blocks.append(block)
            inlined.append(name)
            manifest.append((name, len(text), "INLINED"))
        else:
            skipped.append(name)
            manifest.append((name, len(text), "NOT_INLINED"))
    plan["required_sections"] = [n for n in plan["required_sections"] if n not in inlined]
    plan["inlined_sections"] = inlined
    plan["not_inlined_sections"] = skipped
    lines = [f"- {n}: {c} chars {state}" for n, c, state in manifest]
    text = ("<manifest cap_chars=%d>\n" % cap + "\n".join(lines) + "\n</manifest>\n\n" + head + "".join(blocks))
    return text, {"chars": len(text), "cap_chars": cap, "inlined": inlined, "not_inlined": skipped,
                  "sha256": review.digest(text.encode()),
                  **({"review_state_digest_sha256": digest[1], "review_state_digest_chars": len(digest[0])} if digest else {}),
                  "child_dispatch_sha256": dispatch[1] if dispatch else None, "child_dispatch_chars": len(dispatch[0]) if dispatch else 0}


def make_digest(folder, config, previous, predecessor, snapshot, changed, rule_changes, handoffs):
    """新規担当用のreview_state_digestです。前回の確認済みsnapshotと実記録だけを使い、モデルを起動しません。"""
    old = json.loads((folder / previous["round_id"] / "snapshot.json").read_text())
    reads = sdigest.read_requests(sdigest.child_transcript(receipts, config["project"], predecessor))
    return sdigest.build(config["project"], old, snapshot["rules"], snapshot["snapshot_id"], changed, rule_changes, reads,
                         predecessor, previous.get("journal_reference"), previous["result"]["open_item_ids"], handoffs)


def print_briefing(args):
    """読取専用です。何も書かず、モデルも起動しません。"""
    folder, config = review.load_run(args.run_dir)
    if args.phase != "ci" and args.phase not in config["layers"]:
        raise ValueError("利用者が選んでいない層です")
    if "summary_reference" not in config:
        raise ValueError("run.jsonに共通MDの索引がありません。通常起動で索引を作成してから実行してください")
    state_file = folder / "state.json"
    if state_file.is_symlink():
        raise ValueError("状態ファイルにsymlinkは使用できません")
    state = json.loads(state_file.read_text()) if state_file.exists() else {"version": 3, "phases": {}}
    if not isinstance(state, dict) or state.get("version") != 3 or not isinstance(state.get("phases"), dict):
        raise ValueError("状態ファイルの形式が未対応です")
    phase_state = state["phases"].get(args.phase, {})
    previous = phase_state.get("last_valid")
    owner = phase_state.get("owner") or previous
    is_claude = config["direction"] == "codex-claude-review" and args.phase != "ci"
    rereview = previous is not None and previous["result"]["coverage"] == "COMPLETE"
    request = {"workflow_id": config["direction"], "phase": receipts.PHASES[args.phase], "reviewer": review.LAYERS[args.phase],
               "review_kind": "rereview" if rereview else "continuation" if previous or owner else "initial",
               "project": config["project"], "base": config["base"], "layers": config["layers"],
               "previous_snapshot_id": phase_state.get("snapshot_id"), "rule_source_files": config["rules"],
               "required_diff_views": ["delta"] if rereview else ["branch", "staged", "unstaged"],
               "previous_owner": {k: owner[k] for k in ("parent_session_id", "reviewer_id")} if owner else None,
               "handoff_index": state.get("handoffs", {})}
    continuity = (decide_continuity(folder, phase_state, owner, getattr(args, "fresh_after_seconds", FRESH_AFTER_SECONDS),
                                    owner_context_tokens(config["project"], owner), getattr(args, "fresh_above_tokens", FRESH_ABOVE_TOKENS))
                  if is_claude and owner else None)
    fresh = bool(continuity and continuity["decision"] == "fresh")
    if continuity:
        request["owner_continuity"] = continuity
    if fresh:
        request["fresh_owner_notice"] = FRESH_OWNER_NOTICE
    plan, sections = reading_context(folder, config, phase_state, args.phase, bool(is_claude and owner and not fresh))
    digest = None
    if fresh and rereview:
        old = json.loads((folder / previous["round_id"] / "snapshot.json").read_text())
        current = review.capture(config)
        changed, rule_changes = sdigest.snapshot_delta(old, current)
        digest = make_digest(folder, config, previous, continuity["previous_owner"], current, changed, rule_changes, state.get("handoffs", {}))
    text, report = build_briefing(folder, request, plan, sections, args.briefing_max_chars, digest)
    report["review_md_chars"] = len(review.journal_body(folder))
    report["owner_continuity"] = continuity
    report["required_sections_after"] = plan["required_sections"]
    print(text)
    print("---\n" + json.dumps(report, ensure_ascii=False))
    return 0


def child_final_text(project, native, child, provider, child_offset=0):
    """実子の最終応答を、書換えずに原本から取り出します。"""
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
        return texts[-1] if texts else ""
    return native["completed"].get(child, "")


def child_result_matches(project, native, checked, provider, child_offset=0):
    child = checked["reviewer_id"]
    body = child_final_text(project, native, child, provider, child_offset)
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


def preflight_owner(project, phase, state, owner, previous, policy_id, resume):
    """resume前にstate.jsonだけで親子・phase・tool契約を確認します。モデルは起動しません。"""
    for key in ("parent_session_id", "reviewer_id"):
        if not isinstance(owner.get(key), str) or not re.fullmatch(r"[A-Za-z0-9_-]+", owner[key]):
            raise ValueError("記録済みの親子IDが不正です")
    if owner["tool_contract_sha256"] != policy_id or resume and resume != owner["parent_session_id"]:
        raise ValueError("元の親子またはtool契約を確認できません")
    if previous and any(previous.get(k) not in (None, owner[k]) for k in ("parent_session_id", "reviewer_id")):
        raise ValueError("phase担当の記録が前回の検証済み結果と一致しません")
    for other, entry in state["phases"].items():
        theirs = entry.get("owner") if isinstance(entry, dict) else None
        if other != phase and theirs and theirs.get("reviewer_id") == owner["reviewer_id"]:
            raise ValueError(f"記録済みの担当が別phase({other})の担当と重複しています。別sessionの子は再開できません")
    transcript = receipts.claude_transcript(project, owner["parent_session_id"])
    child = transcript.with_suffix("") / "subagents" / ("agent-" + owner["reviewer_id"] + ".jsonl")
    if not transcript.is_file() or transcript.is_symlink() or not child.is_file() or child.is_symlink():
        raise ValueError("記録済みの子が記録済みの親sessionに属することを原本で確認できません")


def rate_limit_signal(round_dir, exit_code):
    """Claudeの終了が利用上限によるかを、失敗した終了の最終resultと標準エラー末尾だけから判定します。
    正常終了した回(判定欄がない親の言い換えを含む)は対象にしません(child_verbatimで回復でき、上限を扱うPRの本文での誤検出も避けます)。"""
    final, status, is_error = "", None, False
    try:
        with (round_dir / "stdout.jsonl").open() as records:
            for line in records:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict) and record.get("type") == "result":
                    final = record.get("result") if isinstance(record.get("result"), str) else ""
                    status, is_error = record.get("api_error_status"), bool(record.get("is_error"))
    except OSError:
        pass
    try:
        data = (round_dir / "stderr.log").read_bytes()[-4000:].decode("utf-8", "replace")
    except OSError:
        data = ""
    # 親の言い換えで判定欄がない場合は、実子原本の採用(child_verbatim)で回復できるため、上限とは扱いません。
    failed = bool(exit_code != 0 or is_error or not final)
    return provenance.detect_rate_limit(final, status, data, failed)


def finish_rate_limited(folder, state, request, meta, limit, phase, round_dir):
    """利用上限に達したroundを記録して終了します。再試行も追加の子の起動もしません。"""
    hint = limit["reset_hint"]
    meta.update({"status": "RATE_LIMITED", "failure": "rate_limited", "reset_hint": hint, "rate_limit_signal": limit["signal"]})
    body = ("Claudeの利用上限に達したため、このroundは未完了です(再試行しません)。作業は保存済みで再開できます。\n"
            f"検出: {limit['signal']}\nリセット: {hint or '出力から特定できません'}")
    review.private_write(round_dir / "result.md", body)
    review.private_write(round_dir / "execution.json", json.dumps(meta, ensure_ascii=False, indent=2))
    reference = review.append(folder, f"{phase} / {round_dir.name}",
                              "```json\n" + json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False, indent=2) + "\n```\n\n" + body)
    state["phases"][phase].update({"status": "RATE_LIMITED", "latest_reference": reference})
    state["rate_limit"] = {"phase": phase, "round_id": round_dir.name, "reset_hint": hint, "detected_at": utc_now().isoformat()}
    save_state(folder, state)
    request["phase_index"] = {p: {k: v.get(k) for k in ("status", "snapshot_id", "latest_attempt")} for p, v in state["phases"].items()}
    request["handoff_index"] = state["handoffs"]
    request["execution_result_file"] = str(round_dir / "execution.json")
    review.current_request(folder, request)
    print(json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False))
    print(f"RATE_LIMITED: Claudeの利用上限に達しました。作業は保存済みで再開できます。リセット: {hint or '出力から特定できません'}。"
          "自動の再試行はしません。リセット後に利用者が確認し、--after-rate-limit-ackを付けて再実行してください", file=sys.stderr)
    return 3


def run(args):
    if args.print_briefing:
        return print_briefing(args)
    folder, config = review.load_run(args.run_dir)
    if args.phase != "ci" and args.phase not in config["layers"]:
        raise ValueError("利用者が選んでいない層は起動できません")
    # lockはホストだけが待ちます。AIの待機・ポーリングはありません。
    lock = os.open(folder / ".lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock, "w") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scope = review.check_scope(config)
        review.journal_index(folder, config)
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
        cost = None
        if is_claude:
            # 利用量ガード: 拒否はround作成やPENDING書込みより前に行い、何も残しません。
            if state.get("rate_limit"):
                if not args.after_rate_limit_ack:
                    raise ValueError("直前のroundがClaudeの利用上限に達しています(リセット: "
                                     + str(state["rate_limit"].get("reset_hint") or "出力から特定できません")
                                     + ")。作業は保存済みで再開できます。リセット後、利用者が確認して--after-rate-limit-ackを付けた場合だけ再開します")
                state.setdefault("rate_limit_acks", []).append({**state.pop("rate_limit"), "acknowledged_at": utc_now().isoformat()})
            cost = provenance.estimate_cost_class(config["layers"], len(scope["changed_paths"]))
            if config.get("claude_usage") == "unknown":
                started = sorted(p for p, entry in state["phases"].items() if p != args.phase and isinstance(entry, dict) and entry.get("latest_attempt"))
                print(f"claude_usage: unknown。推定コスト区分={cost}(層={len(config['layers'])}, 変更path={len(scope['changed_paths'])}"
                      + (", adv含む" if "adv" in config["layers"] else "") + ")。測定値ではありません", file=sys.stderr)
                if started and not args.confirm_more_layers:
                    raise ValueError(f"利用量が未入力のため、起動済みの層({', '.join(started)})の後に別の層は起動しません。"
                                     "利用者が追加の層を確認した場合だけ--confirm-more-layersを付けてください")
        continuity, fresh, active_owner = None, False, owner
        if owner and is_claude:
            preflight_owner(config["project"], args.phase, state, owner, previous, policy_id, args.resume)
            args.resume = owner["parent_session_id"]
            continuity = decide_continuity(folder, phase_state, owner, args.fresh_after_seconds,
                                           owner_context_tokens(config["project"], owner), args.fresh_above_tokens)
            if continuity["decision"] == "fresh":
                # 記録済みの文脈が上限を超える(または任意のTTLを超えた)ため新規担当で始めます（承認は引き継ぎません）。
                fresh, active_owner, args.resume = True, None, None
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
        if continuity:
            request["owner_continuity"] = continuity
        if fresh:
            request["fresh_owner_notice"] = FRESH_OWNER_NOTICE
        request["project"] = config["project"]
        request["base"] = config["base"]
        request["reading_plan"], sections = reading_context(folder, config, phase_state, args.phase, bool(is_claude and args.resume))
        request["reading_plan"]["required_diff_views"] = request["required_diff_views"]
        request["head"] = before["head"]
        request["snapshot_id"] = before["snapshot_id"]
        digest = None
        if fresh and rereview:
            digest = make_digest(folder, config, previous, continuity["previous_owner"], before,
                                 comparison["changed_paths"], comparison["rule_changes"], state["handoffs"])
            # 実際のreviewer(子)はreview_context("current")だけを読めるため、digest本体もここへ置きます。
            request["review_state_digest"] = {"sha256": digest[1], "chars": len(digest[0]), "digest": json.loads(digest[0])}
        briefing, briefing_report = build_briefing(folder, request, request["reading_plan"], sections, args.briefing_max_chars, digest)
        del request["head"], request["snapshot_id"]
        request["reading_plan"]["briefing_sha256"] = briefing_report["sha256"]
        review.private_write(round_dir / "briefing.md", briefing)
        review.private_write(round_dir / "context.json", json.dumps({"request": request, "sections": sections, "briefing": briefing_report}, ensure_ascii=False))
        review.current_request(folder, request)
        prompt = (f"{folder / 'review.md'} を基に{'再レビュー' if previous or owner else 'レビュー'}してください。\n"
                  f"<<BRIEFING sha256={briefing_report['sha256']}>>\n{briefing}<<END BRIEFING>>\n"
                  + ("\n親への固定指示: 担当の子を起動するときは、briefing内の<<CHILD_DISPATCH ...>>から<<END CHILD_DISPATCH>>までのブロックを、"
                     "一字も変えず子のpromptの先頭へそのまま置いてください。要約・書換え・追記で置き換えず、子の最終メッセージも変えずに返してください。\n"
                     if briefing_report["child_dispatch_sha256"] else ""))
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
        if fresh:
            history = [*phase_state.get("previous_owners", []), continuity["previous_owner"]]
            state["phases"][args.phase].update({"previous_owner": continuity["previous_owner"], "previous_owners": history})
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
                "failure": failure, **({"cost_class": cost} if cost else {}), "argv": argv, "finished_at": utc_now().isoformat(), "owner_continuity": continuity, "tool_contract_sha256": policy_id, "briefing": briefing_report,
                "status": "PENDING_RESULT_VALIDATION" if exit_code == 0 and not changed and not failure else "BLOCKED"}
        if is_claude:
            limit = rate_limit_signal(round_dir, exit_code)
            if limit:
                return finish_rate_limited(folder, state, request, meta, limit, args.phase, round_dir)
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
            native = receipts.identities(rows, "claude" if is_claude else "codex", review.LAYERS[args.phase], active_owner)
            meta["parent_session_id"] = native["parent_session_id"]
            candidates = [child for child, role in native["children"].items() if role == review.LAYERS[args.phase]]
            if len(candidates) == 1 and re.fullmatch(r"[A-Za-z0-9_-]+", candidates[0]) and not fresh:
                state["phases"][args.phase]["owner"] = {"parent_session_id": native["parent_session_id"],
                    "reviewer_id": candidates[0], "tool_contract_sha256": policy_id, "result": {"open_item_ids": []}}
            if meta["status"] == "BLOCKED":
                raise ValueError("CLI失敗、原本欠落またはsource変更です")
            provider = "claude" if is_claude else "codex"

            def accept(text):
                result = receipts.workflow_result(text)
                bind_reviewer(config["project"], native, result, provider, review.LAYERS[args.phase], child_offset, active_owner)
                checked = receipts.validate(result, {**config, "reviewer": review.LAYERS[args.phase]}, args.phase,
                                            before["snapshot_id"], native, previous or owner, state["handoffs"], fresh)
                return checked, receipts.update_handoffs(state["handoffs"], result, checked["reviewer_id"], round_dir.name)

            meta["result_source"] = "parent"
            try:
                checked, handoffs = accept(body)
            except (ValueError, KeyError, TypeError, OSError) as parent_error:
                if not is_claude:
                    raise
                # 親の言い換えは信用せず、実子の最終応答をそのまま採用できるか検証します。
                role = review.LAYERS[args.phase]
                ids = [active_owner["reviewer_id"]] if active_owner and active_owner["reviewer_id"] in native["children"] else \
                    [c for c, r in native["children"].items() if r == role] if not active_owner else []
                try:
                    if len(ids) != 1:
                        raise ValueError("実子を1人に確定できません")
                    verbatim = child_final_text(config["project"], native, ids[0], provider, child_offset if active_owner else 0)
                    checked, handoffs = accept(verbatim)
                except (ValueError, KeyError, TypeError, OSError) as child_error:
                    raise ValueError(f"{parent_error}（実子原本の採用も不可: {child_error}）") from None
                os.replace(result_path, round_dir / "parent-result.md")
                review.private_write(result_path, verbatim)
                body, meta["result_source"] = verbatim, "child_verbatim"
            state["handoffs"] = handoffs
            meta.update({k: checked[k] for k in ("parent_session_id", "reviewer_id", "approved")})
            meta.update(provenance.independence_record(config, checked["result"]["invocation_evidence"]))
            meta["status"] = "APPROVED" if checked["approved"] else "REVIEWED"
            if fresh:
                continuity["new_owner"] = {"parent_session_id": checked["parent_session_id"], "reviewer_id": checked["reviewer_id"]}
            state["phases"][args.phase] = {"status": meta["status"], "snapshot_id": before["snapshot_id"],
                "latest_attempt": round_dir.name,
                **{k: phase_state[k] for k in ("previous_owner", "previous_owners") if k in phase_state},
                **({"previous_owner": continuity["previous_owner"], "previous_owners": state["phases"][args.phase]["previous_owners"],
                    "owner_continuity": continuity["mode"]} if fresh else {}),
                "owner": {"parent_session_id": checked["parent_session_id"], "reviewer_id": checked["reviewer_id"],
                          "tool_contract_sha256": policy_id, "result": {"open_item_ids": []}},
                    "last_valid": {**checked, "round_id": round_dir.name, "tool_contract_sha256": policy_id,
                                   "update_count": len(config.get("updates", []))}}
        except (ValueError, KeyError, TypeError, OSError) as error:
            meta["status"] = "BLOCKED"
            meta["validation_error"] = str(error)
            state["phases"][args.phase]["status"] = "BLOCKED"
        review.private_write(round_dir / "execution.json", json.dumps(meta, ensure_ascii=False, indent=2))
        reference = review.append(folder, f"{args.phase} / {round_dir.name}",
                      "```json\n" + json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False, indent=2) + "\n```\n\n" + body)
        state["phases"][args.phase]["latest_reference"] = reference
        if meta["status"] in ("APPROVED", "REVIEWED"):
            state["phases"][args.phase]["last_valid"]["journal_reference"] = reference
        save_state(folder, state)
        request["phase_index"] = {p: {k: v.get(k) for k in ("status", "snapshot_id", "latest_attempt")} for p, v in state["phases"].items()}
        request["handoff_index"] = state["handoffs"]
        request["execution_result_file"] = str(round_dir / "execution.json")
        request["current_owner"] = {k: state["phases"][args.phase]["owner"][k] for k in ("parent_session_id", "reviewer_id")} if state["phases"][args.phase].get("owner") else None
        review.current_request(folder, request)
        print(json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False))
        return 0 if meta["status"] in ("APPROVED", "REVIEWED") else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=tuple(review.LAYERS), required=True)
    parser.add_argument("--resume", help="同phaseの検証済みClaude親session IDだけです")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--fresh-after-seconds", type=int, default=FRESH_AFTER_SECONDS,
                        help="任意設定: 同phaseの前回終了からこの秒数を超えたら、resumeせず新規Claude担当で始めます。既定0(無効=継続優先)")
    parser.add_argument("--fresh-above-tokens", type=int, default=FRESH_ABOVE_TOKENS,
                        help="前担当の子転記に記録された直近のinput規模(token)がこの値を超えたら新規担当で始めます。0以下で無効。目安であり測定値ではありません")
    parser.add_argument("--after-rate-limit-ack", action="store_true",
                        help="直前の利用上限(RATE_LIMITED)を利用者が確認した後の再実行に必要です。自動再試行はありません")
    parser.add_argument("--confirm-more-layers", action="store_true",
                        help="claude_usageが未入力のrunで、最初の層の後に別の層を起動することを利用者が確認した場合だけ指定します")
    parser.add_argument("--briefing-max-chars", type=int, default=60000, help="依頼文へ逐語で入れる本文の上限文字数")
    parser.add_argument("--print-briefing", action="store_true", help="briefingと大きさだけを標準出力へ出します。書込みもモデル起動もしません")
    args = parser.parse_args()
    try:
        return run(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
