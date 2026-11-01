"""実ログ形式で、内部advisorの検出と集計漏れを検証します。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/summarize_claude_session.py"
spec = importlib.util.spec_from_file_location("claude_summary", SCRIPT)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.parent = self.root / "session.jsonl"
        self.shape = {"type": "api-request-shape", "shape": {"tools": [
            {"name": name} for name in ("Read", "Glob", "Grep", "Agent", "SendMessage", "DeferredToolPlaceholder")]}}

    def write(self, path, records):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in records))

    def response(self, content, usage=None):
        return {"type": "assistant", "message": {"id": "response", "model": "sonnet",
            "usage": usage or {}, "content": content}}

    def test_restricted_inventory_passes_without_granting_review_approval(self):
        self.write(self.parent, [self.shape, self.response([
            {"type": "tool_use", "id": "read", "name": "Read", "input": {}}])])
        self.assertEqual("CHECKED", summary.summarize(self.parent)["review_boundary"]["status"])
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.parent),
                                 "--check-review-boundary"], capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertNotIn("APPROVE", result.stdout)

    def test_advisor_advertised_without_a_call_blocks(self):
        self.write(self.parent, [self.shape, {"type": "attachment", "attachment": {
            "type": "advisor_tool", "available": True, "model": "opus"}}])
        boundary = summary.summarize(self.parent)["review_boundary"]
        self.assertEqual("BLOCKED", boundary["status"])
        self.assertEqual([], boundary["server_tool_calls"])
        self.assertEqual("advisor", boundary["violations"][0]["name"])

    def test_later_tool_inventory_and_physical_lines_are_checked(self):
        self.write(self.parent, [self.shape])
        with self.parent.open("a") as stream:
            stream.write("\n" + json.dumps({"type": "attachment", "attachment": {
                "type": "prompt_snapshot", "tools": [{"name": "Bash"}]}}) + "\n")
        value = summary.summarize(self.parent)["review_boundary"]
        self.assertEqual("BLOCKED", value["status"])
        self.assertEqual(3, value["violations"][0]["line"])

    def test_child_server_call_and_usage_are_not_hidden_or_duplicated(self):
        self.write(self.parent, [self.shape])
        child = self.root / "session/subagents/agent-child.jsonl"
        usage = {"input_tokens": 4, "output_tokens": 9, "cache_read_input_tokens": 100,
                 "cache_creation_input_tokens": 20, "iterations": [
            {"type": "message", "input_tokens": 2, "output_tokens": 4},
            {"type": "advisor_message", "model": "opus", "input_tokens": 70, "output_tokens": 8},
            {"type": "message", "input_tokens": 2, "output_tokens": 5}]}
        call = {"type": "server_tool_use", "id": "server-1", "name": "advisor", "input": {}}
        row = self.response([call], usage)
        self.write(child, [self.shape, row, row, self.response([
            {"type": "advisor_tool_result", "content": "encrypted-private-body"}], usage)])
        value = summary.summarize(self.parent)
        self.assertEqual({"input_tokens": 74, "output_tokens": 17,
                          "cache_read_input_tokens": 100, "cache_creation_input_tokens": 20}, value["tokens"])
        self.assertEqual(70, value["tokens_by_model"]["opus"]["input_tokens"])
        self.assertEqual(1, value["api_responses"]["children"])
        self.assertEqual(1, len(value["review_boundary"]["server_tool_calls"]))
        self.assertEqual("BLOCKED", value["review_boundary"]["status"])
        self.assertNotIn("encrypted-private-body", json.dumps(value))
        self.assertEqual({"samples": 1, "min_tokens": 124, "median_tokens": 124.0,
                          "max_tokens": 124}, value["context_inputs_by_transcript"][child.name])

    def test_context_usage_merges_streamed_updates_and_records_compaction(self):
        first = self.response([], {"input_tokens": 2, "cache_read_input_tokens": 100})
        update = self.response([], {"input_tokens": 2, "cache_read_input_tokens": 100,
                                    "cache_creation_input_tokens": 20, "output_tokens": 900})
        second = self.response([], {"input_tokens": 3, "cache_read_input_tokens": 40})
        second["message"]["id"] = "after-compact"
        boundary = {"type": "system", "subtype": "compact_boundary", "uuid": "compact-1"}
        synthetic = self.response([])
        synthetic["message"].update({"id": "synthetic", "model": "<synthetic>"})
        self.write(self.parent, [self.shape, first, update, boundary, boundary, second, synthetic])
        value = summary.summarize(self.parent)
        self.assertEqual({"samples": 2, "min_tokens": 43, "median_tokens": 82.5,
                          "max_tokens": 122}, value["context_inputs_by_transcript"][self.parent.name])
        self.assertEqual(1, value["recorded_compaction_boundaries"][self.parent.name])

    def test_missing_context_usage_is_not_reported_as_zero_sized_input(self):
        self.write(self.parent, [self.shape, self.response([])])
        value = summary.summarize(self.parent)
        self.assertEqual({"samples": 0, "min_tokens": None, "median_tokens": None,
                          "max_tokens": None}, value["context_inputs_by_transcript"][self.parent.name])

    def test_empty_compaction_ids_are_counted_as_separate_records(self):
        boundary = {"type": "system", "subtype": "compact_boundary", "uuid": ""}
        self.write(self.parent, [self.shape, boundary, boundary])
        self.assertEqual(2, summary.summarize(self.parent)["recorded_compaction_boundaries"][self.parent.name])

    def test_incomplete_or_malformed_records_do_not_pass_the_cli(self):
        for raw in ("", "[]\n", "not-json\n", json.dumps(self.response([])) + "\n"):
            with self.subTest(raw=raw):
                self.parent.write_text(raw)
                result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.parent),
                                         "--check-review-boundary"], capture_output=True, text=True)
                self.assertEqual(2, result.returncode)

    def test_missing_child_or_forbidden_inventory_does_not_pass(self):
        self.write(self.parent, [self.shape, self.response([
            {"type": "tool_use", "id": "agent", "name": "Agent", "input": {}}])])
        self.assertEqual("UNCONFIRMED", summary.summarize(self.parent)["review_boundary"]["status"])
        bad_shape = {"type": "api-request-shape", "shape": {"tools": [{"name": "Bash"}]}}
        self.write(self.parent, [bad_shape])
        result = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), str(self.parent),
                                 "--check-review-boundary"], capture_output=True, text=True)
        self.assertEqual(1, result.returncode)


if __name__ == "__main__":
    unittest.main()
