"""実行元のIDと、MD内のレビュー判定を照合します。"""

import json
from pathlib import Path
import re

FIELDS = {"workflow_id", "phase", "reviewer", "snapshot_id", "native_verdict", "coverage", "decision",
          "open_item_ids", "questions", "handoffs", "invocation_evidence"}
PHASES = {"cr": "l1_5", "adv": "l2", "qa": "qa", "e2e": "e2e", "ci": "ci"}
CLOSED = {"reviewer_confirmed_fixed", "reviewer_withdrawn"}
# handoffの重み(HND-1)。語彙は.codex/workflows/*.ymlのfindings.severity(🔴重・🟡中・🟢Low)と同じ3値です。
# 既存の3ツールに重みの正規化処理はなかったため、別名は設けず、先頭の絵文字だけで判定します(例: "🟡中" は "🟡")。
WEIGHT_RANK = {"🟢": 0, "🟡": 1, "🔴": 2}
# 重みを持たない旧台帳のhandoffは読めるまま保ち、実効値を中間の🟡として扱います(保守側)。
# 台帳へ書き戻さず、判定時に計算するだけです。ownerが重みを明示するまで単層承認を止めます。
LEGACY_WEIGHT = "🟡"


def canonical_owner(owner):
    return {"qa": "test-qa", "e2e": "e2e-qa", "cr": "code-quality-reviewer", "adv": "adviser",
            "l1_5": "code-quality-reviewer", "l2": "adviser", "ci": "ci-reviewer"}.get(owner, owner)


def handoff_rows(result):
    found = {}
    for item in result.get("handoffs", []):
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip()
                or not isinstance(item.get("owner"), str) or not item["owner"].strip()
                or item.get("status") not in CLOSED | {"open", "pending", "fix_candidate"}
                or item["id"] in found):
            raise ValueError("handoffのID/owner/statusが欠落、不正または重複しています")
        found[item["id"]] = item
    return found


def normalize_weight(value):
    """重みを🔴/🟡/🟢のいずれかへ正規化します。不正な値はNoneです。"""
    if isinstance(value, str) and value.strip()[:1] in WEIGHT_RANK:
        return value.strip()[:1]
    return None


def effective_weight(item, known=None):
    """重みの実効値です。現在の結果、台帳、旧台帳の既定値の順に採ります。"""
    return (normalize_weight(item.get("weight")) if isinstance(item, dict) else None) or \
        normalize_weight((known or {}).get("weight")) or LEGACY_WEIGHT


def check_weight(item, known):
    """新規handoffには有効な重みが必須です。未解決の既存行の重みは下げられません(上げるのは許可)。
    重みを下げる唯一の道は、実ownerがclosure_evidence付きで解消・撤回することです。"""
    if "weight" in item and normalize_weight(item["weight"]) is None:
        raise ValueError("handoffのweightは🔴/🟡/🟢のいずれかが必要です: " + item["id"])
    if known is None:
        if normalize_weight(item.get("weight")) is None:
            raise ValueError("新規handoffには重み(weight: 🔴/🟡/🟢)が必要です: " + item["id"])
        return
    if item["status"] not in CLOSED and normalize_weight(item.get("weight")) is not None \
            and WEIGHT_RANK[normalize_weight(item["weight"])] < WEIGHT_RANK[effective_weight({}, known)]:
        raise ValueError("未解決handoffの重みは下げられません(実ownerの解消・撤回証拠で閉じてください): " + item["id"])


def update_handoffs(ledger, result, reviewer_id, round_id):
    """元の問いを保ち、実ownerの根拠付き結果だけで閉じます。"""
    updated = {key: dict(value) for key, value in ledger.items()}
    for key, item in handoff_rows(result).items():
        owner = canonical_owner(item["owner"])
        known = updated.get(key)
        if known and known["owner"] != owner:
            raise ValueError("handoffのownerを変更できません: " + key)
        if known and any(item.get(field) not in (None, known[field]) for field in ("question", "evidence")):
            raise ValueError("元のhandoffの問い・根拠は保持してください: " + key)
        check_weight(item, known)
        if known is None:
            if (item["status"] in CLOSED or not isinstance(item.get("question"), str) or not item["question"].strip()
                    or not isinstance(item.get("evidence"), str) or not item["evidence"].strip()):
                raise ValueError("新規handoffには未解決の問いと根拠が必要です: " + key)
            known = {**item, "owner": owner, "weight": normalize_weight(item["weight"]),
                     "origin_reviewer": result["reviewer"], "origin_round": round_id}
        if item["status"] in CLOSED:
            if known["status"] not in CLOSED:
                if owner != result["reviewer"] or not isinstance(item.get("closure_evidence"), str) or not item["closure_evidence"].strip():
                    raise ValueError("handoffの実ownerによる解消・撤回証拠が必要です: " + key)
                known = {**known, "status": item["status"], "closure": {"owner": owner, "reviewer_id": reviewer_id,
                    "round_id": round_id, "snapshot_id": result["snapshot_id"], "evidence": item["closure_evidence"]}}
        elif known["status"] in CLOSED:
            if item.get("reopen_evidence"):
                known = {**known, "status": item["status"], "reopen_evidence": item["reopen_evidence"], "reopen_round": round_id}
            else:
                raise ValueError("解消済みhandoffの再開には新たな根拠が必要です: " + key)
        else:
            known = {**known, "status": item["status"]}
        if item["status"] not in CLOSED and normalize_weight(item.get("weight")):
            known = {**known, "weight": normalize_weight(item["weight"])}
        updated[key] = known
    return updated


def semantic_result(result):
    value = {**result, "invocation_evidence": dict(result["invocation_evidence"])}
    for key in ("parent_session_id", "reviewer_id"):
        value["invocation_evidence"].pop(key, None)
    return value


def workflow_result(body):
    blocks = re.findall(r"(?m)^```workflow-result\s*\n(.*?)\n```\s*$", body, re.S)
    if len(blocks) != 1:
        raise ValueError("workflow-resultのJSON欄は1つ必要です")
    def unique_fields(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("判定欄のkeyが重複しています: " + key)
            value[key] = item
        return value
    result = json.loads(blocks[0], object_pairs_hook=unique_fields)
    if not isinstance(result, dict) or set(result) != FIELDS:
        raise ValueError("Workflow Resultの11項目が一致しません")
    return result


def records(path, offset=0):
    if not path.is_file() or path.is_symlink():
        return []
    with path.open() as stream:
        stream.seek(offset)
        return [json.loads(line) for line in stream if line.strip()]


def claude_transcript(project, parent_id):
    if not isinstance(parent_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", parent_id):
        raise ValueError("親session IDが不正です")
    import os
    root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    return root / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project)) / (parent_id + ".jsonl")


def identities(rows, provider, expected_role, previous=None):
    parents, children, completed = set(), {}, {}
    calls = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("実行記録の形式が不正です")
        if row.get("type") == "turn.failed":
            raise ValueError("Codexのturnが失敗しています")
        if provider == "claude":
            if row.get("type") == "result" and isinstance(row.get("session_id"), str):
                parents.add(row["session_id"])
            message = row.get("message", {})
            content = message.get("content", []) if isinstance(message, dict) else []
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task", "SendMessage"):
                    calls[block.get("id")] = (block["name"], block.get("input", {}))
                if block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                    tool, inputs = calls[block["tool_use_id"]]
                    native = row.get("toolUseResult", row.get("tool_use_result", {}))
                    if not isinstance(native, dict) or block.get("is_error"):
                        continue
                    if tool in ("Agent", "Task") and isinstance(native.get("agentId"), str) and not inputs.get("resume"):
                        children[native["agentId"]] = inputs.get("subagent_type")
                    if tool == "SendMessage" and previous and native.get("success") is True:
                        resumed = native.get("resumedAgentId")
                        if resumed == previous.get("reviewer_id"):
                            children[resumed] = expected_role
        else:
            if row.get("type") == "thread.started" and isinstance(row.get("thread_id"), str):
                parents.add(row["thread_id"])
            item = row.get("item", {})
            if not isinstance(item, dict) or item.get("type") != "collab_tool_call":
                continue
            if item.get("tool") == "spawn_agent" and item.get("status") == "completed":
                for child in item.get("receiver_thread_ids", []):
                    if isinstance(child, str):
                        children[child] = item.get("agent_type")
            for child, state in item.get("agents_states", {}).items():
                if isinstance(state, dict) and state.get("status") == "completed" and isinstance(state.get("message"), str):
                    completed[child] = state["message"]
                else:
                    completed.pop(child, None)
    if len(parents) != 1:
        raise ValueError("今回の親IDを実行記録から確定できません")
    return {"parent_session_id": next(iter(parents)), "children": children, "completed": completed}


def validate(result, config, phase, snapshot_id, native, previous=None, handoff_ledger=None, fresh_owner=False):
    expected = {"workflow_id": config["direction"], "phase": PHASES[phase],
                "reviewer": config["reviewer"], "snapshot_id": snapshot_id}
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError("workflow/phase/reviewer/snapshotが今回の依頼と一致しません")
    if result["coverage"] not in ("COMPLETE", "PARTIAL", "BLOCKED"):
        raise ValueError("coverageが不正です")
    if result["decision"] not in ("APPROVE", "REQUEST_CHANGES", "NEEDS_USER_INPUT", "BLOCKED", "CONTINUE_REVIEW"):
        raise ValueError("decisionが不正です")
    if not isinstance(result["native_verdict"], str):
        raise ValueError("native_verdictは文字列が必要です")
    for field in ("open_item_ids", "questions", "handoffs"):
        if not isinstance(result[field], list):
            raise ValueError(field + "は配列が必要です")
    if any(not isinstance(value, str) or not value for value in result["open_item_ids"]):
        raise ValueError("指摘IDが不正です")
    current_handoffs = handoff_rows(result)
    # HND-1: 新規handoffの重み必須と、未解決行の重み引下げ禁止を、承認判定の前に確認します。
    known_rows = {**(handoff_rows(previous["result"]) if previous else {}), **(handoff_ledger or {})}
    for key, handoff in current_handoffs.items():
        check_weight(handoff, known_rows.get(key))
    evidence = result["invocation_evidence"]
    if not isinstance(evidence, dict):
        raise ValueError("invocation_evidenceはobjectが必要です")
    child = evidence.get("reviewer_id") or native.get("reviewer_id")
    if (evidence.get("parent_session_id") not in (None, native["parent_session_id"]) or not isinstance(child, str)
            or native.get("reviewer_id") not in (None, child)
            or not re.fullmatch(r"[A-Za-z0-9_-]+", child)
            or child not in native["children"] or native["children"][child] not in (None, config["reviewer"])):
        raise ValueError("親子IDまたは実担当が実行記録と一致しません")
    if previous and not fresh_owner and config["direction"] == "codex-claude-review" and phase != "ci":
        if native["parent_session_id"] != previous["parent_session_id"] or child != previous["reviewer_id"]:
            raise ValueError("元のClaude親子を再開していません")
    for field in ("platform", "model"):
        if not isinstance(evidence.get(field), str) or not evidence[field]:
            raise ValueError(field + "の実行証拠が必要です")
    if evidence["platform"] != ("Claude Code" if config["direction"] == "codex-claude-review" and phase != "ci" else "Codex"):
        raise ValueError("reviewerのplatformが一致しません")
    if previous:
        dropped = set(previous["result"]["open_item_ids"]) - set(result["open_item_ids"])
        updates = evidence.get("finding_updates", {})
        for finding in dropped:
            update = updates.get(finding) if isinstance(updates, dict) else None
            if (not isinstance(update, dict) or update.get("status") not in ("reviewer_confirmed_fixed", "reviewer_withdrawn")
                    or not isinstance(update.get("evidence"), str) or not update["evidence"].strip()):
                raise ValueError("前回IDの解消・撤回証拠がありません: " + finding)
        for key, handoff in handoff_rows(previous["result"]).items():
            if key in current_handoffs and canonical_owner(current_handoffs[key]["owner"]) != canonical_owner(handoff["owner"]):
                raise ValueError("前回handoffのownerを変更できません: " + key)
            if key not in current_handoffs and handoff.get("status") not in CLOSED:
                known = (handoff_ledger or {}).get(key, {})
                if known.get("status") not in CLOSED or canonical_owner(handoff["owner"]) != known.get("owner"):
                    raise ValueError("未解決handoffが判定欄から消えています: " + key)
    if result["decision"] == "APPROVE":
        if result["coverage"] != "COMPLETE" or result["open_item_ids"] or result["questions"]:
            raise ValueError("未確認・指摘・質問があるため承認できません")
        accepted = {"L1.5_APPROVE", "L1.5_APPROVE_WITH_NOTES"} if phase == "cr" else {"CODEX VERDICT: LGTM"} if phase == "ci" else {"APPROVE"}
        if result["native_verdict"] not in accepted:
            raise ValueError("native判定が承認条件を満たしません")
        for handoff in result["handoffs"]:
            if handoff.get("status") not in CLOSED:
                # HND-1: 🟡/🔴の未解決handoffは、depends_on_for_approval=falseでも承認を止めます。
                # 現在の結果と台帳のうち重い方を採り、重みがどこにもない旧行は🟡扱いです。
                known = known_rows.get(handoff["id"], {})
                ranks = [WEIGHT_RANK[w] for w in (normalize_weight(handoff.get("weight")), normalize_weight(known.get("weight"))) if w]
                if max(ranks or [WEIGHT_RANK[LEGACY_WEIGHT]]) >= WEIGHT_RANK["🟡"]:
                    raise ValueError("🟡/🔴の未解決handoffがあるため承認できません: " + handoff["id"])
            if not isinstance(handoff, dict) or handoff.get("status") not in ("reviewer_confirmed_fixed", "reviewer_withdrawn"):
                if phase == "ci" or not isinstance(handoff, dict) or handoff.get("depends_on_for_approval") is not False:
                    raise ValueError("判断に必要なhandoffが未解消です")
    return {"parent_session_id": native["parent_session_id"], "reviewer_id": child, "result": result,
            "approved": result["decision"] == "APPROVE"}
