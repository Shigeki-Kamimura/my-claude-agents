"""対象照合、修正差分、実IDと判定欄の正常・失敗系を確認します。"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_md_review as fixtures

launcher, review = fixtures.launcher, fixtures.review

receipts = launcher.receipts


class MDReviewFlowTests(unittest.TestCase):
    setUp = fixtures.MDReviewTests.setUp
    git = fixtures.MDReviewTests.git
    cli = fixtures.MDReviewTests.cli
    init = fixtures.MDReviewTests.init
    freeze = fixtures.MDReviewTests.freeze

    def result(self, **updates):
        value = {"workflow_id": "claude-codex-review", "phase": "l1_5", "reviewer": "code-quality-reviewer",
                 "snapshot_id": "source-A", "native_verdict": "L1.5_APPROVE", "coverage": "COMPLETE", "decision": "APPROVE",
                 "open_item_ids": [], "questions": [], "handoffs": [],
                 "invocation_evidence": {"parent_session_id": "parent-A", "reviewer_id": "child-A", "platform": "Codex", "model": "fixture-model"}}
        value.update(updates)
        return value

    def body(self, result):
        return "Fixture result\n\n```workflow-result\n" + json.dumps(result) + "\n```\n"

    def native(self, result):
        rows = [{"type": "thread.started", "thread_id": "parent-A"},
                {"type": "item.completed", "item": {"type": "collab_tool_call", "tool": "spawn_agent", "status": "completed",
                 "sender_thread_id": "parent-A", "receiver_thread_ids": ["child-A"],
                 "agents_states": {"child-A": {"status": "completed", "message": self.body(result)}}}}]
        return receipts.identities(rows, "codex", "code-quality-reviewer")

    def validate(self, result, native=None, previous=None):
        return receipts.validate(result, {"direction": "claude-codex-review", "reviewer": "code-quality-reviewer"},
                                 "cr", "source-A", native or self.native(result), previous)

    def test_missing_branch_or_untracked_path_stops_before_launch(self):
        self.init("--paths", "code.txt", code=2)
        self.assertFalse(self.run.exists())
        self.init()
        (self.project / "forgotten.txt").write_text("new fix\n")
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2)
        self.assertEqual([], list(self.run.glob("*/execution.json")))

    def test_auto_scope_includes_rename_ends_modes_and_new_files(self):
        self.git("mv", "code.txt", "renamed.txt")
        (self.project / "renamed.txt").chmod(0o755)
        self.cli("md_review.py", "--project", self.project, "--base", self.base, "--direction", "claude-codex-review",
                 "--layers", "cr", "--rules", self.project / "rule.md", "--summary-file", self.summary, "--out-dir", self.run)
        config = review.load_run(self.run)[1]
        self.assertEqual({"code.txt", "renamed.txt", "new.txt"}, set(config["paths"]))

    def test_excluded_environment_bytes_are_not_read(self):
        (self.project / ".env.development").write_text("PRIVATE_FIXTURE_VALUE\n")
        config = {"project": str(self.project), "base": self.base, "paths": ["code.txt", "new.txt"], "exclusions": {}}
        read_bytes = Path.read_bytes
        def guarded(path):
            self.assertNotEqual(".env.development", path.name)
            return read_bytes(path)
        with patch.object(Path, "read_bytes", guarded):
            scope = review.check_scope(config)
        self.assertIn(".env.development", scope["secret_exclusions"])
        self.init("--exclude", "new.txt", "unrelated change", "--paths", "code.txt")
        self.assertEqual("unrelated change", review.load_run(self.run)[1]["exclusions"]["new.txt"])

    def test_delta_contains_only_changes_since_reviewed_worktree(self):
        old_dir, config, old_info = self.freeze()
        (self.project / "code.txt").write_text("fixed\n")
        target = self.run / "round-2"
        target.mkdir()
        for view in ("base", "head", "index", "worktree"):
            (target / view).mkdir()
        before = review.capture(config, target)
        comparison = launcher.previous_source(self.run, {"round_id": old_dir.name, "result": {"snapshot_id": old_info["snapshot_id"]}}, target, before)
        diff = review.frozen_diff(target, "delta")
        self.assertIn("-working", diff)
        self.assertIn("+fixed", diff)
        self.assertNotIn("+branch", diff)
        self.assertNotIn("new.txt", diff)
        self.assertEqual(["code.txt"], comparison["changed_paths"])

    def test_modified_prior_snapshot_cannot_be_used_for_delta(self):
        old_dir, config, before = self.freeze()
        (old_dir / "worktree/code.txt").write_text("tampered\n")
        target = self.run / "round-2"
        target.mkdir()
        with self.assertRaises(ValueError):
            launcher.previous_source(self.run, {"round_id": old_dir.name, "result": {"snapshot_id": before["snapshot_id"]}}, target, before)

    def test_result_requires_runtime_ids_snapshot_and_consistent_approval(self):
        good = self.result()
        self.assertTrue(self.validate(good)["approved"])
        mutations = [{"snapshot_id": "stale"}, {"phase": "l2"}, {"reviewer": "adviser"},
                     {"coverage": "PARTIAL"}, {"open_item_ids": ["CR-01"]}, {"questions": ["unanswered"]},
                     {"native_verdict": "L1.5_REQUEST_CHANGES"}]
        for change in mutations:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(self.result(**change))
        forged = copy.deepcopy(good)
        forged["invocation_evidence"]["reviewer_id"] = "invented-child"
        with self.assertRaises(ValueError):
            self.validate(forged, self.native(good))
        with self.assertRaises(ValueError):
            receipts.workflow_result(self.body(good) + self.body(good))

    def test_prior_finding_needs_explicit_owner_closure_evidence(self):
        previous = {"parent_session_id": "parent-A", "reviewer_id": "child-A", "result": self.result(open_item_ids=["CR-01"])}
        good = self.result()
        with self.assertRaises(ValueError):
            self.validate(good, previous=previous)
        good["invocation_evidence"]["finding_updates"] = {"CR-01": {"status": "reviewer_confirmed_fixed", "evidence": "code.txt fix inspected"}}
        self.assertTrue(self.validate(good, previous=previous)["approved"])

    def test_claude_agent_and_resumed_child_ids_come_from_native_result(self):
        for tool in ("Agent", "Task"):
            with self.subTest(tool=tool):
                rows = [{"type": "result", "session_id": "parent-A"},
                        {"message": {"content": [{"type": "tool_use", "id": "call-A", "name": tool, "input": {"subagent_type": "code-quality-reviewer"}}]}},
                        {"message": {"content": [{"type": "tool_result", "tool_use_id": "call-A"}]}, "toolUseResult": {"agentId": "child-A"}}]
                native = receipts.identities(rows, "claude", "code-quality-reviewer")
                self.assertEqual({"child-A": "code-quality-reviewer"}, native["children"])
                failed = copy.deepcopy(rows)
                failed[-1]["message"]["content"][0]["is_error"] = True
                self.assertEqual({}, receipts.identities(failed, "claude", "code-quality-reviewer")["children"])
                missing = copy.deepcopy(rows)
                del missing[-1]["toolUseResult"]["agentId"]
                self.assertEqual({}, receipts.identities(missing, "claude", "code-quality-reviewer")["children"])
        resumed = [{"type": "result", "session_id": "parent-A"},
                   {"message": {"content": [{"type": "tool_use", "id": "call-B", "name": "SendMessage", "input": {"to": "child-A"}}]}},
                   {"message": {"content": [{"type": "tool_result", "tool_use_id": "call-B"}]}, "toolUseResult": {"success": True, "resumedAgentId": "child-A"}}]
        self.assertIn("child-A", receipts.identities(resumed, "claude", "code-quality-reviewer", {"reviewer_id": "child-A"})["children"])
        self.assertEqual({}, receipts.identities(resumed, "claude", "code-quality-reviewer", {"reviewer_id": "other-child"})["children"])

    def test_codex_parent_cannot_replace_native_child_verdict(self):
        child = self.result(decision="REQUEST_CHANGES", native_verdict="L1.5_REQUEST_CHANGES", open_item_ids=["CR-01"])
        parent = self.result()
        native = self.native(child)
        checked = self.validate(parent, native)
        with self.assertRaises(ValueError):
            launcher.child_result_matches(self.project, native, checked, "codex")

    def test_runtime_ids_can_be_bound_without_asking_model_to_guess(self):
        result = self.result()
        del result["invocation_evidence"]["parent_session_id"]
        del result["invocation_evidence"]["reviewer_id"]
        native = self.native(result)
        launcher.bind_reviewer(self.project, native, result, "codex", "code-quality-reviewer")
        checked = self.validate(result, native)
        self.assertEqual("parent-A", checked["parent_session_id"])
        self.assertEqual("child-A", checked["reviewer_id"])

    def test_old_claude_child_output_does_not_confirm_resumed_review(self):
        result = self.result()
        parent = self.temp / "native/parent-A.jsonl"
        child = parent.with_suffix("") / "subagents/agent-child-A.jsonl"
        child.parent.mkdir(parents=True)
        row = {"type": "assistant", "message": {"content": [{"type": "text", "text": self.body(result)}]}}
        child.write_text(json.dumps(row) + "\n")
        offset = child.stat().st_size
        checked = {"reviewer_id": "child-A", "result": result}
        with patch.object(receipts, "claude_transcript", return_value=parent):
            with self.assertRaises(ValueError):
                launcher.child_result_matches(self.project, self.native(result), checked, "claude", offset)
            with child.open("a") as stream:
                stream.write(json.dumps(row) + "\n")
            launcher.child_result_matches(self.project, self.native(result), checked, "claude", offset)

    def test_native_child_id_claim_is_checked_even_when_parent_omits_ids(self):
        child = self.result()
        child["invocation_evidence"]["parent_session_id"] = "wrong-parent"
        parent = self.result()
        del parent["invocation_evidence"]["parent_session_id"]
        del parent["invocation_evidence"]["reviewer_id"]
        with self.assertRaises(ValueError):
            launcher.bind_reviewer(self.project, self.native(child), parent, "codex", "code-quality-reviewer")

    def test_snapshot_metadata_is_bound_to_original_review_id(self):
        old_dir, config, old_info = self.freeze()
        saved = old_dir / "snapshot.json"
        modified = json.loads(saved.read_text())
        modified["paths"] = [row for row in modified["paths"] if row[0] != "new.txt"]
        modified["snapshot_id"] = review.digest(json.dumps({k: v for k, v in modified.items() if k != "snapshot_id"}, sort_keys=True).encode())
        saved.write_text(json.dumps(modified))
        target = self.run / "round-2"
        target.mkdir()
        with self.assertRaises(ValueError):
            launcher.previous_source(self.run, {"round_id": old_dir.name, "result": {"snapshot_id": old_info["snapshot_id"]}}, target, review.capture(config))

    def test_handoffs_persist_and_only_actual_owner_can_close(self):
        handoff = {"id": "H-01", "owner": "test-qa", "question": "negative path covered?", "evidence": "code.txt path",
                   "status": "open", "weight": "🟢", "depends_on_for_approval": False}
        first = self.result(handoffs=[handoff])
        ledger = receipts.update_handoffs({}, first, "child-A", "round-A")
        previous = {"parent_session_id": "parent-A", "reviewer_id": "child-A", "result": first}
        with self.assertRaises(ValueError):
            self.validate(self.result(), previous=previous)
        closed = {"id": "H-01", "owner": "test-qa", "status": "reviewer_confirmed_fixed", "closure_evidence": "spec negative case inspected"}
        with self.assertRaises(ValueError):
            receipts.update_handoffs(ledger, self.result(handoffs=[closed]), "child-A", "round-B")
        qa = self.result(reviewer="test-qa", phase="qa", native_verdict="APPROVE", handoffs=[closed])
        ledger = receipts.update_handoffs(ledger, qa, "qa-child", "qa-round")
        checked = receipts.validate(self.result(), {"direction": "claude-codex-review", "reviewer": "code-quality-reviewer"},
                                    "cr", "source-A", self.native(self.result()), previous, ledger)
        self.assertTrue(checked["approved"])
        self.assertEqual("qa-child", ledger["H-01"]["closure"]["reviewer_id"])
        self.assertEqual("code.txt path", ledger["H-01"]["evidence"])

    def weighted(self, weight="🟡", **updates):
        value = {"id": "H-W", "owner": "test-qa", "question": "q", "evidence": "e", "status": "open",
                 "depends_on_for_approval": False}
        if weight is not None:
            value["weight"] = weight
        value.update(updates)
        return value

    def test_hnd1_new_handoff_requires_valid_weight(self):
        for bad in (None, "", "high", "Low", 2):
            handoff = self.weighted(bad if bad is not None else None)
            if bad is not None:
                handoff["weight"] = bad
            for check in (lambda r: receipts.update_handoffs({}, r, "child-A", "round-A"),
                          lambda r: self.validate(r)):
                with self.assertRaises(ValueError, msg=repr(bad)):
                    check(self.result(handoffs=[handoff], decision="REQUEST_CHANGES", native_verdict="L1.5_REQUEST_CHANGES"))
        ledger = receipts.update_handoffs({}, self.result(handoffs=[self.weighted("🟡中")]), "child-A", "round-A")
        self.assertEqual("🟡", ledger["H-W"]["weight"])

    def test_hnd1_weight_is_preserved_and_cannot_be_lowered_while_open(self):
        first = self.result(handoffs=[self.weighted("🟡")], decision="REQUEST_CHANGES", native_verdict="L1.5_REQUEST_CHANGES")
        ledger = receipts.update_handoffs({}, first, "child-A", "round-A")
        omitted = self.result(handoffs=[{k: v for k, v in self.weighted("🟡").items() if k != "weight"}])
        self.assertEqual("🟡", receipts.update_handoffs(ledger, omitted, "child-A", "round-B")["H-W"]["weight"])
        lowered = self.result(handoffs=[self.weighted("🟢")])
        with self.assertRaises(ValueError):
            receipts.update_handoffs(ledger, lowered, "child-A", "round-B")
        previous = {"parent_session_id": "parent-A", "reviewer_id": "child-A", "result": first}
        with self.assertRaises(ValueError):
            self.validate(lowered, previous=previous)
        raised = receipts.update_handoffs(ledger, self.result(handoffs=[self.weighted("🔴")]), "child-A", "round-B")
        self.assertEqual("🔴", raised["H-W"]["weight"])
        closed = {"id": "H-W", "owner": "test-qa", "status": "reviewer_confirmed_fixed", "closure_evidence": "inspected"}
        qa = self.result(reviewer="test-qa", phase="qa", native_verdict="APPROVE", handoffs=[closed])
        self.assertEqual("🟡", receipts.update_handoffs(ledger, qa, "qa-child", "qa-round")["H-W"]["weight"])

    def test_hnd1_yellow_or_red_open_handoff_blocks_approve_but_green_does_not(self):
        for weight in ("🟡", "🔴"):
            with self.assertRaises(ValueError, msg=weight):
                self.validate(self.result(handoffs=[self.weighted(weight)], native_verdict="L1.5_APPROVE_WITH_NOTES"))
        checked = self.validate(self.result(handoffs=[self.weighted("🟢")], native_verdict="L1.5_APPROVE_WITH_NOTES"))
        self.assertTrue(checked["approved"])
        # 台帳の重みが🟡なら、現在の結果が🟢と書いても承認できません(重い方を採ります)。
        ledger = receipts.update_handoffs({}, self.result(handoffs=[self.weighted("🟡")]), "child-A", "round-A")
        with self.assertRaises(ValueError):
            receipts.validate(self.result(handoffs=[self.weighted("🟢")]), {"direction": "claude-codex-review", "reviewer": "code-quality-reviewer"},
                              "cr", "source-A", self.native(self.result(handoffs=[self.weighted("🟢")])), None, ledger)
        # 🟡でも、実ownerが閉じた後なら承認できます。
        closed = {"id": "H-W", "owner": "test-qa", "status": "reviewer_confirmed_fixed", "closure_evidence": "inspected"}
        ledger = receipts.update_handoffs(ledger, self.result(reviewer="test-qa", phase="qa", native_verdict="APPROVE", handoffs=[closed]),
                                          "qa-child", "qa-round")
        self.assertEqual("reviewer_confirmed_fixed", ledger["H-W"]["status"])

    def test_hnd1_legacy_handoff_without_weight_is_readable_and_treated_as_yellow(self):
        legacy = {"id": "OLD-1", "owner": "test-qa", "question": "q", "evidence": "e", "status": "open",
                  "depends_on_for_approval": False, "origin_reviewer": "code-quality-reviewer", "origin_round": "r0"}
        ledger = {"OLD-1": dict(legacy)}
        restated = {k: legacy[k] for k in ("id", "owner", "status", "depends_on_for_approval")}
        result = self.result(handoffs=[restated])
        previous = {"parent_session_id": "parent-A", "reviewer_id": "child-A", "result": result}
        # 読み取りと台帳更新は成功し、台帳へ既定値は書き戻しません。
        self.assertNotIn("weight", receipts.update_handoffs(ledger, result, "child-A", "round-B")["OLD-1"])
        self.assertEqual(1, len(receipts.handoff_rows(previous["result"])))
        # 実効値は🟡のため、承認は止まります。
        with self.assertRaises(ValueError):
            receipts.validate(result, {"direction": "claude-codex-review", "reviewer": "code-quality-reviewer"}, "cr", "source-A",
                              self.native(result), previous, ledger)
        # 旧行を🟢へ下げるのも拒否し、🟡以上の明示は受け付けます。
        with self.assertRaises(ValueError):
            receipts.update_handoffs(ledger, self.result(handoffs=[{**restated, "weight": "🟢"}]), "child-A", "round-B")
        self.assertEqual("🔴", receipts.update_handoffs(ledger, self.result(handoffs=[{**restated, "weight": "🔴"}]), "child-A", "round-B")["OLD-1"]["weight"])

    def test_phase_assignments_include_transport_and_qa_role(self):
        root = Path(launcher.__file__).resolve().parents[1]
        for filename in ("claude-review.yml", "codex-review.yml"):
            text = (root / ".codex/workflows" / filename).read_text()
            common = text.split("    phase_common: ", 1)[1].splitlines()[0]
            self.assertIn("MD依頼と判定欄の機械照合", common)
            self.assertIn("    ci: phase_common", text)

    def test_fake_codex_rounds_use_short_md_prompt_and_persist_validated_state(self):
        self.init("--direction", "claude-codex-review")
        fakebin = self.temp / "bin"
        fakebin.mkdir()
        fake = fakebin / "codex"
        fake.write_text('''#!/usr/bin/python3
import json,re,sys
from pathlib import Path
if "mcp" in sys.argv:
    print("[]")
    sys.exit(0)
prompt=sys.stdin.read()
md=Path(prompt.split(" を基に",1)[0])
request=json.loads(re.search(r"```json\\n(.*?)\\n```",md.read_text(),re.S)[1])
snapshot=json.loads(Path(request["snapshot_file"]).read_text())
again=request["review_kind"]=="rereview"
parent="parent-"+request["round_id"]
child="child-"+request["round_id"]
result={"workflow_id":"claude-codex-review","phase":request["phase"],"reviewer":request["reviewer"],"snapshot_id":snapshot["snapshot_id"],"native_verdict":"L1.5_APPROVE" if again else "L1.5_REQUEST_CHANGES","coverage":"COMPLETE","decision":"APPROVE" if again else "REQUEST_CHANGES","open_item_ids":[] if again else ["CR-01"],"questions":[],"handoffs":[],"invocation_evidence":{"parent_session_id":parent,"reviewer_id":child,"platform":"Codex","model":"fake-fixture-model"}}
if again:
    result["invocation_evidence"]["finding_updates"]={"CR-01":{"status":"reviewer_confirmed_fixed","evidence":"code.txt fix"}}
body="FAKE PROVIDER FIXTURE\\n```workflow-result\\n"+json.dumps(result)+"\\n```\\n"
Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(body)
print(json.dumps({"type":"thread.started","thread_id":parent}))
print(json.dumps({"type":"item.completed","item":{"type":"collab_tool_call","tool":"spawn_agent","status":"completed","receiver_thread_ids":[child],"agents_states":{child:{"status":"completed","message":body}}}}))
''')
        fake.chmod(0o700)
        env = {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"]}
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        state = json.loads((self.run / "state.json").read_text())
        self.assertEqual("REVIEWED", state["phases"]["cr"]["status"])
        original_round = state["phases"]["cr"]["latest_attempt"]
        (self.project / "code.txt").write_text("fixed\n")
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        state = json.loads((self.run / "state.json").read_text())
        self.assertEqual("APPROVED", state["phases"]["cr"]["status"])
        current_round = self.run / state["phases"]["cr"]["latest_attempt"]
        self.assertTrue((current_round / "request.txt").read_text().startswith(f"{self.run / 'review.md'} を基に再レビューしてください。\n<<BRIEFING sha256="))
        self.assertEqual(["code.txt"], json.loads((current_round / "comparison.json").read_text())["changed_paths"])
        self.assertIn("-working", review.frozen_diff(current_round, "delta"))
        context = json.loads((current_round / "context.json").read_text())
        self.assertEqual(["current"], context["request"]["reading_plan"]["required_sections"])
        self.assertEqual(["previous_result", "summary"], context["request"]["reading_plan"]["inlined_sections"])
        self.assertFalse(context["request"]["reading_plan"]["retained_owner_context"])
        self.assertIn("User request:", review.review_context(current_round, "summary")["text"])
        self.assertIn("CR-01", review.review_context(current_round, "previous_result")["text"])
        journal = (self.run / "review.md").read_text()
        self.assertIn(original_round, journal)
        self.assertNotIn('"argv"', journal)

    FAKE_CLAUDE = '''#!/usr/bin/python3
import json,os,re,sys
from pathlib import Path
prompt=sys.stdin.read()
if os.environ.get("FAKE_ARGV"):
    Path(os.environ["FAKE_ARGV"]).write_text(json.dumps(sys.argv))
if os.environ.get("FAKE_MARKER"):
    Path(os.environ["FAKE_MARKER"]).write_text("started")
md=Path(prompt.split(" を基に",1)[0])
request=json.loads(re.search(r"```json\\n(.*?)\\n```",md.read_text(),re.S)[1])
snapshot=json.loads(Path(request["snapshot_file"]).read_text())
handoff={"id":"E2E-H1","owner":"e2e-qa","question":"full original question","evidence":"full original evidence","status":"open","weight":"🟢","depends_on_for_approval":False}
def block(handoffs):
    result={"workflow_id":"codex-claude-review","phase":request["phase"],"reviewer":request["reviewer"],"snapshot_id":snapshot["snapshot_id"],"native_verdict":"L1.5_REQUEST_CHANGES","coverage":"COMPLETE","decision":"REQUEST_CHANGES","open_item_ids":["CR-01"],"questions":[],"handoffs":handoffs,"invocation_evidence":{"platform":"Claude Code","model":"fake-fixture-model","note":"child wrote this"}}
    return "```workflow-result\\n"+json.dumps(result)+"\\n```\\n"
mode=os.environ["FAKE_MODE"]
child_text="CHILD FINAL\\n"+block([handoff]) if mode!="both_lack" else "CHILD FINAL without block"
parent_text={"paraphrase":"I summarise: approved with no block.","both_lack":"paraphrase","altered":"PARENT\\n"+block([{**handoff,"question":"short"}]),"ok":"PARENT\\n"+block([handoff])}[mode]
child=Path(os.environ["FAKE_CHILD"])
child.parent.mkdir(parents=True,exist_ok=True)
with child.open("a") as f: f.write(json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":child_text}]}})+"\\n")
print(json.dumps({"message":{"content":[{"type":"tool_use","id":"c1","name":"Agent","input":{"subagent_type":"code-quality-reviewer"}}]}}))
print(json.dumps({"message":{"content":[{"type":"tool_result","tool_use_id":"c1"}]},"toolUseResult":{"agentId":"child-X"}}))
print(json.dumps({"type":"result","session_id":"parent-X","result":parent_text}))
'''

    def claude_round(self, mode, marker=None, code=None):
        if not (self.run / "state.json").exists() and not (self.run / "review.md").exists():
            self.init()
        fakebin = self.temp / "bin"
        fakebin.mkdir(exist_ok=True)
        fake = fakebin / "claude"
        fake.write_text(self.FAKE_CLAUDE)
        fake.chmod(0o700)
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.temp / "cfg")
        self.addCleanup(os.environ.pop, "CLAUDE_CONFIG_DIR", None)
        transcript = receipts.claude_transcript(self.project, "parent-X")
        env = {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"], "CLAUDE_CONFIG_DIR": str(self.temp / "cfg"),
               "FAKE_MODE": mode, "FAKE_CHILD": str(transcript.with_suffix("") / "subagents/agent-child-X.jsonl")}
        if marker:
            env["FAKE_MARKER"] = str(marker)
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.touch()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2 if code is None else code, env=env)
        records = sorted(self.run.glob("*/execution.json"), key=lambda p: p.stat().st_mtime_ns)
        return env, records, json.loads(records[-1].read_text()) if records else None

    def test_parent_paraphrase_uses_child_final_message_verbatim(self):
        _, records, meta = self.claude_round("paraphrase", code=0)
        self.assertEqual("child_verbatim", meta["result_source"])
        self.assertEqual("REVIEWED", meta["status"])
        round_dir = records[-1].parent
        self.assertTrue((round_dir / "result.md").read_text().startswith("CHILD FINAL"))
        self.assertIn("I summarise", (round_dir / "parent-result.md").read_text())
        state = json.loads((self.run / "state.json").read_text())
        self.assertEqual("note", next(k for k in state["phases"]["cr"]["last_valid"]["result"]["invocation_evidence"] if k == "note"))
        self.assertEqual("full original question", state["handoffs"]["E2E-H1"]["question"])

    def test_altered_parent_handoff_is_replaced_by_child_verbatim(self):
        _, _, meta = self.claude_round("altered", code=0)
        self.assertEqual("child_verbatim", meta["result_source"])
        state = json.loads((self.run / "state.json").read_text())
        self.assertEqual("full original question", state["handoffs"]["E2E-H1"]["question"])

    def test_parent_with_valid_block_stays_parent_sourced(self):
        _, _, meta = self.claude_round("ok", code=0)
        self.assertEqual("parent", meta["result_source"])

    def test_both_without_block_stay_blocked(self):
        _, _, meta = self.claude_round("both_lack")
        self.assertEqual("BLOCKED", meta["status"])
        self.assertIn("workflow-result", meta["validation_error"])
        self.assertNotEqual("child_verbatim", meta.get("result_source"))

    def test_foreign_child_resume_starts_no_model(self):
        env, records, _ = self.claude_round("ok", code=0)
        state_file = self.run / "state.json"
        state = json.loads(state_file.read_text())
        owner = state["phases"]["cr"]["owner"]
        state["phases"]["qa"] = {"status": "REVIEWED", "owner": dict(owner)}
        state_file.write_text(json.dumps(state))
        marker = self.temp / "started"
        env["FAKE_MARKER"] = str(marker)
        stopped = self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2, env=env)
        self.assertIn("別phase", stopped.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(len(records), len(list(self.run.glob("*/execution.json"))))

    def second_round(self, gap, threshold=300, strip=False, tamper=False):
        """1回目後、前回終了からgap秒後に同phaseを再実行します（プロセス内、時計は差し替え）。"""
        import datetime
        env, records, _ = self.claude_round("ok", code=0)
        first = records[-1]
        meta = json.loads(first.read_text())
        self.assertIn("finished_at", meta)
        if strip:
            del meta["finished_at"]
        else:
            meta["finished_at"] = "2026-01-01T00:00:00+00:00"
        first.write_text(json.dumps(meta))
        if tamper:
            state = json.loads((self.run / "state.json").read_text())
            state["phases"]["cr"]["owner"]["tool_contract_sha256"] = "changed"
            (self.run / "state.json").write_text(json.dumps(state))
        argv_file = self.temp / "argv.json"
        env["FAKE_ARGV"] = str(argv_file)
        now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=gap)
        args = ["start_md_review.py", "--run-dir", str(self.run), "--phase", "cr", "--fresh-after-seconds", str(threshold)]
        with patch.dict(os.environ, env), patch.object(sys, "argv", args), patch.object(launcher, "utc_now", lambda: now):
            code = launcher.main()
        newest = max((p for p in self.run.glob("*/execution.json") if p != first), key=lambda p: p.stat().st_mtime_ns, default=None)
        argv = json.loads(argv_file.read_text()) if argv_file.exists() else None
        return code, argv, json.loads(newest.read_text()), newest.parent

    def test_gap_over_threshold_starts_fresh_owner_without_inheriting_approval(self):
        code, argv, meta, round_dir = self.second_round(301)
        self.assertEqual(0, code)
        self.assertNotIn("--resume", argv)
        self.assertEqual("fresh_after_ttl", meta["owner_continuity"]["mode"])
        self.assertEqual(301.0, meta["owner_continuity"]["gap_seconds"])
        ids = {"parent_session_id": "parent-X", "reviewer_id": "child-X"}
        self.assertEqual(ids, meta["owner_continuity"]["previous_owner"])
        self.assertEqual(ids, meta["owner_continuity"]["new_owner"])
        self.assertFalse(meta["resume"])
        briefing = (round_dir / "briefing.md").read_text()
        for name in ("summary", "previous_result"):
            self.assertIn(f"<<SECTION {name} ", briefing)
        self.assertIn("CR-01", briefing)
        self.assertIn(launcher.FRESH_OWNER_NOTICE, briefing)
        context = json.loads((round_dir / "context.json").read_text())
        self.assertFalse(context["request"]["reading_plan"]["retained_owner_context"])
        self.assertEqual("fresh_after_ttl", context["request"]["owner_continuity"]["mode"])
        phase = json.loads((self.run / "state.json").read_text())["phases"]["cr"]
        self.assertEqual(ids, phase["previous_owner"])
        self.assertEqual([ids], phase["previous_owners"])
        self.assertEqual(["CR-01"], phase["last_valid"]["result"]["open_item_ids"])
        self.assertIn("fresh_after_ttl", (self.run / "review.md").read_text())

    def test_gap_within_threshold_resumes_as_before(self):
        code, argv, meta, round_dir = self.second_round(300)
        self.assertEqual(0, code)
        self.assertEqual("parent-X", argv[argv.index("--resume") + 1])
        self.assertEqual("resumed", meta["owner_continuity"]["mode"])
        context = json.loads((round_dir / "context.json").read_text())
        self.assertTrue(context["request"]["reading_plan"]["retained_owner_context"])
        self.assertNotIn(launcher.FRESH_OWNER_NOTICE, (round_dir / "briefing.md").read_text())

    def test_unknown_timestamp_resumes_without_guessing(self):
        code, argv, meta, _ = self.second_round(99999, strip=True)
        self.assertIn("--resume", argv)
        self.assertEqual("resumed_gap_unknown", meta["owner_continuity"]["mode"])
        self.assertIsNone(meta["owner_continuity"]["gap_seconds"])

    def test_threshold_zero_disables_fresh_owner(self):
        code, argv, meta, _ = self.second_round(99999, threshold=0)
        self.assertIn("--resume", argv)
        self.assertEqual("resumed_ttl_disabled", meta["owner_continuity"]["mode"])

    def test_preflight_mismatch_stays_blocked_even_when_gap_is_long(self):
        marker = self.temp / "never"
        try:
            self.second_round(99999, tamper=True)
        except Exception:
            pass
        self.assertFalse((self.temp / "argv.json").exists())
        self.assertEqual(1, len(list(self.run.glob("*/execution.json"))))

    def test_print_briefing_reports_continuity_without_writing(self):
        import datetime
        self.claude_round("ok", code=0)
        first = next(self.run.glob("*/execution.json"))
        meta = json.loads(first.read_text())
        meta["finished_at"] = "2026-01-01T00:00:00+00:00"
        first.write_text(json.dumps(meta))
        now = datetime.datetime(2026, 1, 1, 0, 20, tzinfo=datetime.timezone.utc)
        args = ["start_md_review.py", "--run-dir", str(self.run), "--phase", "cr", "--print-briefing", "--fresh-after-seconds", "300"]
        import io
        out = io.StringIO()
        with patch.object(sys, "argv", args), patch.object(launcher, "utc_now", lambda: now), patch("sys.stdout", out):
            launcher.main()
        report = json.loads(out.getvalue().rsplit("---\n", 1)[1])
        self.assertEqual("fresh_after_ttl", report["owner_continuity"]["mode"])
        self.assertIn(launcher.FRESH_OWNER_NOTICE, out.getvalue())
        self.assertEqual(1, len(list(self.run.glob("*/execution.json"))))


if __name__ == "__main__":
    unittest.main()
