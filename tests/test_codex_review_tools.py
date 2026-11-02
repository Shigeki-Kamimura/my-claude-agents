"""読み込み上限と、応答単位の集計・入力保護を確認します。"""
import json
import hashlib
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
STAMP = "2026-11-02T01:00:00Z"


class ReviewToolsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.log = self.root / "parent.jsonl"

    def cli(self, script, *args, code=0):
        result = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / script),
                                 *map(str, args)], capture_output=True, text=True)
        self.assertEqual(code, result.returncode, result.stderr)
        return result

    def write(self, *rows):
        self.log.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def usage(self, response_id="r1", **changes):
        timestamp = changes.pop("timestamp", STAMP)
        usage = {"input_tokens": 100, "cached_input_tokens": 40, "cache_write_input_tokens": 0,
                 "output_tokens": 20, "reasoning_output_tokens": 5, "total_tokens": 120}
        usage.update(changes)
        return {"type": "token_usage_record", "timestamp": timestamp,
                "payload": {"response_id": response_id, "usage": usage,
                            "thread_token_usage": {"total_tokens": 9999}}}

    def event(self, kind, **fields):
        return {"type": "event_msg", "timestamp": STAMP, "payload": {"type": kind, **fields}}

    def message(self, text, phase="final", role="assistant"):
        return {"type": "response_item", "timestamp": STAMP, "payload": {
            "type": "message", "role": role, "phase": phase,
            "content": [{"type": "output_text", "text": text}]}}

    def summary(self, *args):
        return json.loads(self.cli("summarize_codex_session.py", "--parent", self.log, *args).stdout)

    def test_deduplicates_responses_and_ignores_lagging_event_totals(self):
        usage = self.usage()
        self.write(usage, usage, self.event("token_count", info={"total_token_usage": {
            "input_tokens": 999, "total_tokens": 999}}), self.message("private commentary", "commentary"),
            {"type": "response_item", "timestamp": STAMP, "payload": {"type": "function_call"}},
            {"type": "response_item", "timestamp": STAMP, "payload": {"type": "custom_tool_call"}})
        value = self.summary()
        expected = {key: usage["payload"]["usage"][key] for key in ("input_tokens", "cached_input_tokens", "output_tokens",
                    "reasoning_output_tokens", "total_tokens")}
        expected["uncached_input_tokens"] = 60
        for key, count in expected.items():
            self.assertEqual(count, value["sources"]["parent"]["tokens"][key])
            self.assertEqual(count, value["combined_tokens"][key])
        self.assertEqual(1, value["sources"]["parent"]["model_responses"])
        self.assertEqual(2, sum(value["sources"]["parent"]["top_level_tool_calls"].values()))
        self.assertIsNone(value["actual_cost"])
        self.assertNotIn("private commentary", json.dumps(value))

    def test_missing_authoritative_usage_stays_unavailable_in_combined_summary(self):
        self.write(self.event("token_count", info={"total_token_usage": {"total_tokens": 999}}))
        child = self.root / "child.jsonl"
        child.write_text(json.dumps(self.usage()) + "\n", encoding="utf-8")
        value = self.summary("--child", f"qa={child}")
        self.assertIsNone(value["sources"]["parent"]["tokens"])
        self.assertEqual("NOT_AVAILABLE", value["sources"]["parent"]["status"])
        self.assertIsNone(value["combined_tokens"])
        self.assertEqual(120, value["sources"]["qa"]["tokens"]["total_tokens"])

    def test_final_message_uses_task_complete_then_only_final_assistant_fallback(self):
        self.write(self.usage(), self.message("final answer"), self.message("analysis body", "analysis"),
                   self.message("user body", role="user"))
        self.assertEqual("final answer", self.summary()["sources"]["parent"]["final_message"])
        with self.log.open("a", encoding="utf-8") as stream:
            for row in (self.event("task_complete", last_agent_message="completed first"),
                        self.event("task_complete", last_agent_message="completed latest"),
                        self.message("later fallback")):
                stream.write(json.dumps(row) + "\n")
        self.assertEqual("completed latest", self.summary()["sources"]["parent"]["final_message"])

    def test_malformed_tail_preserves_evidence_and_reports_partial(self):
        self.write(self.usage())
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write('{"incomplete":')
        value = self.summary()["sources"]["parent"]
        self.assertEqual(1, value["malformed_lines"])
        self.assertEqual("PARTIAL", value["status"])
        self.assertEqual(120, value["tokens"]["total_tokens"])

    def test_invalid_counts_and_conflicting_duplicate_are_rejected(self):
        for changes in ({"input_tokens": -1}, {"output_tokens": True}, {"total_tokens": 121},
                        {"cached_input_tokens": 101}, {"input_tokens": "100"},
                        {"reasoning_output_tokens": 21}):
            with self.subTest(changes=changes):
                self.write(self.usage(**changes))
                self.cli("summarize_codex_session.py", "--parent", self.log, code=2)
        self.write(self.usage(), self.usage(output_tokens=21, total_tokens=121))
        self.cli("summarize_codex_session.py", "--parent", self.log, code=2)

    def test_window_excludes_usage_and_messages_and_rejects_bad_timestamp(self):
        self.write(self.usage(timestamp="2026-11-01T01:00:00Z"), self.usage("r2"),
                   self.event("task_complete", last_agent_message="selected"),
                   {**self.message("outside"), "timestamp": "2026-11-03T01:00:00Z"},
                   {**self.event("task_complete", last_agent_message="outside task"),
                    "timestamp": "2026-11-03T01:00:00Z"})
        value = self.summary("--since", "2026-11-02T00:00:00Z", "--until", "2026-11-02T23:00:00Z")
        self.assertEqual(1, value["sources"]["parent"]["model_responses"])
        self.assertEqual("selected", value["sources"]["parent"]["final_message"])
        self.cli("summarize_codex_session.py", "--parent", self.log, "--since", "yesterday", code=2)

    def test_alias_inputs_and_output_cannot_overwrite_input(self):
        self.write(self.usage())
        alias = self.root / "alias.jsonl"
        alias.symlink_to(self.log)
        original = self.log.read_bytes()
        self.cli("summarize_codex_session.py", "--parent", self.log, "--child", f"qa={alias}", code=2)
        for output in (self.log, alias):
            self.cli("summarize_codex_session.py", "--parent", self.log, "--out", output, code=2)
            self.assertEqual(original, self.log.read_bytes())

    def test_hard_link_is_not_counted_as_an_independent_child(self):
        self.write(self.usage())
        alias = self.root / "hardlink.jsonl"
        alias.hardlink_to(self.log)
        self.cli("summarize_codex_session.py", "--parent", self.log, "--child", f"qa={alias}", code=2)

    def test_output_file_is_private_json(self):
        self.write(self.usage())
        output = self.root / "report.json"
        self.cli("summarize_codex_session.py", "--parent", self.log, "--out", output)
        self.assertEqual(120, json.loads(output.read_text())["combined_tokens"]["total_tokens"])
        self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))

    def test_truncation_counts_both_native_tool_output_forms_once(self):
        def result(kind, call_id, output):
            return {"type": "response_item", "timestamp": STAMP,
                    "payload": {"type": kind, "call_id": call_id, "output": output}}
        custom = result("custom_tool_call_output", "c1", [
            {"type": "input_text", "text": "Warning: truncated output (original token count: 12000)"}])
        self.write(self.usage(), custom, custom,
                   result("function_call_output", "c2", "123 tokens truncated"),
                   result("custom_tool_call_output", "c3", [
                       {"type": "text", "text": "The rule describes truncated output; this result is complete."}]),
                   result("custom_tool_call_output", "c4", [
                       {"type": "input_text", "text": "source.py:21: message = '123 tokens truncated'"}]),
                   result("custom_tool_call_output", "c5", [
                       {"type": "text", "text": "First output is complete."},
                       {"type": "text", "text": "Warning: truncated output (original token count: 9000)"}]))
        report = self.root / "report.json"
        self.cli("summarize_codex_session.py", "--parent", self.log, "--out", report)
        value = json.loads(report.read_text())
        self.assertEqual(3, value["sources"]["parent"]["truncated_tool_results"])

    def test_repository_output_is_rejected_without_creating_a_report(self):
        self.write(self.usage())
        repo = self.root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
        output = repo / "report.json"
        self.cli("summarize_codex_session.py", "--parent", self.log, "--out", output, code=2)
        self.assertFalse(output.exists())

    def test_bounded_reader_reconstructs_complete_source_without_skipping(self):
        source = self.root / "rules.txt"
        lines = [f"日本語 {i} " + '"\\' * 6 + ("\r\n" if i % 3 else "\n")
                 for i in range(12)] + ["last without newline"]
        source.write_text("".join(lines), encoding="utf-8")
        start, restored = 1, []
        while True:
            result = self.cli("read_review_source.py", source, "--start-line", start, "--max-chars", 500)
            self.assertLessEqual(len(result.stdout), 500)
            value = json.loads(result.stdout)
            self.assertEqual(start, value["start_line"])
            self.assertEqual(len(lines), value["total_lines"])
            numbered = value["text"].splitlines(keepends=True)
            for number, line in enumerate(numbered, start):
                match = re.match(r"^\s*(\d+)(?:: |\t| )", line)
                self.assertIsNotNone(match)
                self.assertEqual(number, int(match[1]))
                restored.append(line[match.end():])
            self.assertEqual(start + len(numbered) - 1, value["end_line"])
            if value["complete"]:
                break
            self.assertEqual(value["end_line"] + 1, value["next_line"])
            self.assertGreater(value["next_line"], start)
            start = value["next_line"]
        self.assertEqual("".join(lines), "".join(restored))

    def test_overlong_line_and_past_eof_fail_without_source_output(self):
        source = self.root / "rules.txt"
        source.write_text("x" * 1000, encoding="utf-8")
        for args in (("--max-chars", 300), ("--start-line", 2)):
            result = self.cli("read_review_source.py", source, *args, code=2)
            self.assertEqual("", result.stdout)
        source.write_text("", encoding="utf-8")
        self.assertTrue(json.loads(self.cli("read_review_source.py", source).stdout)["complete"])

    def test_requested_range_completion_and_exact_byte_identity(self):
        source = self.root / "rules.txt"
        data = b"first\r\nsecond\nlast"
        source.write_bytes(data)
        value = json.loads(self.cli("read_review_source.py", source, "--end-line", 2).stdout)
        self.assertEqual(hashlib.sha256(data).hexdigest(), value["source_sha256"])
        self.assertEqual("1: first\r\n2: second\n", value["text"])
        self.assertEqual(2, value["requested_end_line"])
        self.assertTrue(value["range_complete"])
        self.assertIsNone(value["next_range_line"])
        self.assertFalse(value["complete"])
        self.assertEqual(3, value["next_line"])

    def test_batch_bounds_combined_output_and_resumes_every_range(self):
        source = self.root / "rules.txt"
        source.write_text("".join(f"section {i}\n" for i in range(100)), encoding="utf-8")
        manifest = self.root / "reads.json"
        manifest.write_text(json.dumps([{"path": str(source), "start_line": 1, "end_line": 30},
                                        {"path": str(source), "start_line": 60, "end_line": 90}]))
        result = self.cli("read_review_source.py", "--batch", manifest, "--max-chars", 900)
        self.assertLessEqual(len(result.stdout), 900)
        reads = json.loads(result.stdout)["reads"]
        self.assertEqual([1, 60], [r["start_line"] for r in reads])
        for value, end in zip(reads, (30, 90)):
            self.assertLessEqual(value["end_line"], end)
            self.assertEqual(value["end_line"] + 1, value["next_line"])
            self.assertFalse(value["complete"])
            self.assertFalse(value["range_complete"])
            self.assertEqual(value["next_line"], value["next_range_line"])
        entire = json.loads(self.cli("read_review_source.py", "--batch", manifest).stdout)
        self.assertEqual([30, 90], [r["end_line"] for r in entire["reads"]])
        for value in entire["reads"]:
            self.assertTrue(value["range_complete"])
            self.assertIsNone(value["next_range_line"])

    def test_batch_failure_emits_no_partial_source_and_validates_requests(self):
        source = self.root / "rules.txt"
        source.write_text("private source\n", encoding="utf-8")
        manifest = self.root / "reads.json"
        for requests in ([], {}, [{"path": str(source)}, {"path": "missing"}],
                         [{"path": str(source), "start_line": True}],
                         [{"path": str(source), "end_line": 0}],
                         [{"path": str(source), "unknown": 1}]):
            manifest.write_text(json.dumps(requests))
            result = self.cli("read_review_source.py", "--batch", manifest, code=2)
            self.assertEqual("", result.stdout)


if __name__ == "__main__":
    unittest.main()
