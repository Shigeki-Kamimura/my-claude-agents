"""実装・並列CR・QA/E2Eの遷移を判定します。モデルやGitは呼びません。"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = 1
WORKFLOW = "implementation-pcr-loop"
BACKENDS = {"codex", "claude"}
ROLES = {
    "hq": "hq-coder", "pl": "req-pl", "cr_a": "code-quality-reviewer",
    "cr_b": "code-quality-reviewer", "validator": "code-quality-reviewer",
    "qa": "test-qa", "e2e": "e2e-qa", "l2": "adviser",
}
REVIEW_SLOTS = {"cr_a", "cr_b", "validator", "qa", "e2e", "l2"}
QA_CHECKS = {"happy_path", "fail_path", "missing_tests", "excess_tests", "assertions", "fixtures_mocks"}
TERMINAL = {"READY_FOR_USER", "NEEDS_USER_INPUT", "BLOCKED", "RATE_LIMITED"}
CLOSED = {"reviewer_confirmed_fixed", "reviewer_withdrawn"}


class ContractError(ValueError):
    """判断に必要な入力が不足、不一致です。"""


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ContractError(message)


def identity(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class Policy:
    implementation_backend: str
    pcr_backend: str
    qa_backend: str
    e2e_backend: str
    l2_backend: str | None = None
    max_fix_rounds: int = 3
    max_owner_rounds: int = 1
    cross_model_required: tuple[str, ...] = ("l2",)
    publish: bool = False

    def validate(self) -> None:
        for name in ("implementation_backend", "pcr_backend", "qa_backend", "e2e_backend"):
            require(getattr(self, name) in BACKENDS, f"{name}が未対応です")
        require(self.l2_backend in BACKENDS | {None}, "l2_backendが未対応です")
        require(type(self.publish) is bool and self.publish is False, "このフローは公開操作を許可しません")
        require(type(self.max_fix_rounds) is int and 1 <= self.max_fix_rounds <= 3, "修正上限は1〜3回です")
        require(type(self.max_owner_rounds) is int and self.max_owner_rounds == 1, "限定確認は各段階1回です")
        require(set(self.cross_model_required) <= {"qa", "e2e", "l2"}, "別モデル必須の指定が不正です")
        for layer in self.cross_model_required:
            provider = getattr(self, layer + "_backend")
            if provider is not None:
                require(provider != self.implementation_backend, layer + "は実装者と別系統が必須です")

    def provider(self, slot: str) -> str:
        if slot in {"hq", "pl"}:
            return self.implementation_backend
        if slot in {"cr_a", "cr_b", "validator"}:
            return self.pcr_backend
        value = getattr(self, slot + "_backend")
        require(value in BACKENDS, "未選択の担当です: " + slot)
        return value


def new_state(policy: Policy, snapshot_id: str, rules_id: str, request: str) -> dict:
    policy.validate()
    require(all(map(text, (snapshot_id, rules_id, request))), "対象版・規約版・依頼が必要です")
    state = {
        "schema_version": SCHEMA_VERSION, "workflow_id": WORKFLOW, "policy": asdict(policy),
        "snapshot_id": snapshot_id, "rules_id": rules_id, "request": request,
        "status": "RUNNING", "stage": "hq", "epoch": 0, "fix_rounds": 0,
        "sequence": 0, "jobs": {}, "reports": {}, "owners": {}, "owner_parents": {}, "owner_transports": {}, "ledger": {},
        "history": [], "owner_rounds": {}, "questions": [], "answers": [],
        "reconcile": [], "archive_status": "PENDING", "stop_reason": None,
    }
    queue(state, ["hq"], "implement")
    return state


def policy_of(state: dict) -> Policy:
    p = Policy(**state["policy"])
    p.validate()
    return p


def queue(state: dict, slots: list[str], mode: str, obligations: dict | None = None) -> None:
    policy = policy_of(state)
    for slot in slots:
        require(slot in ROLES, "不明な担当です")
        state["sequence"] += 1
        job_id = f"job-{state['sequence']:04d}"
        prior = state["owners"].get(slot)
        state["jobs"][job_id] = {
            "id": job_id, "slot": slot, "role": ROLES[slot], "provider": policy.provider(slot),
            "snapshot_id": state["snapshot_id"], "rules_id": state["rules_id"],
            "epoch": state["epoch"], "mode": mode, "status": "PLANNED",
            "previous_owner": prior, "previous_parent": state["owner_parents"].get(slot),
            "owner_mode": ("fresh_with_ledger" if prior and policy.provider(slot) == "codex"
                           and (policy.implementation_backend != "codex" or state["owner_transports"].get(slot) == "cli") else "resume" if prior else "fresh"),
            "ledger_id": identity(unresolved(state)), "obligations": (obligations or {}).get(slot, []),
        }


def pending(state: dict) -> list[dict]:
    if state["status"] in TERMINAL or state["archive_status"] != "COMPLETE":
        return []
    return [copy.deepcopy(j) for j in state["jobs"].values() if j["status"] == "PLANNED"]


def stop(state: dict, status: str, reason: str) -> None:
    state["status"], state["stop_reason"] = status, reason


def claim(state: dict, job_id: str, snapshot_id: str, rules_id: str) -> dict:
    next_state = copy.deepcopy(state)
    require(state["status"] == "RUNNING", "停止中です。自動再試行できません")
    require(state["archive_status"] == "COMPLETE", "会話HTMLの保存が完了していません")
    require(snapshot_id == state["snapshot_id"] and rules_id == state["rules_id"], "対象または規約が変わりました")
    job = next_state["jobs"].get(job_id)
    require(job and job["status"] == "PLANNED", "二重起動または不明な依頼です")
    job["status"] = "CLAIMED"
    return next_state


def validate_result(job: dict, result: dict, receipt: dict) -> None:
    require(isinstance(result, dict) and isinstance(receipt, dict), "結果と実行証拠が必要です")
    for key in ("job_id", "slot", "provider", "snapshot_id", "rules_id"):
        expected = job["id"] if key == "job_id" else job[key]
        require(result.get(key) == expected, "依頼と結果が一致しません: " + key)
    for key in ("job_id", "provider", "role"):
        expected = job["id"] if key == "job_id" else job[key]
        require(receipt.get(key) == expected, "実行記録が一致しません: " + key)
    require(receipt.get("completed") is True and (receipt.get("actual_child") is True or job["slot"] == "hq" and receipt.get("implementation_parent") is True), "実担当の完了証拠がありません")
    require(all(text(receipt.get(k)) for k in ("owner_id", "parent_id", "evidence_ref", "started_at", "finished_at")),
            "親子ID・時刻・原記録の参照が必要です")
    require(receipt.get("source_before") == job["snapshot_id"], "開始時の対象が一致しません")
    require(result.get("coverage") in {"COMPLETE", "PARTIAL", "BLOCKED"}, "確認範囲が不正です")
    require(result.get("decision") in {"APPROVE", "REQUEST_CHANGES", "NEEDS_USER_INPUT", "BLOCKED", "RATE_LIMITED", "IMPLEMENTED", "CLARIFIED"}, "判定が不正です")
    require(text(result.get("native_verdict")), "原担当の判定が必要です")
    for key in ("findings", "closures", "questions", "missing_obligations"):
        require(isinstance(result.get(key), list), key + "は配列が必要です")
    ids = []
    for finding in result["findings"]:
        require(isinstance(finding, dict), "指摘の形式が不正です")
        require(all(text(finding.get(k)) for k in ("id", "summary", "evidence", "scope_basis")), "指摘のID・根拠・範囲の根拠が必要です")
        require(finding.get("severity") in {"low", "important", "critical"}, "重要度が不正です")
        require(finding.get("route") in {"hq", "pl"}, "未選択の層を追加する指摘は受理できません")
        ids.append(finding["id"])
    require(len(ids) == len(set(ids)), "複数の修正事項には別々のIDが必要です")
    if job.get("previous_owner") and job["slot"] != "hq":
        if job.get("owner_mode") == "fresh_with_ledger":
            require(receipt.get("previous_owner") == job["previous_owner"]
                    and receipt.get("ledger_id") == job["ledger_id"], "新規担当への台帳引継ぎが不足しています")
        else:
            require(receipt["owner_id"] == job["previous_owner"] and receipt["parent_id"] == job.get("previous_parent"), "元担当の継続が確認できません")
    if job["slot"] in REVIEW_SLOTS | {"pl"}:
        require(receipt.get("source_after") == job["snapshot_id"], "読み取り専用の確認中に対象が変わりました")
    if job["slot"] in REVIEW_SLOTS:
        loaded = result.get("rules_loaded")
        require(isinstance(loaded, dict) and loaded.get("source_set_id") == job["rules_id"]
                and isinstance(loaded.get("sections"), list) and loaded["sections"], "規約の適用節・例外の記録が必要です")
        require(type(loaded.get("complete")) is bool, "規約読了の状態が不明です")
        if result["coverage"] == "COMPLETE":
            require(loaded["complete"], "未読規約を残してCOMPLETEにできません")
    if job["slot"] == "l2":
        consultations = result.get("consultations")
        require(isinstance(consultations, dict) and isinstance(consultations.get("required_roles"), list)
                and text(consultations.get("trigger_evidence")), "L2の専門担当の要否・根拠が必要です")
        actual = receipt.get("consultants", {})
        if result["decision"] == "APPROVE":
            require(set(consultations["required_roles"]) <= {v["role"] for v in actual.values() if v.get("completed") is True},
                    "L2の必須専門担当が未完了です")
    if job["slot"] in {"qa", "e2e"}:
        checks = result.get("adequacy_checks")
        require(isinstance(checks, dict) and set(checks) == QA_CHECKS, "正常系・異常系・過不足・期待値・fixtureの確認が必要です")
        for check in checks.values():
            require(isinstance(check, dict) and check.get("status") in {"CHECKED", "NOT_APPLICABLE", "UNCONFIRMED"}
                    and text(check.get("evidence")), "QA/E2Eの確認根拠が不足しています")
        if result["decision"] == "APPROVE":
            require(all(c["status"] != "UNCONFIRMED" for c in checks.values()), "未確認の過不足を承認できません")
    if result["decision"] == "APPROVE":
        require(result["coverage"] == "COMPLETE" and not any(result[k] for k in ("findings", "questions", "missing_obligations")), "未解決事項があるため承認できません")
        accepted = {"L1.5_APPROVE", "L1.5_APPROVE_WITH_NOTES"} if job["slot"] in {"cr_a", "cr_b", "validator"} else {"APPROVE"}
        require(result["native_verdict"] in accepted, "原担当の判定が承認ではありません")
    if job["slot"] in {"hq", "pl", "validator"}:
        require(not result["findings"], "実装・計画・検証担当は発見担当の指摘一覧を直接追加できません")
        require(not result["closures"], "実装者・pl・検証担当は元の指摘を閉じられません")


def update_ledger(state: dict, job: dict, result: dict, receipt: dict) -> None:
    slot = job["slot"]
    if slot in {"hq", "pl", "validator"}:
        return
    reported = set()
    for finding in result["findings"]:
        key = slot + ":" + finding["id"]
        reported.add(key)
        old = state["ledger"].get(key)
        if old:
            require(old["status"] == "open", "解消済みIDの再利用はできません")
            require(old["evidence"] == finding["evidence"] and old["summary"] == finding["summary"], "元の指摘を上書きできません")
            if old["route"] != finding["route"] or old["severity"] != finding["severity"]:
                require(text(finding.get("disposition_evidence")), "振分け・重要度の変更には原担当の根拠が必要です")
                old.setdefault("amendments", []).append({"route": old["route"], "severity": old["severity"],
                    "evidence": finding["disposition_evidence"], "snapshot_id": job["snapshot_id"]})
                old["route"], old["severity"] = finding["route"], finding["severity"]
            old.pop("fix_pending_snapshot", None)
            continue
        state["ledger"][key] = {
            **finding, "key": key, "slot": slot, "origin_owner": receipt["owner_id"],
            "origin_snapshot": job["snapshot_id"], "status": "open",
        }
    closed_keys = set()
    for closure in result["closures"]:
        require(isinstance(closure, dict), "解消記録が不正です")
        key = closure.get("key")
        known = state["ledger"].get(key)
        require(known and known["slot"] == slot and known["status"] == "open", "他担当または不明な指摘は閉じられません")
        require(closure.get("status") in CLOSED and text(closure.get("evidence")), "解消・撤回の根拠が必要です")
        require(key not in closed_keys, "解消記録が重複しています")
        closed_keys.add(key)
        known["status"] = closure["status"]
        known["closure"] = {**closure, "owner_id": receipt["owner_id"], "snapshot_id": job["snapshot_id"]}
    own_open = {key for key, f in state["ledger"].items() if f["slot"] == slot and f["status"] == "open"}
    require(own_open <= reported, "未解決の元指摘が結果から消えています")
    if result["decision"] == "APPROVE":
        require(not own_open, "未解決の指摘を残した承認はできません")


def unresolved(state: dict) -> list[dict]:
    return [f for f in state["ledger"].values() if f["status"] == "open"]


def request_owner(state: dict, slot: str, obligations: list, return_stage: str) -> None:
    key = f"{state['epoch']}:{slot}:{return_stage}"
    count = state["owner_rounds"].get(key, 0)
    if count >= policy_of(state).max_owner_rounds:
        stop(state, "NEEDS_USER_INPUT", "限定確認後も未解決です: " + slot)
        return
    state["owner_rounds"][key] = count + 1
    state["return_stage"] = return_stage
    queue(state, [slot], "complete_evidence", {slot: obligations})


def next_review_stage(state: dict, after: str) -> None:
    stages = ["pcr", "qa", "e2e"] + (["l2"] if policy_of(state).l2_backend else [])
    index = stages.index(after) + 1
    if index == len(stages):
        if unresolved(state):
            stop(state, "BLOCKED", "未解決の指摘があります")
        else:
            stop(state, "READY_FOR_USER", "選択した確認が完了しました。commit/push/PRは実行しません")
        return
    state["stage"] = stages[index]
    slot = stages[index]
    queue(state, [slot], "recheck" if slot in state["owners"] else "initial")


def route_open(state: dict, after: str) -> bool:
    findings = [f for f in unresolved(state) if f.get("fix_pending_snapshot") != state["snapshot_id"]]
    if not findings:
        return False
    if any(f["route"] == "pl" for f in findings):
        state["clarify_slots"] = sorted({f["slot"] for f in findings if f["route"] == "pl"})
        state["return_stage"] = after
        state["stage"] = "pl"
        queue(state, ["pl"], "clarify", {"pl": [f["key"] for f in findings if f["route"] == "pl"]})
        return True
    if state["fix_rounds"] >= policy_of(state).max_fix_rounds:
        stop(state, "NEEDS_USER_INPUT", "修正回数の上限です")
        return True
    state["stage"] = "fix"
    state["fix_rounds"] += 1
    queue(state, ["hq"], "fix", {"hq": [f["key"] for f in findings]})
    return True


def after_validation(state: dict, result: dict) -> None:
    open_keys = {f["key"] for f in unresolved(state) if f["slot"] in {"cr_a", "cr_b"}}
    assessments = result.get("assessments")
    require(isinstance(assessments, dict) and set(assessments) == open_keys, "検証担当は全ての未解決IDを照合してください")
    require(result.get("mandatory_coverage_checked") is True, "必須確認の不足を照合していません")
    requests: dict[str, list[str]] = {}
    for key, assessment in assessments.items():
        require(isinstance(assessment, dict) and assessment.get("fact") in {"CONFIRMED", "REJECTED", "UNCONFIRMED"}
                and assessment.get("pr_scope") in {"IN_SCOPE", "OUT_OF_SCOPE", "UNCONFIRMED"}
                and text(assessment.get("evidence")), "検証の根拠・範囲判定が不足しています")
        if assessment["fact"] != "CONFIRMED" or assessment["pr_scope"] != "IN_SCOPE":
            requests.setdefault(state["ledger"][key]["slot"], []).append(key)
    for slot in ("cr_a", "cr_b"):
        report = state["reports"][slot]
        if report["coverage"] != "COMPLETE" or report["missing_obligations"]:
            requests.setdefault(slot, []).extend(report["missing_obligations"] or ["coverage"])
        elif report["decision"] != "APPROVE" and not report["findings"] and not report["questions"]:
            requests.setdefault(slot, []).append("native_verdict_without_disposition")
    if result["coverage"] != "COMPLETE" or result["missing_obligations"] or (not open_keys and result["decision"] != "APPROVE"):
        request_owner(state, "validator", result["missing_obligations"] or ["coverage_or_native_verdict"], "validator")
        return
    question_slots = [slot for slot in ("cr_a", "cr_b") if state["reports"][slot]["questions"]]
    if question_slots:
        state["clarify_slots"] = question_slots
        state["return_stage"] = "pcr"
        state["stage"] = "pl"
        state["questions"] = [q for slot in question_slots for q in state["reports"][slot]["questions"]]
        queue(state, ["pl"], "clarify", {"pl": state["questions"]})
        return
    if requests:
        state["reconcile_after"] = "pcr"
        state["reconcile"] = [{"slot": k, "obligations": v} for k, v in requests.items()]
        item = state["reconcile"].pop(0)
        state["stage"] = "reconcile"
        request_owner(state, item["slot"], item["obligations"], "reconcile")
        return
    if not route_open(state, "pcr"):
        next_review_stage(state, "pcr")


def accept(state: dict, job_id: str, result: dict, receipt: dict) -> dict:
    """受理できない結果では入力の状態を変更しません。"""
    require(state["status"] == "RUNNING", "停止済みです。結果は監査記録としてのみ保存してください")
    next_state = copy.deepcopy(state)
    job = next_state["jobs"].get(job_id)
    require(job and job["status"] == "CLAIMED", "未起動・二重結果または不明な依頼です")
    validate_result(job, result, receipt)
    if job["mode"] == "initial" and job["slot"] in {"cr_a", "cr_b", "validator"}:
        used = [v for k, v in next_state["owners"].items() if k in {"cr_a", "cr_b", "validator"}]
        require(receipt["owner_id"] not in used, "独立レビューで同じ担当を再利用しています")
    job["status"] = "COMPLETED"
    job["receipt"] = copy.deepcopy(receipt)
    next_state["history"].append({"job_id": job_id, "result": copy.deepcopy(result), "receipt": copy.deepcopy(receipt)})
    next_state["owners"][job["slot"]] = receipt["owner_id"]
    next_state["owner_parents"][job["slot"]] = receipt["parent_id"]
    next_state["owner_transports"][job["slot"]] = receipt.get("transport", "native")
    next_state["reports"][job["slot"]] = copy.deepcopy(result)
    update_ledger(next_state, job, result, receipt)
    if result.get("handoffs"):
        next_state.setdefault("pending_handoffs", []).append({"job_id": job_id, "items": copy.deepcopy(result["handoffs"])})
        stop(next_state, "NEEDS_USER_INPUT", "跨層handoffを保存しました。この試行版では自動閉鎖・別層の追加起動をしません")
        return next_state
    if result["decision"] in {"RATE_LIMITED", "BLOCKED"}:
        stop(next_state, result["decision"], result.get("reason", result["native_verdict"]))
        return next_state
    if result["decision"] == "NEEDS_USER_INPUT" and job["slot"] == "pl":
        stop(next_state, "NEEDS_USER_INPUT", result.get("reason", "業務判断が必要です"))
        return next_state
    slot = job["slot"]
    if slot == "hq":
        require(result["decision"] == "IMPLEMENTED", "実装完了ではありません")
        require(result["coverage"] == "COMPLETE" and not result["questions"] and not result["missing_obligations"], "実装の必須条件が未完了です")
        require(isinstance(result.get("verification"), list) and result["verification"], "実装側の検証記録が必要です")
        for v in result["verification"]:
            require(isinstance(v, dict) and text(v.get("evidence")) and v.get("status") in {"PASS", "FAILED", "NOT_RUN", "PARTIAL"}
                    and type(v.get("required")) is bool, "検証記録が不正です")
            require(not v["required"] or v["status"] == "PASS", "必須の実装側検証が完了していません")
        new_snapshot = result.get("new_snapshot_id")
        require(text(new_snapshot) and receipt.get("source_after") == new_snapshot, "修正後の実対象が一致しません")
        if job["mode"] == "fix" and new_snapshot == next_state["snapshot_id"]:
            stop(next_state, "NEEDS_USER_INPUT", "修正後も対象が同じです。進展のない再レビューは開始しません")
            return next_state
        next_state["snapshot_id"] = new_snapshot
        if job["mode"] == "fix":
            for finding in unresolved(next_state):
                finding["fix_pending_snapshot"] = new_snapshot
        next_state["epoch"] += 1
        next_state["stage"] = "pcr"
        queue(next_state, ["cr_a", "cr_b"], "recheck" if "cr_a" in next_state["owners"] else "initial")
    elif slot == "pl":
        answers = result.get("answers")
        require(result["decision"] == "CLARIFIED" and isinstance(answers, list) and answers
                and all(isinstance(a, dict) and text(a.get("answer")) and text(a.get("evidence")) for a in answers), "plの根拠付き回答が不足しています")
        next_state["answers"].extend(answers)
        require(type(result.get("requires_user")) is bool, "plは人間の判断が必要かを明示してください")
        if result["requires_user"]:
            stop(next_state, "NEEDS_USER_INPUT", "plの回答を保存しました。業務上の決定が必要です")
        else:
            require(result["coverage"] == "COMPLETE" and not result["questions"] and not result["missing_obligations"], "plの確認が未完了です")
            require(result.get("resolution_basis") == "existing_authoritative_sources", "既存根拠で決まらない要件は自動採用できません")
            slots = next_state.get("clarify_slots", [])
            require(bool(slots), "確認を返す原担当が不明です")
            next_state["reconcile_after"] = next_state["return_stage"]
            next_state["reconcile"] = [{"slot": s, "obligations": answers} for s in slots]
            item = next_state["reconcile"].pop(0)
            next_state["stage"] = "reconcile"
            request_owner(next_state, item["slot"], item["obligations"], "reconcile")
    elif slot in {"cr_a", "cr_b"} and next_state["stage"] == "pcr":
        current = [j for j in next_state["jobs"].values() if j["epoch"] == job["epoch"] and j["slot"] in {"cr_a", "cr_b"}]
        if all(j["status"] == "COMPLETED" for j in current):
            next_state["stage"] = "validator"
            queue(next_state, ["validator"], "recheck" if "validator" in next_state["owners"] else "initial")
    elif next_state["stage"] == "reconcile":
        if result["coverage"] != "COMPLETE" or result["missing_obligations"] or result["questions"]:
            stop(next_state, "NEEDS_USER_INPUT", "原担当の限定確認が未完了です")
        elif next_state["reconcile"]:
            item = next_state["reconcile"].pop(0)
            request_owner(next_state, item["slot"], item["obligations"], "reconcile")
        else:
            rejected = [k for k, a in next_state["reports"]["validator"]["assessments"].items()
                        if a["fact"] != "CONFIRMED" or a["pr_scope"] != "IN_SCOPE"]
            if any(k in {f["key"] for f in unresolved(next_state)} for k in rejected):
                stop(next_state, "NEEDS_USER_INPUT", "原担当と検証担当の判断が一致しません")
            elif not route_open(next_state, next_state.get("reconcile_after", "pcr")):
                next_review_stage(next_state, next_state.get("reconcile_after", "pcr"))
    elif slot == "validator":
        after_validation(next_state, result)
    elif slot in {"qa", "e2e", "l2"}:
        if result["missing_obligations"] or result["coverage"] != "COMPLETE":
            request_owner(next_state, slot, result["missing_obligations"] or ["coverage"], slot)
        elif result["questions"] or result["decision"] == "NEEDS_USER_INPUT":
            next_state["clarify_slots"] = [slot]
            next_state["return_stage"] = slot
            next_state["stage"] = "pl"
            next_state["questions"] = result["questions"]
            queue(next_state, ["pl"], "clarify", {"pl": result["questions"]})
        elif not route_open(next_state, slot):
            require(result["decision"] == "APPROVE", "指摘なしでも未承認の判定を通せません")
            next_review_stage(next_state, slot)
    return next_state


def task_payload(state: dict, job_id: str) -> dict:
    job = copy.deepcopy(state["jobs"][job_id])
    job["workflow_id"] = WORKFLOW
    job["request"] = state["request"]
    job["publish"] = False
    job["read_only"] = job["slot"] != "hq"
    job["rules_id"] = state["rules_id"]
    job["scope"] = "delta_and_pending" if job["mode"] in {"fix", "recheck", "complete_evidence"} else "assigned_initial_scope"
    if job["slot"] == "validator":
        job["reports"] = {k: copy.deepcopy(state["reports"][k]) for k in ("cr_a", "cr_b")}
    elif job["slot"] in {"hq", "pl"} or job["mode"] != "initial":
        job["open_findings"] = copy.deepcopy(unresolved(state))
        job["answers"] = copy.deepcopy(state["answers"])
    if job["slot"] in {"qa", "e2e"}:
        job["adequacy_checks_required"] = sorted(QA_CHECKS)
    job["review_kind"] = ("self_check" if job["provider"] == policy_of(state).implementation_backend else "cross_model")
    return job
