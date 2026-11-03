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
        rows = [{"type": "result", "session_id": "parent-A"},
                {"message": {"content": [{"type": "tool_use", "id": "call-A", "name": "Agent", "input": {"subagent_type": "code-quality-reviewer"}}]}},
                {"message": {"content": [{"type": "tool_result", "tool_use_id": "call-A"}]}, "toolUseResult": {"agentId": "child-A"}}]
        native = receipts.identities(rows, "claude", "code-quality-reviewer")
        self.assertEqual({"child-A": "code-quality-reviewer"}, native["children"])
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
                   "status": "open", "depends_on_for_approval": False}
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
        self.assertEqual(f"{self.run / 'review.md'} を基に再レビューしてください。\n", (current_round / "request.txt").read_text())
        self.assertEqual(["code.txt"], json.loads((current_round / "comparison.json").read_text())["changed_paths"])
        self.assertIn("-working", review.frozen_diff(current_round, "delta"))
        journal = (self.run / "review.md").read_text()
        self.assertIn(original_round, journal)
        self.assertNotIn('"argv"', journal)


if __name__ == "__main__":
    unittest.main()
