"""遷移を模擬受領結果で検証します。実モデルは起動しません。"""
from __future__ import annotations

import copy
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import implementation_review_state as flow


def fixture_state(**overrides):
    values = dict(implementation_backend="codex", pcr_backend="codex", qa_backend="claude",
                  e2e_backend="codex", l2_backend="claude")
    values.update(overrides)
    state = flow.new_state(flow.Policy(**values), "snapshot-0", "rules-0", "模擬依頼: 演習の設問編集を実装してください。")
    state["archive_status"] = "COMPLETE"
    return state


def finding(id="F1", route="hq", summary="古い設問で上書きします"):
    return {"id": id, "summary": summary, "evidence": "fixture.ts:10 保存後も古いcacheを使用します",
            "scope_basis": "変更した保存処理", "severity": "important", "route": route}


def prepare(state, slot, **updates):
    job = next(j for j in flow.pending(state) if j["slot"] == slot)
    state = flow.claim(state, job["id"], state["snapshot_id"], state["rules_id"])
    job = state["jobs"][job["id"]]
    verdict = "L1.5_APPROVE" if slot in {"cr_a", "cr_b", "validator"} else "APPROVE"
    result = {"job_id": job["id"], "slot": slot, "provider": job["provider"],
              "snapshot_id": job["snapshot_id"], "rules_id": job["rules_id"], "coverage": "COMPLETE",
              "decision": "APPROVE", "native_verdict": verdict,
              "findings": [], "closures": [], "questions": [], "missing_obligations": []}
    if slot in flow.REVIEW_SLOTS:
        result["rules_loaded"] = {"source_set_id": job["rules_id"], "complete": True, "sections": ["fixture: applicable scope and exceptions"]}
    if slot == "l2":
        result["consultations"] = {"required_roles": [], "trigger_evidence": "fixture: no framework boundary is changed"}
    if slot == "hq":
        result.update(decision="IMPLEMENTED", native_verdict="IMPLEMENTED", new_snapshot_id="snapshot-" + str(state["epoch"] + 1),
                      verification=[{"status": "PASS", "required": True, "evidence": "fixture test exit=0"}])
    if slot == "validator":
        result.update(assessments={f["key"]: {"fact": "CONFIRMED", "pr_scope": "IN_SCOPE", "evidence": f["evidence"]}
                                  for f in flow.unresolved(state) if f["slot"] in {"cr_a", "cr_b"}}, mandatory_coverage_checked=True)
        if result["assessments"]:
            result.update(decision="REQUEST_CHANGES", native_verdict="L1.5_REQUEST_CHANGES")
    if slot in {"qa", "e2e"}:
        result["adequacy_checks"] = {key: {"status": "CHECKED", "evidence": "fixture assertion: " + key} for key in flow.QA_CHECKS}
    result.update(updates)
    if result["findings"] or result["missing_obligations"] or result["questions"]:
        result.update(decision="REQUEST_CHANGES", native_verdict="L1.5_REQUEST_CHANGES" if slot in {"cr_a", "cr_b", "validator"} else "REQUEST_CHANGES")
    owner = job["previous_owner"] if job["owner_mode"] == "resume" else "fixture-owner-" + job["id"]
    parent = job["previous_parent"] if job["owner_mode"] == "resume" else "fixture-parent-" + job["id"]
    receipt = {"job_id": job["id"], "provider": job["provider"], "role": job["role"], "owner_id": owner,
               "parent_id": parent, "actual_child": True, "completed": True, "evidence_ref": "fixture-native.jsonl",
               "started_at": "2026-11-12T07:00:00Z", "finished_at": "2026-11-12T07:01:00Z",
               "source_before": job["snapshot_id"], "source_after": result.get("new_snapshot_id", job["snapshot_id"]),
               "previous_owner": job["previous_owner"], "ledger_id": job["ledger_id"]}
    return state, job, result, receipt


def finish(state, slot, **updates):
    state, job, result, receipt = prepare(state, slot, **updates)
    return flow.accept(state, job["id"], result, receipt)


def through_pcr(state):
    for slot in ("hq", "cr_a", "cr_b", "validator"):
        state = finish(state, slot)
    return state


class StateTests(unittest.TestCase):
    def test_qa_e2e_four_provider_combinations(self):
        for qa, e2e in itertools.product(("codex", "claude"), repeat=2):
            with self.subTest(qa=qa, e2e=e2e):
                state = through_pcr(fixture_state(qa_backend=qa, e2e_backend=e2e))
                self.assertEqual(flow.pending(state)[0]["provider"], qa)
                state = finish(state, "qa")
                self.assertEqual(flow.pending(state)[0]["provider"], e2e)
                state = finish(state, "e2e")
                state = finish(state, "l2")
                self.assertEqual(state["status"], "READY_FOR_USER")
                self.assertFalse(state["policy"]["publish"])

    def test_pcr_discovery_jobs_available_together(self):
        state = finish(fixture_state(), "hq")
        self.assertEqual({j["slot"] for j in flow.pending(state)}, {"cr_a", "cr_b"})
        self.assertNotIn("reports", flow.task_payload(state, flow.pending(state)[0]["id"]))
        state = finish(state, "cr_a")
        self.assertEqual([j["slot"] for j in flow.pending(state)], ["cr_b"])
        state = finish(state, "cr_b")
        self.assertEqual([j["slot"] for j in flow.pending(state)], ["validator"])
        self.assertEqual(set(flow.task_payload(state, flow.pending(state)[0]["id"])["reports"]), {"cr_a", "cr_b"})

    def test_fix_and_delta_recheck_closes_only_by_owner(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual(flow.pending(state)[0]["slot"], "hq")
        state = finish(state, "hq")
        self.assertEqual(state["ledger"]["cr_a:F1"]["status"], "open")
        self.assertEqual({j["mode"] for j in flow.pending(state)}, {"recheck"})
        state = finish(state, "cr_a", closures=[{"key": "cr_a:F1", "status": "reviewer_confirmed_fixed", "evidence": "fixture.ts:10 invalidation完了後に開きます"}])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual(state["stage"], "qa")
        self.assertEqual(state["fix_rounds"], 1)

    def test_qa_fix_invalidates_pcr_and_qa(self):
        state = through_pcr(fixture_state())
        state = finish(state, "qa", findings=[finding("QA1", summary="異常系の期待値がありません")])
        state = finish(state, "hq")
        self.assertEqual({j["slot"] for j in flow.pending(state)}, {"cr_a", "cr_b"})
        self.assertEqual(state["ledger"]["qa:QA1"]["status"], "open")

    def test_qa_repair_is_confirmed_by_qa_before_another_fix(self):
        state = through_pcr(fixture_state())
        state = finish(state, "qa", findings=[finding("Q1")])
        state = finish(state, "hq")
        state = finish(state, "cr_a")
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual([j["slot"] for j in flow.pending(state)], ["qa"])
        state = finish(state, "qa", closures=[{"key": "qa:Q1", "status": "reviewer_confirmed_fixed", "evidence": "negative assertion added"}])
        state = finish(state, "e2e")
        state = finish(state, "l2")
        self.assertEqual(state["status"], "READY_FOR_USER")
        self.assertEqual(state["fix_rounds"], 1)

    def test_qa_question_returns_to_qa_then_e2e(self):
        state = through_pcr(fixture_state())
        state = finish(state, "qa", questions=["Q1: intended fail behavior"])
        state = finish(state, "pl", decision="CLARIFIED", native_verdict="CLARIFIED", requires_user=False,
                       resolution_basis="existing_authoritative_sources", answers=[{"id": "Q1", "answer": "explicit 400", "evidence": "spec.md:3"}])
        state = finish(state, "qa")
        self.assertEqual(state["stage"], "e2e")

    def test_pl_to_hq_route_requires_owner_evidence(self):
        state = finish(fixture_state(), "hq")
        f = finding(route="pl")
        state = finish(state, "cr_a", findings=[f])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        state = finish(state, "pl", decision="CLARIFIED", native_verdict="CLARIFIED", requires_user=False,
                       resolution_basis="existing_authoritative_sources", answers=[{"id": "Q1", "answer": "preserve existing questions", "evidence": "spec.md:20"}])
        amended = {**f, "route": "hq", "disposition_evidence": "spec.md:20 defines preservation"}
        state = finish(state, "cr_a", findings=[amended])
        self.assertEqual(flow.pending(state)[0]["slot"], "hq")
        self.assertEqual(len(state["ledger"]["cr_a:F1"]["amendments"]), 1)

    def test_no_progress_stops_without_redispatch(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        state = finish(state, "hq", new_snapshot_id=state["snapshot_id"])
        self.assertEqual(state["status"], "NEEDS_USER_INPUT")
        self.assertEqual(flow.pending(state), [])

    def test_repair_cap_stops(self):
        state = finish(fixture_state(max_fix_rounds=1), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        state = finish(state, "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual(state["status"], "NEEDS_USER_INPUT")

    def test_rejection_requires_original_owner_response(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator", assessments={"cr_a:F1": {"fact": "REJECTED", "pr_scope": "OUT_OF_SCOPE", "evidence": "baseにも同じ問題があります"}})
        self.assertEqual(state["ledger"]["cr_a:F1"]["status"], "open")
        self.assertEqual(flow.pending(state)[0]["slot"], "cr_a")
        state = finish(state, "cr_a", closures=[{"key": "cr_a:F1", "status": "reviewer_withdrawn", "evidence": "base/head一致、差分制限により撤回します"}])
        self.assertEqual(state["stage"], "qa")

    def test_unresolved_rejection_stops(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator", assessments={"cr_a:F1": {"fact": "UNCONFIRMED", "pr_scope": "IN_SCOPE", "evidence": "根拠不足です"}})
        state = finish(state, "cr_a", findings=[finding()])
        self.assertEqual(state["status"], "NEEDS_USER_INPUT")

    def test_missing_evidence_returns_to_reviewer_not_hq(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", coverage="PARTIAL", missing_obligations=["scope-rule-exception"])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual(flow.pending(state)[0]["slot"], "cr_a")
        self.assertEqual(flow.pending(state)[0]["mode"], "complete_evidence")
        state = finish(state, "cr_a")
        self.assertEqual(state["stage"], "qa")

    def test_pl_reuses_sourced_requirements_then_returns_to_owner(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", questions=["Q1:既存のカテゴリ未設定を許すか"])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        self.assertEqual(flow.pending(state)[0]["slot"], "pl")
        state = finish(state, "pl", decision="CLARIFIED", native_verdict="CLARIFIED", requires_user=False,
                       resolution_basis="existing_authoritative_sources", answers=[{"id": "Q1", "answer": "既存仕様で許容済みです", "evidence": "spec.md:20"}])
        self.assertEqual(flow.pending(state)[0]["slot"], "cr_a")
        state = finish(state, "cr_a")
        self.assertEqual(state["stage"], "qa")

    def test_pl_cannot_invent_product_decision(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", questions=["Q1"])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        state = finish(state, "pl", decision="CLARIFIED", native_verdict="CLARIFIED", requires_user=True,
                       answers=[{"id": "Q1", "answer": "権限の選択が必要です", "evidence": "仕様A/Bが衝突しています"}])
        self.assertEqual(state["status"], "NEEDS_USER_INPUT")

    def test_double_claim_and_double_result_rejected(self):
        state, job, result, receipt = prepare(fixture_state(), "hq")
        with self.assertRaises(flow.ContractError):
            flow.claim(state, job["id"], state["snapshot_id"], state["rules_id"])
        state = flow.accept(state, job["id"], result, receipt)
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)

    def test_wrong_provider_rejected(self):
        state, job, result, receipt = prepare(through_pcr(fixture_state()), "qa")
        receipt["provider"] = "codex"
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)

    def test_source_change_and_rules_change_rejected(self):
        state = fixture_state()
        for snapshot, rules in (("different", "rules-0"), ("snapshot-0", "different")):
            with self.assertRaises(flow.ContractError):
                flow.claim(state, "job-0001", snapshot, rules)
        state, job, result, receipt = prepare(finish(state, "hq"), "cr_a")
        receipt["source_after"] = "changed"
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)

    def test_rate_limit_does_not_change_backend_or_retry(self):
        state = through_pcr(fixture_state())
        state = finish(state, "qa", decision="RATE_LIMITED", native_verdict="RATE_LIMITED", coverage="BLOCKED")
        self.assertEqual(state["status"], "RATE_LIMITED")
        self.assertEqual(flow.pending(state), [])
        self.assertEqual(state["policy"]["qa_backend"], "claude")

    def test_archive_required_before_dispatch(self):
        state = fixture_state()
        state["archive_status"] = "PARTIAL"
        self.assertEqual(flow.pending(state), [])
        with self.assertRaises(flow.ContractError):
            flow.claim(state, "job-0001", state["snapshot_id"], state["rules_id"])

    def test_partial_and_missing_check_never_approve(self):
        state, job, result, receipt = prepare(through_pcr(fixture_state()), "qa")
        result["coverage"] = "PARTIAL"
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)
        result["coverage"] = "COMPLETE"
        result["adequacy_checks"].pop("fail_path")
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)

    def test_no_actual_child_no_approval(self):
        state, job, result, receipt = prepare(through_pcr(fixture_state()), "qa")
        receipt["actual_child"] = False
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)

    def test_validator_checks_all_ids_and_mandatory_coverage(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        for changes in ({"assessments": {}}, {"mandatory_coverage_checked": False}):
            s, job, result, receipt = prepare(state, "validator", **changes)
            with self.assertRaises(flow.ContractError):
                flow.accept(s, job["id"], result, receipt)

    def test_hq_and_validator_cannot_close_other_findings(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        s, job, result, receipt = prepare(state, "validator", closures=[{"key": "cr_a:F1", "status": "reviewer_withdrawn", "evidence": "parent says so"}])
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)

    def test_duplicate_findings_must_split_ids(self):
        s, job, result, receipt = prepare(finish(fixture_state(), "hq"), "cr_a", findings=[finding(), finding(summary="別問題です")])
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)

    def test_plain_approval_does_not_drop_open_finding(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", findings=[finding()])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        state = finish(state, "hq")
        s, job, result, receipt = prepare(state, "cr_a")
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)

    def test_policy_forbids_publish_and_same_family_l2(self):
        for extra in ({"publish": True}, {"l2_backend": "codex"}, {"max_fix_rounds": 4}, {"qa_backend": "unknown"}):
            with self.assertRaises(flow.ContractError):
                fixture_state(**extra)

    def test_optional_l2_is_not_started(self):
        state = through_pcr(fixture_state(l2_backend=None))
        state = finish(state, "qa")
        state = finish(state, "e2e")
        self.assertEqual(state["status"], "READY_FOR_USER")

    def test_required_l2_consultation_cannot_be_skipped(self):
        state = through_pcr(fixture_state())
        state = finish(state, "qa")
        state = finish(state, "e2e")
        s, job, result, receipt = prepare(state, "l2", consultations={"required_roles": ["react-ui-flow"], "trigger_evidence": "tsx boundary changed"})
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)
        receipt["consultants"] = {"react-id": {"role": "react-ui-flow", "completed": True}}
        accepted = flow.accept(s, job["id"], result, receipt)
        self.assertEqual(accepted["status"], "READY_FOR_USER")

    def test_missing_rule_read_cannot_be_complete(self):
        s, job, result, receipt = prepare(finish(fixture_state(), "hq"), "cr_a")
        result["rules_loaded"]["complete"] = False
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)

    def test_returned_payload_cannot_modify_state(self):
        state = finish(fixture_state(), "hq")
        value = flow.task_payload(state, flow.pending(state)[0]["id"])
        value["request"] = "overwrite"
        self.assertNotEqual(state["request"], "overwrite")

    def test_failed_validation_is_transactional(self):
        state, job, result, receipt = prepare(fixture_state(), "hq")
        before = copy.deepcopy(state)
        result["provider"] = "wrong"
        with self.assertRaises(flow.ContractError):
            flow.accept(state, job["id"], result, receipt)
        self.assertEqual(state, before)

    def test_same_family_is_not_cross_model_evidence(self):
        state = through_pcr(fixture_state(qa_backend="codex"))
        task = flow.task_payload(state, flow.pending(state)[0]["id"])
        self.assertEqual(task["review_kind"], "self_check")

    def test_reviewer_owner_cannot_be_silently_replaced(self):
        state = finish(fixture_state(), "hq")
        state = finish(state, "cr_a", coverage="PARTIAL", missing_obligations=["rules"])
        state = finish(state, "cr_b")
        state = finish(state, "validator")
        s, job, result, receipt = prepare(state, "cr_a")
        receipt["owner_id"] = "different-owner"
        with self.assertRaises(flow.ContractError):
            flow.accept(s, job["id"], result, receipt)


if __name__ == "__main__":
    unittest.main()
