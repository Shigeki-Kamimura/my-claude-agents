"""圧縮区間とReadの集計を、実ログ形式で確認します。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/summarize_claude_session.py"
spec = importlib.util.spec_from_file_location("claude_context_summary", SCRIPT)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class ContextSegmentTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.parent = Path(folder.name) / "parent.jsonl"

    def write(self, path, *rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def response(self, response_id, usage=None, content=None):
        return {"type": "assistant", "message": {"id": response_id, "model": "sonnet",
                "usage": usage or {}, "content": content or []}}

    def boundary(self, uuid):
        return {"type": "system", "subtype": "compact_boundary", "uuid": uuid}

    def segment(self, index, uuid, inputs=(), counts=(0, 0, 0)):
        ordered = sorted(inputs)
        size = len(ordered)
        return {"segment": index, "boundary_uuid": uuid, "samples": size,
                "min_tokens": min(inputs) if size else None,
                "median_tokens": (ordered[(size - 1) // 2] + ordered[size // 2]) / 2 if size else None,
                "max_tokens": max(inputs) if size else None,
                "first_tokens": inputs[0] if size else None, "last_tokens": inputs[-1] if size else None,
                "total_input_tokens": sum(inputs), "input_tokens": counts[0],
                "cache_read_input_tokens": counts[1], "cache_creation_input_tokens": counts[2]}

    def test_segments_show_cache_creation_spike_without_counting_output_or_advisor(self):
        self.write(self.parent, self.response("r1", {"input_tokens": 2, "cache_read_input_tokens": 100,
            "cache_creation_input_tokens": 20, "output_tokens": 999, "iterations": [
                {"type": "advisor_message", "model": "opus", "input_tokens": 700, "output_tokens": 800}]}),
            self.boundary("b1"), self.response("r2", {"input_tokens": 3, "cache_read_input_tokens": 40,
            "cache_creation_input_tokens": 1000, "output_tokens": 9000}),
            self.response("r3", {"input_tokens": 4, "cache_read_input_tokens": 6}))
        value = summary.summarize(self.parent)
        self.assertEqual([self.segment(0, None, [122], (2, 100, 20)),
                          self.segment(1, "b1", [1043, 10], (7, 46, 1000))],
                         value["context_inputs_by_compaction"][self.parent.name])
        self.assertEqual({"samples": 3, "min_tokens": 10, "median_tokens": 122.0, "max_tokens": 1043},
                         value["context_inputs_by_transcript"][self.parent.name])
        self.assertEqual({"input_tokens": 709, "output_tokens": 10799,
                          "cache_read_input_tokens": 146, "cache_creation_input_tokens": 1020}, value["tokens"])
        self.assertEqual({"parent": 3, "children": 0, "total": 3}, value["api_responses"])

    def test_streamed_update_stays_in_first_segment_and_replayed_boundary_is_not_counted(self):
        self.write(self.parent, self.response("r1", {"input_tokens": 2, "cache_read_input_tokens": 100}),
            self.boundary("b1"), self.response("r1", {"input_tokens": 2, "cache_read_input_tokens": 100,
                "cache_creation_input_tokens": 20, "output_tokens": 900}), self.boundary("b1"),
            self.response("r2", {"input_tokens": 3, "cache_read_input_tokens": 40}))
        value = summary.summarize(self.parent)
        self.assertEqual([self.segment(0, None, [122], (2, 100, 20)),
                          self.segment(1, "b1", [43], (3, 40, 0))],
                         value["context_inputs_by_compaction"][self.parent.name])
        self.assertEqual(1, value["recorded_compaction_boundaries"][self.parent.name])
        self.assertEqual(2, value["api_responses"]["total"])

    def test_transcripts_keep_separate_ids_and_empty_segments_without_inventing_samples(self):
        child = self.parent.with_suffix("") / "subagents/agent-child.jsonl"
        empty = child.with_name("agent-empty.jsonl")
        self.write(self.parent, self.response("same"), self.response("no-usage"),
                   self.boundary(None), self.boundary(""), self.response("same", {"input_tokens": 8}))
        self.write(child, self.response("same", {"input_tokens": 5}), self.boundary("b1"), self.boundary("b2"))
        self.write(empty)
        value = summary.summarize(self.parent)
        self.assertEqual({self.parent.name: [self.segment(0, None, [8], (8, 0, 0)),
                          self.segment(1, None), self.segment(2, None)],
                          child.name: [self.segment(0, None, [5], (5, 0, 0)),
                          self.segment(1, "b1"), self.segment(2, "b2")],
                          empty.name: [self.segment(0, None)]}, value["context_inputs_by_compaction"])
        self.assertEqual({"parent": 2, "children": 1, "total": 3}, value["api_responses"])

    def test_read_counts_require_positive_integer_offset_and_limit_and_deduplicate_per_transcript(self):
        def read(tool_id, args, name="Read"):
            return {"type": "tool_use", "id": tool_id, "name": name, "input": args}
        calls = [read("bounded", {"offset": 1, "limit": 10, "file_path": "/private/source.txt"})]
        invalid = [{}, {"limit": 10}, {"offset": 1}, {"offset": 0, "limit": 1},
                   {"offset": 1, "limit": -1}, {"offset": True, "limit": 1},
                   {"offset": 1, "limit": False}, {"offset": 1.0, "limit": 1},
                   {"offset": "1", "limit": 1}, None, "malformed"]
        calls += [read(f"bad-{i}", args) for i, args in enumerate(invalid)]
        calls += [read("other", {"offset": 1, "limit": 1}, "Bash")]
        row = self.response("response", content=calls)
        self.write(self.parent, row, row)
        child = self.parent.with_suffix("") / "subagents/agent-child.jsonl"
        self.write(child, self.response("response", content=[calls[0]]))
        value = summary.summarize(self.parent)
        self.assertEqual({self.parent.name: {"read_calls": 12, "explicit_range_calls": 1, "missing_range_calls": 11},
                          child.name: {"read_calls": 1, "explicit_range_calls": 1, "missing_range_calls": 0}},
                         value["source_reads_by_transcript"])
        metrics = {key: value[key] for key in ("source_reads_by_transcript", "context_inputs_by_compaction")}
        self.assertNotIn("/private/source.txt", json.dumps(metrics))


if __name__ == "__main__":
    unittest.main()
