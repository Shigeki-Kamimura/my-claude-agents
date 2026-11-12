"""CLI引数・保存順序を確認します。実CLIと課金は発生しません。"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import implementation_review as controller
import implementation_review_archive as archive
import implementation_review_state as flow
import start_implementation_review_task as transport

RENDERER = Path(os.environ.get("REVIEW_RENDERER_TEST_PATH", str(ROOT / "tools/render_review_record.py")))
COMMAND_SOURCE = Path(os.environ.get("REVIEW_COMMAND_TEST_PATH", str(ROOT / "tools/start_md_review.py")))


class TransportTests(unittest.TestCase):
    def test_review_snapshot_retains_actual_prior_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "snapshots").mkdir()
            state = {"snapshot_id": "snap1", "rules_id": "rules1", "source_config": {}, "history": []}
            job = {"slot": "cr_a"}
            first = {"snapshot_id": "snap1", "rules_id": "rules1", "paths": [], "rules": []}
            with patch.object(controller, "source_identity", return_value=first):
                controller.freeze_review_source(folder, state, job)
            saved = json.loads((folder / "snapshots/snap1/snapshot.json").read_text())
            self.assertNotIn("rules_id", saved)
            self.assertEqual(saved["snapshot_id"], "snap1")
            state["history"] = [{"result": {"slot": "cr_a", "snapshot_id": "snap1", "coverage": "COMPLETE"}}]
            state["snapshot_id"] = "snap2"
            with patch.object(controller, "source_identity", return_value={**first, "snapshot_id": "snap2"}):
                controller.freeze_review_source(folder, state, job)
            self.assertEqual(job["previous_snapshot_id"], "snap1")
            self.assertEqual(job["prior_coverage"], "COMPLETE")

    def test_python_sources_parse(self):
        for path in (ROOT / "tools").glob("*implementation_review*.py"):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"))

    def command_functions(self):
        tree = ast.parse(COMMAND_SOURCE.read_text(encoding="utf-8"))
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"command", "command_for_provider"}]
        self.assertEqual(len(nodes), 2)
        namespace = {"sys": sys, "json": json, "review": SimpleNamespace(ROOT=Path("/fixture/config")),
                     "codex_mcp_overrides": lambda project: ["-c", "features.apps=false"],
                     "MD_TOOLS": ("git_diff", "review_context"), "TOOLS": ["Read", "Glob", "Grep", "Agent"], "BACKLOG_READ": ("get_issue",)}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(COMMAND_SOURCE), "exec"), namespace)
        return namespace

    def test_provider_selection_preserves_original_wrappers(self):
        ns = self.command_functions()
        for direction, provider in (("codex-claude-review", "claude"), ("claude-codex-review", "codex")):
            old = ns["command"]({"direction": direction, "project": "/fixture/project"}, "qa", Path("/fixture/round"))
            new = ns["command_for_provider"](provider, "/fixture/project", Path("/fixture/round"))
            self.assertEqual(old, new)
        self.assertEqual(ns["command"]({"direction": "codex-claude-review", "project": "/fixture/project"}, "ci", Path("/fixture/round"))[0], "codex")

    def test_both_provider_commands_stay_read_only(self):
        ns = self.command_functions()
        codex = ns["command_for_provider"]("codex", "/fixture/project", Path("/fixture/round"))
        self.assertEqual(codex[codex.index("--sandbox") + 1], "read-only")
        self.assertIn("features.apps=false", codex)
        claude = ns["command_for_provider"]("claude", "/fixture/project", Path("/fixture/round"))
        self.assertEqual(claude[claude.index("--permission-mode") + 1], "dontAsk")
        for tool in ("Bash", "Edit", "Write", "NotebookEdit"):
            self.assertIn(tool, claude[claude.index("--disallowedTools") + 1:])
        self.assertIn("--strict-mcp-config", claude)

    def test_invalid_backend_and_codex_resume_refused(self):
        ns = self.command_functions()
        for provider, resume in (("unknown", None), ("codex", "old-parent")):
            with self.assertRaises(ValueError):
                ns["command_for_provider"](provider, "/fixture/project", Path("/fixture/round"), resume)

    def test_only_selected_read_only_job_can_be_dispatched(self):
        state = flow.new_state(flow.Policy("codex", "codex", "claude", "codex"), "snap", "rules", "fixture")
        state["archive_status"] = "COMPLETE"
        with self.assertRaises(flow.ContractError):
            transport.allowed_task(state, "job-0001")
        flow.queue(state, ["qa"], "initial")
        job = transport.allowed_task(state, "job-0002")
        self.assertEqual(job["provider"], "claude")
        state["archive_status"] = "PARTIAL"
        with self.assertRaises(flow.ContractError):
            transport.allowed_task(state, "job-0002")

    def test_html_failure_keeps_pending_transition_and_old_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "parent.jsonl"
            log.write_text(json.dumps({"role": "user", "text": "fixture"}) + "\n")
            state = flow.new_state(flow.Policy("codex", "codex", "claude", "codex"), "snap", "rules", "fixture")
            state.update(run_id="fixture", revision=0, audit=[], archive_sources={"parent": controller.log_window("parent", "parent", log)}, required_archive_owners=[])
            folder = root / "run"
            folder.mkdir()
            with patch.object(archive, "save_record", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    controller.persist(folder, state, {"type": "fixture"})
            self.assertTrue((folder / "pending-transition.json").is_file())
            self.assertFalse((folder / "state.json").exists())

    def test_html_saved_before_state_becomes_dispatchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "parent.jsonl"
            log.write_text(json.dumps({"role": "user", "text": "fixture"}) + "\n")
            state = flow.new_state(flow.Policy("codex", "codex", "claude", "codex"), "snap", "rules", "fixture")
            state.update(run_id="fixture", revision=0, audit=[], archive_sources={"parent": controller.log_window("parent", "parent", log)}, required_archive_owners=[])
            folder = root / "run"
            folder.mkdir()
            original = archive.renderer_from
            with patch.object(archive, "renderer_from", side_effect=lambda path=None: original(RENDERER)):
                saved = controller.persist(folder, state, {"type": "fixture"})
            self.assertEqual(saved["archive_status"], "COMPLETE")
            self.assertTrue(Path(saved["last_html"]).is_file())
            self.assertFalse((folder / "pending-transition.json").exists())
            self.assertTrue(flow.pending(saved))

    def test_missing_transcript_blocks_next_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "parent.jsonl"
            log.write_text(json.dumps({"role": "user", "text": "fixture"}) + "\n")
            state = flow.new_state(flow.Policy("codex", "codex", "claude", "codex"), "snap", "rules", "fixture")
            state.update(run_id="fixture", revision=0, audit=[], archive_sources={"parent": controller.log_window("parent", "parent", log)}, required_archive_owners=["missing-child"])
            folder = root / "run"
            folder.mkdir()
            original = archive.renderer_from
            with patch.object(archive, "renderer_from", side_effect=lambda path=None: original(RENDERER)):
                saved = controller.persist(folder, state, {"type": "fixture"})
            self.assertEqual(saved["status"], "BLOCKED")
            self.assertEqual(flow.pending(saved), [])

    def test_codex_log_lookup_binds_exact_session_id(self):
        import datetime as dt
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            folder = home / "sessions/2026/11/12"
            folder.mkdir(parents=True)
            path = folder / "rollout-2026-11-12T00-00-00-test-id.jsonl"
            path.write_text(json.dumps({"type": "session_meta", "payload": {"id": "test-id"}}) + "\n")
            start = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)
            self.assertEqual(transport.codex_log("test-id", start, start, home), path)
            path.write_text(json.dumps({"type": "session_meta", "payload": {"id": "wrong"}}) + "\n")
            with self.assertRaises(flow.ContractError):
                transport.codex_log("test-id", start, start, home)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{"publish": false, "publish": true}')
            with self.assertRaises(flow.ContractError):
                controller.load_json(path)


if __name__ == "__main__":
    unittest.main()
