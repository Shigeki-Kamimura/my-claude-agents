"""共通MDだけを使い、前回確認後の必要欄を漏れなく渡すことを確認します。"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
import uuid

import test_md_review as fixtures

launcher, review = fixtures.launcher, fixtures.review
receipts = launcher.receipts
ROOT = fixtures.ROOT


class MDReviewContextTests(unittest.TestCase):
    setUp = fixtures.MDReviewTests.setUp
    git = fixtures.MDReviewTests.git
    cli = fixtures.MDReviewTests.cli
    init = fixtures.MDReviewTests.init

    def stdin_cli(self, text, *args, code=0):
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/md_review.py"), *map(str, args)],
                                input=text, text=True, capture_output=True)
        self.assertEqual(code, result.returncode, result.stderr)
        return result

    def note(self, text):
        return self.stdin_cli(text, "--run-dir", self.run, "--note-stdin")

    def context(self, phase_state, retained=False):
        config = review.load_run(self.run)[1]
        plan, sections = launcher.reading_context(self.run, config, phase_state, "cr", retained)
        target = self.run / "context-fixture"
        target.mkdir(exist_ok=True)
        review.atomic_text(target / "context.json", json.dumps({"request": {"reading_plan": plan}, "sections": sections}))
        return target, plan, sections

    def test_stdin_writes_one_request_md_without_fix_copies(self):
        self.stdin_cli("Acceptance: preserve disabled controls\n", "--project", self.project, "--base", self.base,
                       "--direction", "claude-codex-review", "--layers", "cr", "--rules", self.project / "rule.md",
                       "--summary-stdin", "--out-dir", self.run)
        self.note("CR-01 fixed; targeted verification: exit 0")
        self.assertEqual(["review.md"], [p.name for p in self.run.rglob("*.md")])
        index = json.loads((self.run / "latest-fix.json").read_text())
        self.assertNotIn("path", index)
        text = (self.run / "review.md").read_text()
        self.assertEqual(1, text.count("CR-01 fixed; targeted verification: exit 0"))
        self.assertIn("CR-01 fixed", review.journal_read(self.run, index["reference"]))

    def test_rereview_includes_all_new_updates_and_preserves_pending_ids(self):
        self.init()
        self.note("OLD_UPDATE_ALREADY_CHECKED")
        prior = review.append(self.run, "cr / previous-round", "Native result: CR-01 unresolved")
        phase = {"last_valid": {"round_id": "previous-round", "journal_reference": prior, "update_count": 1,
                                "result": {"open_item_ids": ["CR-01"]}}}
        self.note("FIRST_NEW_FIX")
        self.note("SECOND_NEW_FIX")
        target, plan, sections = self.context(phase, retained=True)
        page = review.review_context(target, "updates")
        self.assertIn("FIRST_NEW_FIX", page["text"])
        self.assertIn("SECOND_NEW_FIX", page["text"])
        self.assertNotIn("OLD_UPDATE_ALREADY_CHECKED", page["text"])
        self.assertEqual(["current", "updates"], plan["required_sections"])
        self.assertEqual(["CR-01"], plan["pending_item_ids"])
        self.assertEqual(2, plan["update_count"])
        self.assertIn("previous_result", sections)
        _, fresh, _ = self.context(phase)
        self.assertEqual(["current", "summary", "previous_result", "updates"], fresh["required_sections"])

    def test_delivery_failure_keeps_last_attempt_and_does_not_advance_update_cursor(self):
        self.init()
        prior = review.append(self.run, "cr / previous-round", "VALID_PRIOR_RESULT")
        self.note("STILL_UNREVIEWED_FIX")
        failed = review.append(self.run, "cr / blocked-round", "MISSING_JSON_DELIVERY")
        phase = {"latest_attempt": "blocked-round", "latest_reference": failed,
                 "last_valid": {"round_id": "previous-round", "journal_reference": prior, "update_count": 0}}
        target, plan, _ = self.context(phase, retained=True)
        self.assertIn("previous_attempt", plan["required_sections"])
        self.assertIn("MISSING_JSON_DELIVERY", review.review_context(target, "previous_attempt")["text"])
        self.assertIn("STILL_UNREVIEWED_FIX", review.review_context(target, "updates")["text"])

    def test_context_pages_only_selected_section_and_rejects_tampered_reference(self):
        self.init()
        self.note("PAGED_FIX_" + "x" * 25000)
        review.append(self.run, "cr / unrelated-round", "HISTORY_MUST_NOT_BE_READ")
        target, _, _ = self.context({})
        offset, pieces = 0, []
        while offset is not None:
            page = review.review_context(target, "updates", offset)
            self.assertLessEqual(len(page["text"]), 12000)
            pieces.append(page["text"])
            offset = page["next_offset"]
        self.assertIn("PAGED_FIX_", "".join(pieces))
        self.assertNotIn("HISTORY_MUST_NOT_BE_READ", "".join(pieces))
        review.current_request(self.run, {"phase": "qa", "different_header_length": "y" * 300})
        self.assertIn("PAGED_FIX_", review.review_context(target, "updates")["text"])
        p = self.run / "review.md"
        p.write_text(p.read_text().replace("PAGED_FIX_", "TAMPERED__"))
        with self.assertRaises(ValueError):
            review.review_context(target, "updates")

    def test_context_mcp_rejects_arbitrary_files_and_invalid_offsets(self):
        self.init()
        target, _, _ = self.context({})
        (target / "snapshot.json").write_text(json.dumps({"paths": [], "snapshot_id": "fixture"}))
        arguments = [{"section": "summary"}, {"section": "/etc/passwd"},
                     {"section": "current", "path": "/etc/passwd"}, {"section": "current", "offset": -1},
                     {"section": "current", "offset": True}]
        messages = [{"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": "review_context", "arguments": value}} for i, value in enumerate(arguments)]
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/md_review.py"), "--serve", str(target)],
                                input="\n".join(map(json.dumps, messages)) + "\n", text=True, capture_output=True, check=True)
        rows = list(map(json.loads, result.stdout.splitlines()))
        self.assertIn("result", rows[0])
        self.assertTrue(all("error" in row for row in rows[1:]))

    def test_legacy_run_indexes_existing_notes_without_copying_or_losing_history(self):
        self.init()
        self.note("LEGACY_FIX_ONE")
        self.note("LEGACY_FIX_TWO")
        for text in ("LEGACY_FIX_ONE", "LEGACY_FIX_TWO"):
            (self.run / ("fix-" + str(uuid.uuid4()) + ".md")).write_text(text)
        before = (self.run / "review.md").read_text()
        config = review.load_run(self.run)[1]
        del config["summary_reference"], config["updates"]
        review.atomic_text(self.run / "run.json", json.dumps(config))
        review.journal_index(self.run, config)
        self.assertEqual(before, (self.run / "review.md").read_text())
        self.assertEqual(2, len(config["updates"]))
        _, plan, _ = self.context({"last_valid": {"round_id": "legacy", "journal_reference": config["summary_reference"]}})
        self.assertEqual(2, plan["update_count"])

    def test_new_summary_keeps_quoted_host_headings_and_later_acceptance(self):
        text = "Before\n\n```text\n\n## cr / 00000000-0000-0000-0000-000000000000\n\nExample\n```\nAcceptance: never omit this\n"
        self.stdin_cli(text, "--project", self.project, "--base", self.base, "--direction", "claude-codex-review",
                       "--layers", "cr", "--rules", self.project / "rule.md", "--summary-stdin", "--out-dir", self.run)
        target, _, _ = self.context({})
        self.assertIn("Acceptance: never omit this", review.review_context(target, "summary")["text"])
        self.assertEqual([], review.load_run(self.run)[1]["updates"])

    def test_legacy_ambiguous_or_missing_host_evidence_stops_instead_of_cutting_summary(self):
        self.init()
        self.note("LEGACY_FIX")
        config = review.load_run(self.run)[1]
        del config["summary_reference"], config["updates"]
        # 旧ホストの原本がなければ見出しだけでは移行しません。
        with self.assertRaises(ValueError):
            review.journal_index(self.run, config)
        (self.run / ("fix-" + str(uuid.uuid4()) + ".md")).write_text("LEGACY_FIX")
        config = review.load_run(self.run)[1]
        del config["summary_reference"], config["updates"]
        body = review.journal_body(self.run)
        entry = body[body.index("\n\n## Implementation update\n\n"):]
        with (self.run / "review.md").open("a") as stream:
            stream.write(entry)
        with self.assertRaises(ValueError):
            review.journal_index(self.run, config)

    def test_legacy_uses_actual_result_boundary_after_quoted_example(self):
        text = "```text\n\n## cr / 00000000-0000-0000-0000-000000000000\n\nExample\n```\nAcceptance: retained\n"
        self.summary.write_text(text)
        self.init()
        round_id = str(uuid.uuid4())
        target = self.run / round_id
        target.mkdir()
        meta = {"phase": "cr", "artifacts": str(target), "status": "REVIEWED"}
        (target / "execution.json").write_text(json.dumps(meta))
        (target / "result.md").write_text("NATIVE_REAL_RESULT\n")
        review.append(self.run, "cr / " + round_id, "```json\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n\nNATIVE_REAL_RESULT\n")
        config = review.load_run(self.run)[1]
        del config["summary_reference"], config["updates"]
        review.journal_index(self.run, config)
        self.assertIn("Acceptance: retained", review.journal_read(self.run, config["summary_reference"]))
        reference = review.result_reference(self.run, {"round_id": round_id}, "cr", config)
        self.assertIn("NATIVE_REAL_RESULT", review.journal_read(self.run, reference))
        self.note("NEW_MANAGED_FIX_AFTER_LEGACY_MIGRATION")
        previous = {"last_valid": {"round_id": round_id, "result": {"open_item_ids": ["CR-01"]}}}
        context, plan, _ = self.context(previous)
        self.assertIn("previous_result", plan["required_sections"])
        self.assertIn("NATIVE_REAL_RESULT", review.review_context(context, "previous_result")["text"])
        self.assertIn("NEW_MANAGED_FIX_AFTER_LEGACY_MIGRATION", review.review_context(context, "updates")["text"])

    def test_both_platform_rules_prohibit_extra_request_mds(self):
        for path in ("AGENTS.md", ".codex/AGENTS.md", ".claude/CLAUDE.md", ".claude-company/CLAUDE.md"):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn("do not create per-layer, per-round or delivery-correction request MDs", text)
                self.assertIn("--summary-stdin", text)
                self.assertIn("md_review.review_context", text)

    def fake_claude(self):
        fakebin = self.temp / "bin"
        fakebin.mkdir()
        fake = fakebin / "claude"
        fake.write_text(r'''#!/usr/bin/python3
import json,os,re,sys
from pathlib import Path
prompt=sys.stdin.read()
md=Path(prompt.split(" を基に",1)[0])
request=json.loads(re.search(r"```json\n(.*?)\n```",md.read_text(),re.S)[1])
again="--resume" in sys.argv
parent="parent-A"
child="child-A"
result={"workflow_id":"codex-claude-review","phase":"l1_5","reviewer":"code-quality-reviewer","snapshot_id":json.loads(Path(request["snapshot_file"]).read_text())["snapshot_id"],"native_verdict":"L1.5_APPROVE" if again else "L1.5_REQUEST_CHANGES","coverage":"COMPLETE","decision":"APPROVE" if again else "REQUEST_CHANGES","open_item_ids":[] if again else ["CR-01"],"questions":[],"handoffs":[],"invocation_evidence":{"platform":"Claude Code","model":"fake-fixture-model"}}
if again:
    result["invocation_evidence"]["finding_updates"]={"CR-01":{"status":"reviewer_confirmed_fixed","evidence":"code.txt fix"}}
body="NATIVE_FIXTURE\n```workflow-result\n"+json.dumps(result)+"\n```\n"
if os.environ.get("FIXTURE_MALFORMED"):
    body="MISSING_NATIVE_JSON"
project=re.sub(r"[^A-Za-z0-9]","-",request["project"])
transcript=Path(os.environ["CLAUDE_CONFIG_DIR"])/"projects"/project/(parent+".jsonl")
transcript.parent.mkdir(parents=True,exist_ok=True)
children=transcript.with_suffix("")/"subagents"
children.mkdir(parents=True,exist_ok=True)
call="call-resume" if again else "call-initial"
tool="SendMessage" if again else "Agent"
input={"to":child} if again else {"subagent_type":"code-quality-reviewer"}
native={"success":True,"resumedAgentId":child} if again else {"agentId":child}
rows=[{"message":{"content":[{"type":"tool_use","id":call,"name":tool,"input":input}]}},{"message":{"content":[{"type":"tool_result","tool_use_id":call}]},"toolUseResult":native}]
with transcript.open("a") as f:
    for row in rows:
        f.write(json.dumps(row)+"\n")
with (children/("agent-"+child+".jsonl")).open("a") as f:
    f.write(json.dumps({"type":"assistant","message":{"content":[{"type":"text","text":body}]}})+"\n")
print(json.dumps({"type":"result","session_id":parent,"result":body}))
''')
        fake.chmod(0o700)
        return {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"],
                "CLAUDE_CONFIG_DIR": str(self.temp / "claude-config")}

    def test_claude_same_owner_round_reads_new_updates_without_repeating_history(self):
        self.init()
        env = self.fake_claude()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        self.note("NEW_FIX_ONE")
        self.note("NEW_FIX_TWO")
        (self.project / "code.txt").write_text("fixed\n")
        response = self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        self.assertNotIn('"argv"', response.stdout)
        state = json.loads((self.run / "state.json").read_text())
        phase = state["phases"]["cr"]
        self.assertEqual("APPROVED", phase["status"])
        target = self.run / phase["latest_attempt"]
        context = json.loads((target / "context.json").read_text())
        request = context["request"]
        self.assertEqual(["current"], request["reading_plan"]["required_sections"])
        self.assertEqual(["updates"], request["reading_plan"]["inlined_sections"])
        self.assertEqual(["delta"], request["required_diff_views"])
        self.assertEqual(["CR-01"], request["reading_plan"]["pending_item_ids"])
        self.assertEqual(2, request["reading_plan"]["update_count"])
        self.assertIn("NEW_FIX_ONE", review.review_context(target, "updates")["text"])
        self.assertIn("NEW_FIX_TWO", review.review_context(target, "updates")["text"])
        self.assertNotIn("NATIVE_FIXTURE", review.review_context(target, "updates")["text"])
        header = json.loads(re.search(r"```json\n(.*?)\n```", (self.run / "review.md").read_text(), re.S)[1])
        self.assertEqual({"parent_session_id": "parent-A", "reviewer_id": "child-A"}, header["current_owner"])

    def briefing(self, phase_state, retained=False, cap=60000, handoffs=None):
        config = review.load_run(self.run)[1]
        plan, sections = launcher.reading_context(self.run, config, phase_state, "cr", retained)
        request = {"phase": "l1_5", "handoff_index": handoffs or {}}
        text, report = launcher.build_briefing(self.run, request, plan, sections, cap)
        return text, report, plan

    def prior_phase(self, update_count=1):
        prior = review.append(self.run, "cr / previous-round", "PRIOR_RESULT_BODY CR-01 full finding text")
        return {"last_valid": {"round_id": "previous-round", "journal_reference": prior, "update_count": update_count,
                               "result": {"open_item_ids": ["CR-01"]}}}

    def test_briefing_initial_round_has_identity_and_summary_without_previous_result(self):
        self.init()
        text, report, plan = self.briefing({})
        self.assertIn("## Identity", text)
        self.assertIn("User request: review cr only", text)
        self.assertNotIn("<<SECTION previous_result", text)
        self.assertEqual(["summary"], report["inlined"])
        self.assertEqual(["current"], plan["required_sections"])
        self.assertEqual(report["sha256"], review.digest(text.encode()))

    def test_briefing_rereview_has_previous_result_open_ids_handoffs_and_updates_verbatim(self):
        self.init()
        self.note("OLD_UPDATE")
        phase = self.prior_phase(update_count=1)
        self.note("NEW_FIX_VERBATIM")
        handoff = {"E2E-H1": {"id": "E2E-H1", "question": "full original question", "evidence": "full original evidence", "status": "open"}}
        text, report, plan = self.briefing(phase, handoffs=handoff)
        self.assertIn("PRIOR_RESULT_BODY CR-01 full finding text", text)
        self.assertIn('["CR-01"]', text)
        self.assertIn("full original question", text)
        self.assertIn("NEW_FIX_VERBATIM", text)
        self.assertNotIn("OLD_UPDATE", text)
        self.assertEqual(["previous_result", "updates", "summary"], report["inlined"])
        self.assertEqual(["current"], plan["required_sections"])
        self.assertEqual(["CR-01"], plan["pending_item_ids"])

    def test_briefing_retained_owner_omits_summary_and_previous_result(self):
        self.init()
        phase = self.prior_phase(update_count=0)
        self.note("FIX_FOR_RETAINED")
        text, report, plan = self.briefing(phase, retained=True)
        self.assertIn("FIX_FOR_RETAINED", text)
        self.assertNotIn("PRIOR_RESULT_BODY", text)
        self.assertNotIn("User request: review cr only", text)
        self.assertEqual(["updates"], report["inlined"])
        self.assertEqual(["CR-01"], plan["pending_item_ids"])

    def test_briefing_cap_overflow_keeps_section_required_and_lists_not_inlined(self):
        self.init()
        phase = self.prior_phase(update_count=0)
        self.note("BIG_UPDATE_" + "x" * 5000)
        base_text, _, _ = self.briefing(phase, cap=10**6)
        head = base_text.index("## Identity")
        text, report, plan = self.briefing(phase, cap=head + 2500)
        self.assertIn("updates", report["not_inlined"])
        self.assertIn("updates: ", text)
        self.assertIn("NOT_INLINED", text)
        self.assertNotIn("BIG_UPDATE_", text)
        self.assertIn("updates", plan["required_sections"])
        self.assertNotIn("updates", plan["inlined_sections"])
        self.assertIn("previous_result", plan["inlined_sections"])

    def test_prompt_carries_briefing_markers_and_hash_and_costs_are_recorded(self):
        self.init()
        env = self.fake_claude()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        state = json.loads((self.run / "state.json").read_text())
        target = self.run / state["phases"]["cr"]["latest_attempt"]
        briefing = (target / "briefing.md").read_text()
        digest = review.digest(briefing.encode())
        prompt = (target / "request.txt").read_text()
        self.assertTrue(prompt.startswith(f"{self.run / 'review.md'} を基にレビューしてください。\n<<BRIEFING sha256={digest}>>\n"))
        self.assertIn("<<END BRIEFING>>\n", prompt)
        self.assertTrue(prompt.rstrip().endswith("子の最終メッセージも変えずに返してください。"))
        self.assertIn(briefing, prompt)
        context = json.loads((target / "context.json").read_text())
        self.assertEqual(digest, context["briefing"]["sha256"])
        self.assertEqual(len(briefing), context["briefing"]["chars"])
        self.assertEqual(digest, context["request"]["reading_plan"]["briefing_sha256"])
        execution = json.loads((target / "execution.json").read_text())
        self.assertEqual(context["briefing"], execution["briefing"])
        self.assertNotIn("<<BRIEFING", (self.run / "review.md").read_text())

    def test_child_dispatch_block_has_marker_skeleton_and_no_prefilled_verdict(self):
        self.init()
        env = self.fake_claude()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        state = json.loads((self.run / "state.json").read_text())
        target = self.run / state["phases"]["cr"]["latest_attempt"]
        prompt = (target / "request.txt").read_text()
        context = json.loads((target / "context.json").read_text())
        found = re.search(r"<<CHILD_DISPATCH sha256=([0-9a-f]+)>>\n(.*?)\n<<END CHILD_DISPATCH>>", prompt, re.S)
        self.assertTrue(found)
        sha, body = found.groups()
        self.assertEqual(sha, review.digest(body.encode()))
        self.assertEqual(sha, context["briefing"]["child_dispatch_sha256"])
        self.assertEqual(sha, json.loads((target / "execution.json").read_text())["briefing"]["child_dispatch_sha256"])
        self.assertTrue(body.startswith("Workflow: codex-claude-review / phase l1_5 / review_kind initial / round_id " + target.name))
        self.assertIn(str(self.run / "review.md"), body)
        fence = re.search(r"```workflow-result\n(.*?)\n```", body, re.S)
        skeleton = json.loads(fence[1])
        self.assertEqual(set(receipts.FIELDS), set(skeleton))
        self.assertEqual("l1_5", skeleton["phase"])
        for key in ("native_verdict", "coverage", "decision"):
            self.assertTrue(skeleton[key].startswith("<"))
        self.assertEqual([], skeleton["open_item_ids"])
        self.assertIn("<<CHILD_DISPATCH", prompt.split("<<END BRIEFING>>")[0])
        self.assertIn("一字も変えず子のpromptの先頭へそのまま置いてください", prompt.split("<<END BRIEFING>>")[1])

    def test_small_cap_option_leaves_sections_required_in_real_round(self):
        self.init()
        env = self.fake_claude()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", "--briefing-max-chars", "1", env=env)
        state = json.loads((self.run / "state.json").read_text())
        context = json.loads((self.run / state["phases"]["cr"]["latest_attempt"] / "context.json").read_text())
        plan = context["request"]["reading_plan"]
        self.assertEqual(["current", "summary"], plan["required_sections"])
        self.assertEqual(["summary"], plan["not_inlined_sections"])

    def test_print_briefing_writes_nothing_and_starts_no_model(self):
        self.init()
        env = self.fake_claude()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", env=env)
        self.note("UNREVIEWED_FIX")

        def tree():
            return {str(p.relative_to(self.run)): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
                    for p in sorted(self.run.rglob("*"))}
        before = tree()
        empty = self.temp / "empty-bin"
        empty.mkdir()
        result = self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", "--print-briefing",
                          env={"PATH": str(empty)})
        self.assertEqual(before, tree())
        self.assertIn("UNREVIEWED_FIX", result.stdout)
        report = json.loads(result.stdout.rsplit("---\n", 1)[1])
        self.assertIn("updates", report["inlined"])
        self.assertIn("<<CHILD_DISPATCH sha256=" + report["child_dispatch_sha256"], result.stdout)
        self.assertGreater(report["review_md_chars"], report["chars"] - report["child_dispatch_chars"] - 1)

    def test_print_briefing_without_index_exits_2(self):
        self.init()
        config = review.load_run(self.run)[1]
        del config["summary_reference"], config["updates"]
        review.atomic_text(self.run / "run.json", json.dumps(config))
        result = self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", "--print-briefing", code=2)
        self.assertIn("索引", result.stderr)


    def test_invalid_native_result_still_saves_actual_owner_ids_in_single_md(self):
        self.init()
        env = {**self.fake_claude(), "FIXTURE_MALFORMED": "1"}
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2, env=env)
        header = json.loads(re.search(r"```json\n(.*?)\n```", (self.run / "review.md").read_text(), re.S)[1])
        self.assertEqual({"parent_session_id": "parent-A", "reviewer_id": "child-A"}, header["current_owner"])
        state = json.loads((self.run / "state.json").read_text())
        self.assertEqual("BLOCKED", state["phases"]["cr"]["status"])
        self.assertNotIn("last_valid", state["phases"]["cr"])


if __name__ == "__main__":
    unittest.main()
