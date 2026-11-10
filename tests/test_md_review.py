"""実Gitと偽CLIで、MD受渡しの権限境界と失敗系を確認します。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("start_md_review", ROOT / "tools/start_md_review.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
review = launcher.review


class MDReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.project = self.temp / "project"
        self.project.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.test")
        self.git("config", "user.name", "Fixture")
        (self.project / "code.txt").write_text("base\n")
        (self.project / "rule.md").write_text("rule\n")
        self.git("add", "code.txt", "rule.md")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        (self.project / "code.txt").write_text("branch\n")
        self.git("commit", "-qam", "branch")
        (self.project / "code.txt").write_text("staged\n")
        self.git("add", "code.txt")
        (self.project / "code.txt").write_text("working\n")
        (self.project / "new.txt").write_text("new untracked\n")
        self.summary = self.temp / "summary.md"
        self.summary.write_text("User request: review cr only\nPurpose: fixture\n")
        self.run = self.temp / "run"

    def git(self, *args):
        return subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(self.project), *args],
                              text=True, capture_output=True, check=True)

    def cli(self, script, *args, code=0, env=None):
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools" / script), *map(str, args)],
                                text=True, capture_output=True, env=env)
        self.assertEqual(code, result.returncode, result.stderr)
        return result

    def init(self, *extra, code=0):
        return self.cli("md_review.py", "--project", self.project, "--base", self.base,
                        "--direction", "codex-claude-review", "--layers", "cr",
                        "--paths", "code.txt", "new.txt", "--rules", self.project / "rule.md",
                        "--summary-file", self.summary, "--out-dir", self.run, *extra, code=code)

    def freeze(self, *extra):
        self.init(*extra)
        folder, config = review.load_run(self.run)
        target = folder / "fixture-round"
        target.mkdir()
        for view in ("base", "head", "index", "worktree"):
            (target / view).mkdir()
        info = review.capture(config, target)
        review.private_write(target / "snapshot.json", json.dumps(info))
        return target, config, info

    def test_init_leaves_repo_and_index_unchanged_and_never_changes_ignore(self):
        index = (self.project / ".git/index").read_bytes()
        status = self.git("status", "--porcelain").stdout
        self.init()
        self.assertEqual(index, (self.project / ".git/index").read_bytes())
        self.assertEqual(status, self.git("status", "--porcelain").stdout)
        self.assertFalse((self.project / ".gitignore").exists())
        self.assertEqual(0o600, (self.run / "review.md").stat().st_mode & 0o777)
        self.assertEqual(["cr"], review.load_run(self.run)[1]["layers"])

    def test_git_views_keep_branch_index_worktree_and_untracked(self):
        target, _, _ = self.freeze()
        self.assertIn("+branch", review.frozen_diff(target, "branch"))
        self.assertIn("+staged", review.frozen_diff(target, "staged"))
        diff = review.frozen_diff(target, "unstaged")
        self.assertIn("+working", diff)
        self.assertIn("+new untracked", diff)

    def test_extension_commands_are_not_executed(self):
        marker = self.temp / "executed"
        evil = self.temp / "evil"
        evil.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
        evil.chmod(0o700)
        self.git("config", "core.fsmonitor", str(evil))
        self.git("config", "filter.evil.clean", str(evil))
        self.git("config", "filter.evil.process", str(evil))
        self.git("config", "diff.evil.command", str(evil))
        self.git("config", "diff.evil.textconv", str(evil))
        (self.project / ".gitattributes").write_text("*.txt filter=evil diff=evil\n")
        target, _, _ = self.freeze("--paths", "code.txt", "new.txt", ".gitattributes")
        for view in ("branch", "staged", "unstaged"):
            review.frozen_diff(target, view)
        self.assertFalse(marker.exists())

    def test_source_index_rules_and_modes_change_identity(self):
        _, config, original = self.freeze()
        (self.project / "new.txt").write_text("changed\n")
        self.assertNotEqual(original, review.capture(config))
        (self.project / "new.txt").write_text("new untracked\n")
        self.assertEqual(original, review.capture(config))
        (self.project / "rule.md").write_text("new rule\n")
        self.assertNotEqual(original, review.capture(config))
        (self.project / "rule.md").write_text("rule\n")
        (self.project / "code.txt").chmod(0o755)
        self.assertNotEqual(original, review.capture(config))

    def test_git_bridge_rejects_arbitrary_command_and_output_path(self):
        target, _, _ = self.freeze()
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "git_diff", "arguments": {"view": "branch"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "git_diff", "arguments": {"view": "branch", "output_path": str(self.temp / "bad")}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "git_diff", "arguments": {"view": "--output=bad"}}},
        ]
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/md_review.py"), "--serve", str(target)],
                                input="\n".join(map(json.dumps, messages)) + "\n", capture_output=True, text=True, check=True)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(["git_diff", "review_context"], [t["name"] for t in responses[1]["result"]["tools"]])
        self.assertIn("+branch", responses[2]["result"]["content"][0]["text"])
        self.assertIn("error", responses[3])
        self.assertIn("error", responses[4])
        self.assertFalse((self.temp / "bad").exists())

    def test_output_safety_and_path_traversal_fail_closed(self):
        self.init("--out-dir", self.project / "docs/review", code=2)
        self.assertFalse((self.project / "docs/review").exists())
        self.init("--paths", "../secret", code=2)
        self.init("--paths", ".env.development", code=2)
        link = self.temp / "alias"
        link.symlink_to(self.temp / "actual", target_is_directory=True)
        self.init("--out-dir", link / "run", code=2)
        outside = self.temp / "outside"
        outside.mkdir()
        self.init("--out-dir", outside / ".." / "project" / "docs" / "run", code=2)
        self.assertFalse(self.run.exists())

    def test_already_ignored_codex_storage_is_allowed_without_new_exclusions(self):
        exclude = self.project / ".git/info/exclude"
        exclude.write_text(exclude.read_text() + "\n.codex/\n")
        original = exclude.read_bytes()
        target = self.project / ".codex/review-runs/fixture"
        before = self.git("status", "--porcelain").stdout
        self.init("--out-dir", target)
        self.assertEqual(original, exclude.read_bytes())
        self.assertEqual(before, self.git("status", "--porcelain").stdout)

    def test_tool_gate_allows_read_and_rejects_backlog_mutations_and_bash(self):
        for name, code in [("Read", 0), ("Agent", 0), ("Task", 0), ("mcp__md_review__git_diff", 0), ("mcp__md_review__review_context", 0), ("mcp__backlog__get_issue", 0),
                           ("mcp__backlog__add_issue", 2), ("mcp__backlog__delete_issue", 2),
                           ("Bash", 2), ("Write", 2), ("Edit", 2), ("NotebookEdit", 2), ("mcp__other__get_issue", 2)]:
            result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/md_review_tool_gate.py")],
                                    input=json.dumps({"tool_name": name}), text=True, capture_output=True)
            self.assertEqual(code, result.returncode, name)

    def test_invalid_one_shot_appends_response_without_approval_or_retry(self):
        self.init()
        fakebin = self.temp / "bin"
        fakebin.mkdir()
        fake = fakebin / "claude"
        fake.write_text("#!/usr/bin/python3\nimport json,sys\nsys.stdin.read()\nprint(json.dumps({'type':'result','session_id':'fixture-id','result':'FAKE transport response'}))\n")
        fake.chmod(0o700)
        env = {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"]}
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2, env=env)
        record = (self.run / "review.md").read_text()
        self.assertIn("FAKE transport response", record)
        self.assertIn("BLOCKED", record)
        self.assertNotIn('"status": "APPROVE"', record)
        self.assertEqual(1, len(list(self.run.glob("*/execution.json"))))
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "adv", code=2, env=env)
        self.assertEqual(1, len(list(self.run.glob("*/execution.json"))))

    def test_launcher_directions_and_resume_keep_tool_limits(self):
        self.init()
        config = review.load_run(self.run)[1]
        round_dir = self.run / "fixture"
        for resume in (None, "actual-completed-parent"):
            args = launcher.command(config, "cr", round_dir, resume)
            self.assertIn("--print", args)
            self.assertIn("--strict-mcp-config", args)
            self.assertIn("dontAsk", args)
            self.assertNotIn("--background", args)
            self.assertNotIn("--dangerously-skip-permissions", args)
            denied = args[args.index("--disallowedTools") + 1:]
            self.assertTrue({"Bash", "Edit", "Write", "NotebookEdit"}.issubset(denied))
        config["direction"] = "claude-codex-review"
        with patch.object(launcher, "codex_mcp_overrides", return_value=["-c", "mcp_servers.playwright.enabled=false"]):
            args = launcher.command(config, "cr", round_dir)
        self.assertEqual(["codex", "exec"], args[:2])
        self.assertIn("read-only", args)
        with self.assertRaises(ValueError):
            launcher.command(config, "cr", round_dir, "previous-thread")

    def test_new_rules_and_fix_notes_append_without_erasing_review_history(self):
        self.init()
        before = (self.run / "review.md").read_text()
        added = self.project / "added-rule.md"
        added.write_text("extra required rule\n")
        notes = self.temp / "fix.md"
        notes.write_text("Fix candidate: CR-04, add required rule\n")
        self.cli("md_review.py", "--run-dir", self.run, "--note-file", notes,
                 "--add-rules", added, "--add-paths", "added-rule.md")
        config = review.load_run(self.run)[1]
        self.assertIn(str(added.resolve()), config["rules"])
        self.assertIn("added-rule.md", config["paths"])
        original = review.capture(config)
        added.write_text("changed rule\n")
        self.assertNotEqual(original, review.capture(config))
        record = (self.run / "review.md").read_text()
        self.assertTrue(record.startswith(before))
        self.assertIn("Fix candidate: CR-04", record)
        self.cli("md_review.py", "--run-dir", self.run, "--note-file", notes, "--rules", added, code=2)

    def test_codex_effective_mcp_restrictions_and_unknown_configuration_fail_closed(self):
        def answer(data):
            return subprocess.CompletedProcess([], 0, json.dumps(data), "")
        inventory = [{"name": "backlog", "enabled": True}, {"name": "playwright", "enabled": True}]
        effective = [{"name": "backlog", "enabled": True}, {"name": "playwright", "enabled": False}]
        with patch.object(launcher.subprocess, "run", side_effect=[answer(inventory), answer(effective), answer({"enabled_tools": list(launcher.BACKLOG_READ)})]):
            args = launcher.codex_mcp_overrides(self.project)
        self.assertIn("mcp_servers.playwright.enabled=false", args)
        self.assertIn("features.apps=false", args)
        self.assertTrue(any(a.startswith("mcp_servers.backlog.enabled_tools=") for a in args))
        for responses in ([answer(inventory), answer(inventory)],
                          [answer(inventory), answer(effective), answer({"enabled_tools": ["add_issue"]})],
                          [answer({"unrecognized": []})],
                          [answer([{"name": "plugin:unhandled", "enabled": True}])]):
            with patch.object(launcher.subprocess, "run", side_effect=responses), self.assertRaises(ValueError):
                launcher.codex_mcp_overrides(self.project)

    def test_resume_rejects_unrelated_session_and_failure_is_recorded_without_retry(self):
        self.init()
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", "--resume", "unrelated", code=2)
        fakebin = self.temp / "bin"
        fakebin.mkdir()
        fake = fakebin / "claude"
        fake.write_text("#!/usr/bin/python3\nimport sys\nsys.stdin.read()\nprint('invalid response')\nsys.exit(1)\n")
        fake.chmod(0o700)
        env = {**os.environ, "PATH": str(fakebin) + ":" + os.environ["PATH"]}
        self.cli("start_md_review.py", "--run-dir", self.run, "--phase", "cr", code=2, env=env)
        records = list(self.run.glob("*/execution.json"))
        self.assertEqual(1, len(records))
        self.assertEqual("BLOCKED", json.loads(records[0].read_text())["status"])
        self.assertIn("BLOCKED", (self.run / "review.md").read_text())


if __name__ == "__main__":
    unittest.main()
