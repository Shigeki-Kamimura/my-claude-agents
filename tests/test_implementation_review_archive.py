"""会話HTMLの保存、欠落、秘匿欄除外を確認します。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import implementation_review_archive as archive

ROOT = Path(__file__).resolve().parents[1]
RENDERER = Path(os.environ.get("REVIEW_RENDERER_TEST_PATH", str(ROOT / "tools/render_review_record.py")))


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "run"
        self.state = {"run_id": "fixture-run", "status": "RUNNING", "stage": "pcr", "snapshot_id": "snap-1",
                      "rules_id": "rules-1", "updated_at": "2026-11-12T07:10:00Z", "ledger": {}}

    def source(self, owner, rows):
        path = self.root / (owner + ".jsonl")
        data = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
        path.write_bytes(data)
        return {"owner_id": owner, "label": owner, "path": str(path), "start": 0, "end": len(data)}

    def save(self, sources, expected=None, revision=1):
        return archive.save_record(self.out, revision, self.state, sources,
                                   expected or {s["owner_id"] for s in sources}, RENDERER)

    def test_partial_cli_output_keeps_visible_result_only(self):
        rows = [
            {"type": "thread.started", "thread_id": "known-id"},
            {"type": "item.completed", "item": {"type": "reasoning", "text": "HIDDEN_REASONING"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "中断前の公開応答です"}},
            {"type": "result", "result": "利用制限のため停止しました"},
        ]
        result = self.save([self.source("transport", rows)], {"transport", "missing-child"})
        body = Path(result["html_path"]).read_text()
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIn("中断前の公開応答です", body)
        self.assertIn("利用制限のため停止しました", body)
        self.assertNotIn("HIDDEN_REASONING", body)

    def test_parent_children_and_fix_round_kept(self):
        sources = [self.source("parent", [{"timestamp": "2026-11-12T07:00:00Z", "role": "user", "text": "設問編集を実装してください"}])]
        for slot in ("hq", "cr_a", "cr_b", "validator", "qa", "e2e"):
            sources.append(self.source(slot, [{"role": "assistant", "text": slot + "の確認結果です"}]))
        record = self.save(sources)
        self.assertEqual(record["status"], "COMPLETE")
        body = Path(record["html_path"]).read_text()
        for slot in ("hq", "cr_a", "cr_b", "validator", "qa", "e2e"):
            self.assertIn(slot + "の確認結果です", body)
        self.assertIn("設問編集を実装してください", body)
        first = Path(record["html_path"]).read_bytes()
        second = self.save(sources, revision=2)
        self.assertEqual(Path(record["html_path"]).read_bytes(), first)
        self.assertNotEqual(record["html_path"], second["html_path"])

    def test_codex_system_analysis_reasoning_omitted(self):
        rows = [
            {"type": "response_item", "payload": {"type": "message", "role": "system", "content": "HIDDEN_SYSTEM"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "channel": "analysis", "content": "HIDDEN_ANALYSIS"}},
            {"type": "response_item", "payload": {"type": "reasoning", "summary": "HIDDEN_REASONING", "encrypted_content": "HIDDEN_ENCRYPTED"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "channel": "final", "content": [{"type": "output_text", "text": "公開した判定です"}]}},
        ]
        body = Path(self.save([self.source("codex", rows)])["html_path"]).read_text()
        self.assertIn("公開した判定です", body)
        for name in ("HIDDEN_SYSTEM", "HIDDEN_ANALYSIS", "HIDDEN_REASONING", "HIDDEN_ENCRYPTED"):
            self.assertNotIn(name, body)

    def test_claude_thinking_omitted(self):
        source = self.source("claude", [{"type": "assistant", "message": {"content": [
            {"type": "thinking", "thinking": "HIDDEN_THINKING"},
            {"type": "text", "text": "正常系と異常系を確認しました"}]}}])
        record = self.save([source])
        body = Path(record["html_path"]).read_text()
        self.assertNotIn("HIDDEN_THINKING", body)
        self.assertIn("正常系と異常系を確認しました", body)

    def test_generic_protected_roles_and_channels_omitted(self):
        rows = [{"role": role, "text": "HIDDEN_" + role} for role in archive.HIDDEN_ROLES]
        rows += [{"role": "assistant", "channel": "analysis", "text": "HIDDEN_CHANNEL"}, {"role": "user", "text": "公開依頼です"}]
        body = Path(self.save([self.source("parent", rows)])["html_path"]).read_text()
        self.assertNotIn("HIDDEN_", body)
        self.assertIn("公開依頼です", body)

    def test_tool_arguments_are_not_dumped(self):
        source = self.source("claude", [{"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Agent", "input": {"system": "HIDDEN_ARGUMENT"}},
            {"type": "text", "text": "担当を起動しました"}]}}])
        body = Path(self.save([source])["html_path"]).read_text()
        self.assertNotIn("HIDDEN_ARGUMENT", body)
        self.assertIn("ツール呼出し", body)

    def test_html_injection_and_external_resources_disabled(self):
        source = self.source("parent", [{"role": "assistant", "text": '<script>alert(1)</script><img src="https://example.invalid/x">'}])
        body = Path(self.save([source])["html_path"]).read_text()
        self.assertNotIn("<script>", body)
        self.assertNotIn('<img src=', body)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn("default-src 'none'", body)

    def test_known_credentials_redacted(self):
        secret = "sk-" + "X" * 30
        source = self.source("parent", [{"role": "assistant", "text": "api_key=" + secret}])
        body = Path(self.save([source])["html_path"]).read_text()
        self.assertNotIn(secret, body)
        self.assertIn("REDACTED", body)

    def test_missing_child_is_partial_not_fake_conversation(self):
        parent = self.source("parent", [{"role": "user", "text": "依頼です"}])
        record = self.save([parent], {"parent", "cr_b"})
        self.assertEqual(record["status"], "PARTIAL")
        self.assertEqual(record["missing_owners"], ["cr_b"])
        body = Path(record["html_path"]).read_text()
        self.assertIn("PARTIAL", body)
        self.assertNotIn("cr_bの確認結果", body)

    def test_missing_file_is_partial(self):
        source = self.source("parent", [{"role": "user", "text": "依頼です"}])
        Path(source["path"]).unlink()
        record = self.save([source])
        self.assertEqual(record["status"], "PARTIAL")

    def test_unknown_format_and_broken_json_are_visible_gaps(self):
        source = self.source("parent", [{"role": "user", "text": "依頼です"}, {"new_format": "do not guess"}])
        path = Path(source["path"])
        path.write_bytes(path.read_bytes() + b'{bad-json\n')
        source["end"] = path.stat().st_size
        record = self.save([source])
        self.assertEqual(record["status"], "PARTIAL")
        self.assertEqual(record["sources"][0]["unknown_rows"], 1)
        self.assertEqual(record["sources"][0]["unreadable_rows"], 1)

    def test_fixed_window_excludes_unrelated_history(self):
        rows = [{"role": "user", "text": "UNRELATED_OLD"}, {"role": "user", "text": "今回の依頼"}, {"role": "assistant", "text": "UNRELATED_LATER"}]
        source = self.source("parent", rows)
        parts = Path(source["path"]).read_bytes().splitlines(keepends=True)
        source["start"] = len(parts[0])
        source["end"] = len(parts[0]) + len(parts[1])
        body = Path(self.save([source])["html_path"]).read_text()
        self.assertIn("今回の依頼", body)
        self.assertNotIn("UNRELATED_", body)

    def test_partial_last_line_and_mid_line_start_rejected(self):
        for field in ("start", "end"):
            with self.subTest(field=field):
                source = self.source("parent", [{"role": "user", "text": "依頼です"}])
                source[field] += 1 if field == "start" else -1
                record = archive.save_record(self.root / field, 1, self.state, [source], {"parent"}, RENDERER)
                self.assertEqual(record["status"], "PARTIAL")

    def test_no_overwrite_of_existing_record(self):
        source = self.source("parent", [{"role": "user", "text": "依頼です"}])
        self.save([source])
        with self.assertRaises(ValueError):
            self.save([source])

    def test_failed_write_does_not_destroy_previous_html(self):
        source = self.source("parent", [{"role": "user", "text": "依頼です"}])
        self.save([source])
        before = (self.out / "index.html").read_bytes()
        with patch.object(archive, "atomic_write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.save([source], revision=2)
        self.assertEqual((self.out / "index.html").read_bytes(), before)

    def test_records_are_owner_only_permissions(self):
        record = self.save([self.source("parent", [{"role": "user", "text": "依頼です"}])])
        self.assertEqual(Path(record["html_path"]).stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.out.stat().st_mode & 0o777, 0o700)

    def test_output_symlink_refused(self):
        target = self.root / "outside"
        target.mkdir()
        self.out.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.save([self.source("parent", [{"role": "user", "text": "依頼です"}])])

    def test_duplicate_source_ids_refused(self):
        source = self.source("parent", [{"role": "user", "text": "依頼です"}])
        with self.assertRaises(ValueError):
            self.save([source, source])

    def test_codex_duplicate_message_not_double_counted(self):
        source = self.source("codex", [
            {"type": "event_msg", "payload": {"type": "agent_message", "message": "同じ応答"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "同じ応答"}]}}
        ])
        record = self.save([source])
        self.assertEqual(record["sources"][0]["visible_events"], 1)


if __name__ == "__main__":
    unittest.main()
