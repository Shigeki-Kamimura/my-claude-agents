"""一括保存の固定期間と入力保護、新規起動の権限制限を確認します。"""

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"
SINCE = "2026-11-02T01:00:00Z"
UNTIL = "2026-11-02T01:01:00Z"


class CaptureTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.log = self.root / "parent.jsonl"
        self.out = self.root / "record"
        self.usage = {"type": "token_usage_record", "timestamp": SINCE, "payload": {
            "response_id": "r1", "usage": {"input_tokens": 100, "cached_input_tokens": 60,
                                           "output_tokens": 10, "total_tokens": 110}}}
        self.log.write_text(json.dumps(self.usage) + "\n")

    def cli(self, tool, *args, code=0, env=None):
        result = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / tool), *map(str, args)],
                                capture_output=True, text=True, env=env)
        self.assertEqual(code, result.returncode, result.stderr)
        return result

    def capture(self, *args, code=0):
        return self.cli("capture_codex_review.py", "--parent", self.log, "--since", SINCE,
                        "--until", UNTIL, "--out-dir", self.out, *args, code=code)

    def test_capture_uses_same_window_redacts_and_omits_private_messages(self):
        def message(text, **fields):
            return {"type": "response_item", "timestamp": SINCE, "payload": {
                "type": "message", "role": "assistant", "phase": "final",
                "content": [{"type": "output_text", "text": text}], **fields}}
        rows = [self.usage, message("password=supersecret"), message("hidden analysis", phase="analysis"),
                message("hidden system", role="system"), {"type": "response_item", "timestamp": SINCE,
                "payload": {"type": "reasoning", "summary": [{"text": "hidden reasoning"}]}},
                {**message("outside window"), "timestamp": "2026-11-02T02:00:00Z"}]
        self.log.write_text("".join(json.dumps(row) + "\n" for row in rows))
        before = self.log.read_bytes()
        result = self.capture()
        self.assertLess(len(result.stdout), 400)
        usage = json.loads((self.out / "usage.json").read_text())
        self.assertEqual(110, usage["combined_tokens"]["total_tokens"])
        self.assertEqual("password=[REDACTED]", usage["sources"]["parent"]["final_message"])
        for path in self.out.iterdir():
            text = path.read_text()
            for forbidden in ("supersecret", "hidden analysis", "hidden system", "hidden reasoning", "outside window"):
                self.assertNotIn(forbidden, text)
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
        self.assertEqual(before, self.log.read_bytes())
        self.assertTrue((self.out / "index.html").is_file())
        self.assertIn('href="parent-result.md"', (self.out / "index.html").read_text())

    def test_child_and_missing_usage_remain_distinct_without_inventing_totals(self):
        child = self.root / "child.jsonl"
        child.write_text(json.dumps({"type": "event_msg", "timestamp": SINCE,
            "payload": {"type": "task_complete", "last_agent_message": "APPROVE"}}) + "\n")
        self.capture("--child", f"react={child}")
        usage = json.loads((self.out / "usage.json").read_text())
        self.assertIsNone(usage["combined_tokens"])
        self.assertEqual("NOT_AVAILABLE", usage["sources"]["react"]["status"])
        self.assertEqual("APPROVE\n", (self.out / "react-result.md").read_text())

    def test_existing_destination_alias_and_bad_usage_fail_without_overwrite(self):
        before = self.log.read_bytes()
        self.capture("--child", f"duplicate={self.log}", code=2)
        self.assertFalse(self.out.exists())
        self.capture("--child", f"../escape={self.log}", code=2)
        self.assertFalse(self.out.exists())
        self.usage["payload"]["usage"]["total_tokens"] = 999
        self.log.write_text(json.dumps(self.usage) + "\n")
        self.capture(code=2)
        self.assertFalse(self.out.exists())
        self.log.write_bytes(before)
        self.out.mkdir()
        marker = self.out / "keep.txt"
        marker.write_text("keep")
        self.capture(code=2)
        self.assertEqual("keep", marker.read_text())

    def test_malformed_tail_is_partial_and_repo_output_is_rejected(self):
        with self.log.open("a") as stream:
            stream.write('{"broken":')
        self.capture()
        usage = json.loads((self.out / "usage.json").read_text())
        self.assertEqual("PARTIAL", usage["sources"]["parent"]["status"])
        repo = self.root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        self.out = repo / "record"
        self.capture(code=2)
        self.assertFalse(self.out.exists())

    def test_fresh_launcher_preserves_request_sandbox_exit_and_existing_output(self):
        request = self.root / "request.txt"
        request.write_text("adv: inspect the specified snapshot\n")
        stub = self.root / "codex"
        stub.write_text('#!/usr/bin/env python3\nimport json,sys,pathlib\n'
                        'print(json.dumps({"args":sys.argv[1:],"request":sys.stdin.read(),"cwd":str(pathlib.Path.cwd())}))\n'
                        'pathlib.Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text("DEFER")\n'
                        'sys.exit(7)\n')
        stub.chmod(0o700)
        env = {**os.environ, "PATH": str(self.root) + os.pathsep + os.environ["PATH"]}
        args = ("--project", self.root, "--request-file", request, "--out-dir", self.out)
        self.cli("start_codex_review.py", *args, code=7, env=env)
        event = json.loads((self.out / "stream.jsonl").read_text())
        self.assertEqual(request.read_text(), event["request"])
        self.assertEqual(str(self.root), event["cwd"])
        self.assertEqual(["exec", "--cd", str(self.root), "--sandbox", "read-only", "--json",
                          "--output-last-message", str(self.out / "result.md"), "-"], event["args"])
        self.assertEqual(7, json.loads((self.out / "execution.json").read_text())["exit_code"])
        self.cli("start_codex_review.py", *args, code=2, env=env)
        self.assertEqual("DEFER", (self.out / "result.md").read_text())


if __name__ == "__main__":
    unittest.main()
