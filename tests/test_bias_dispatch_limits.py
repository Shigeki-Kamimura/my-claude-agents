"""BIAS-1の来歴管理、Claude利用量ガード、継続優先とreview_state_digestを確認します。"""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_md_review as fixtures
import test_md_review_flow as flow

launcher, review = fixtures.launcher, fixtures.review
ROOT = Path(launcher.__file__).resolve().parents[1]
provenance = review.provenance
sdigest = launcher.sdigest

spec = importlib.util.spec_from_file_location("sync_engineering_preloads", ROOT / "tools/sync_engineering_preloads.py")
preloads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preloads)

SIGNED = """Fix the null check in code.txt.
Requirement: reject empty names (REQ-7).

```python
note = "Co-Authored-By: kept inside code"
```

Generated with openapi-generator 7.1
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
> Co-authored-by: Codex <noreply@openai.com>
This change was written by Claude.
Implemented by an AI assistant.
"""


class SanitizerTests(unittest.TestCase):
    def test_signatures_are_removed_but_code_and_requirements_stay(self):
        cleaned, removed = provenance.strip_author_signatures(SIGNED)
        self.assertEqual(5, removed)
        for gone in ("🤖", "Claude Code", "noreply@anthropic.com", "noreply@openai.com", "written by Claude", "Implemented by an AI"):
            self.assertNotIn(gone, cleaned)
        self.assertIn("Requirement: reject empty names (REQ-7).", cleaned)
        self.assertIn('note = "Co-Authored-By: kept inside code"', cleaned)  # fenced codeは変更しない
        self.assertIn("Generated with openapi-generator 7.1", cleaned)  # AIツールの署名ではない

    def test_unsigned_text_is_unchanged_apart_from_outer_whitespace(self):
        text = "Plain request.\n\n  indented code line\n"
        self.assertEqual(("Plain request.\n\n  indented code line", 0), provenance.strip_author_signatures(text))

    def test_init_strips_summary_and_note_before_storing_and_records_count(self):
        case = SummaryCases()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.summary.write_text("User request: review cr only\nRequirement: REQ-7\n\nCo-Authored-By: Claude <x@example.test>\n🤖 Generated with Claude Code\n")
        result = case.init()
        journal = (case.run / "review.md").read_text()
        self.assertNotIn("Co-Authored-By", journal)
        self.assertNotIn("🤖", journal)
        self.assertIn("Requirement: REQ-7", journal)
        self.assertEqual(2, review.load_run(case.run)[1]["provenance_stripped_lines"])
        self.assertIn("署名行を2行", result.stderr)
        note = case.cli_input("--run-dir", case.run, "--note-stdin", stdin="Fixed REQ-7.\nCo-Authored-By: Claude <x@example.test>\n")
        self.assertNotIn("Co-Authored-By", (case.run / "review.md").read_text())
        self.assertIn("署名行を1行", note.stderr)

    def test_legacy_run_without_new_fields_is_valid_and_malformed_values_are_rejected(self):
        case = SummaryCases()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.init()
        config = review.load_run(case.run)[1]
        self.assertNotIn("author_model", config)
        self.assertNotIn("claude_usage", config)  # 1層・adv以外は記録しない
        self.assertEqual(("codex", "direction"), provenance.effective_author_model(config))
        shutil_run = case.temp / "run2"
        bad = case.cli("md_review.py", "--project", case.project, "--base", case.base, "--direction", "codex-claude-review",
                       "--layers", "cr", "--paths", "code.txt", "new.txt", "--rules", case.project / "rule.md",
                       "--summary-file", case.summary, "--out-dir", shutil_run, "--author-model", "gpt-9", code=2)
        self.assertFalse(shutil_run.exists())
        self.assertIn("invalid choice", bad.stderr)
        case.cli("md_review.py", "--project", case.project, "--base", case.base, "--direction", "codex-claude-review",
                 "--layers", "cr", "--paths", "code.txt", "new.txt", "--rules", case.project / "rule.md",
                 "--summary-file", case.summary, "--out-dir", shutil_run, "--claude-usage-before", "line1\nline2", code=2)
        self.assertFalse(shutil_run.exists())


class SummaryCases(unittest.TestCase):
    setUp = fixtures.MDReviewTests.setUp
    git = fixtures.MDReviewTests.git
    cli = fixtures.MDReviewTests.cli
    init = fixtures.MDReviewTests.init

    def runTest(self):
        pass

    def cli_input(self, *args, stdin):
        import subprocess
        result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/md_review.py"), *map(str, args)],
                                text=True, capture_output=True, input=stdin)
        self.assertEqual(0, result.returncode, result.stderr)
        return result


class IndependenceTests(unittest.TestCase):
    def test_same_model_is_self_check_and_different_is_cross_model(self):
        claude = {"direction": "claude-codex-review", "author_model": "claude"}
        self.assertEqual("self_check", provenance.independence_record(claude, {"platform": "Claude Code", "model": "claude-sonnet-5-5"})["review_independence"])
        self.assertEqual("cross_model", provenance.independence_record(claude, {"platform": "Codex", "model": "gpt-5"})["review_independence"])
        by_direction = {"direction": "codex-claude-review"}
        record = provenance.independence_record(by_direction, {"platform": "Claude Code", "model": "fixture"})
        self.assertEqual(("codex", "direction", "claude", "cross_model"),
                         (record["author_model"], record["author_model_source"], record["reviewer_model"], record["review_independence"]))
        # codex-claude-reviewのciはCodexがCodex作を見るためself_checkとして記録する
        self.assertEqual("self_check", provenance.independence_record(by_direction, {"platform": "Codex", "model": "gpt-5"})["review_independence"])
        for author in ("human", "unknown"):
            self.assertEqual("unknown", provenance.independence_record({"author_model": author}, {"platform": "Codex", "model": "gpt-5"})["review_independence"])

    def test_host_records_independence_without_changing_the_eleven_fields(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        _, records, meta = case.claude_round("ok", code=0)
        self.assertEqual("cross_model", meta["review_independence"])
        self.assertEqual(("codex", "claude"), (meta["author_model"], meta["reviewer_model"]))
        state = json.loads((case.run / "state.json").read_text())
        result = state["phases"]["cr"]["last_valid"]["result"]
        self.assertEqual(11, len(result))
        self.assertNotIn("reviewer_model", result)


class Flow(unittest.TestCase):
    setUp = fixtures.MDReviewTests.setUp
    git = fixtures.MDReviewTests.git
    cli = fixtures.MDReviewTests.cli
    init = fixtures.MDReviewTests.init

    FAKE_CLAUDE = flow.MDReviewFlowTests.FAKE_CLAUDE.replace(
        'mode=os.environ["FAKE_MODE"]\n',
        'mode=os.environ["FAKE_MODE"]\n'
        'if mode=="paraphrase429":\n'
        '    sys.stderr.write("retrying after 429 rate limit\\n")\n'
        '    mode="paraphrase"\n'
        'if mode=="ratelimit":\n'
        '    print(json.dumps({"type":"result","is_error":True,"api_error_status":429,"session_id":"parent-X","result":"You\'ve hit your limit \\u00b7 resets 2pm (Asia/Tokyo)"}))\n'
        '    sys.exit(1)\n', 1)
    claude_round = flow.MDReviewFlowTests.claude_round

    def runTest(self):
        pass

    def later_round(self, gap, extra=(), child_rows=(), summary=None):
        """1回目の後、前回終了からgap秒後に同phaseを再実行します(フラグ未指定なら実際の既定を使います)。"""
        if summary is not None:
            self.summary.write_text(summary)
        env, records, _ = self.claude_round("ok", code=0)
        first = records[-1]
        meta = json.loads(first.read_text())
        meta["finished_at"] = "2026-01-01T00:00:00+00:00"
        first.write_text(json.dumps(meta))
        with Path(env["FAKE_CHILD"]).open("a") as child:
            for row in child_rows:
                child.write(json.dumps(row) + "\n")
        argv_file = self.temp / "argv.json"
        env["FAKE_ARGV"] = str(argv_file)
        now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=gap)
        args = ["start_md_review.py", "--run-dir", str(self.run), "--phase", "cr", *extra]
        with patch.dict(os.environ, env), patch.object(sys, "argv", args), patch.object(launcher, "utc_now", lambda: now):
            code = launcher.main()
        newest = max((p for p in self.run.glob("*/execution.json") if p != first), key=lambda p: p.stat().st_mtime_ns)
        argv = json.loads(argv_file.read_text()) if argv_file.exists() else None
        return code, argv, json.loads(newest.read_text()), newest.parent, json.loads(first.read_text())


def usage_row(tokens):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": "x"}],
                                              "usage": {"input_tokens": 5, "cache_read_input_tokens": tokens, "cache_creation_input_tokens": 0}}}


class ContinuityTests(unittest.TestCase):
    def flow(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def test_default_resumes_even_after_a_long_gap(self):
        self.assertEqual(0, launcher.FRESH_AFTER_SECONDS)
        code, argv, meta, _, _ = self.flow().later_round(10 * 3600)
        self.assertEqual(0, code)
        self.assertIn("--resume", argv)
        self.assertEqual("resume", meta["owner_continuity"]["decision"])
        self.assertEqual("resumed_ttl_disabled", meta["owner_continuity"]["mode"])
        self.assertNotIn("review_state_digest_sha256", meta["briefing"])

    def test_print_briefing_default_does_not_start_fresh_after_a_long_gap(self):
        case = self.flow()
        case.claude_round("ok", code=0)
        first = next(case.run.glob("*/execution.json"))
        meta = json.loads(first.read_text())
        meta["finished_at"] = "2026-01-01T00:00:00+00:00"
        first.write_text(json.dumps(meta))
        now = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
        import io
        out = io.StringIO()
        with patch.object(sys, "argv", ["start_md_review.py", "--run-dir", str(case.run), "--phase", "cr", "--print-briefing"]), \
                patch.object(launcher, "utc_now", lambda: now), patch("sys.stdout", out):
            launcher.main()
        report = json.loads(out.getvalue().rsplit("---\n", 1)[1])
        self.assertEqual("resume", report["owner_continuity"]["decision"])
        self.assertNotIn("REVIEW_STATE_DIGEST", out.getvalue())

    def test_context_above_cap_starts_fresh_with_digest_and_below_cap_resumes(self):
        code, argv, meta, round_dir, _ = self.flow().later_round(5, child_rows=[usage_row(200000)])
        self.assertEqual(0, code)
        self.assertNotIn("--resume", argv)
        continuity = meta["owner_continuity"]
        self.assertEqual(("fresh_over_context_cap", 200005, launcher.FRESH_ABOVE_TOKENS), (continuity["mode"], continuity["context_tokens"], continuity["context_cap_tokens"]))
        briefing = (round_dir / "briefing.md").read_text()
        self.assertIn("<<REVIEW_STATE_DIGEST sha256=" + meta["briefing"]["review_state_digest_sha256"], briefing)
        self.assertIn(launcher.FRESH_OWNER_NOTICE, briefing)
        code, argv, meta, _, _ = self.flow().later_round(5, child_rows=[usage_row(200000)], extra=["--fresh-above-tokens", "250000"])
        self.assertEqual("resume", meta["owner_continuity"]["decision"])
        self.assertIn("--resume", argv)
        code, argv, meta, _, _ = self.flow().later_round(5, child_rows=[usage_row(200000)], extra=["--fresh-above-tokens", "0"])
        self.assertEqual("resume", meta["owner_continuity"]["decision"])

    def test_unknown_context_size_resumes_without_guessing(self):
        _, argv, meta, _, _ = self.flow().later_round(5)
        self.assertIsNone(meta["owner_continuity"]["context_tokens"])
        self.assertIn("--resume", argv)

    def test_fresh_digest_without_recorded_reads_still_works_and_credits_nothing(self):
        # 旧state(digest関連のキーなし)と転記にRead記録がない場合でも、TTL任意設定のfreshは従来どおり動く
        code, argv, meta, round_dir, _ = self.flow().later_round(600, extra=["--fresh-after-seconds", "300"])
        self.assertEqual(0, code)
        self.assertEqual("fresh_after_ttl", meta["owner_continuity"]["mode"])
        briefing = (round_dir / "briefing.md").read_text()
        digest = json.loads(briefing.split("<<REVIEW_STATE_DIGEST", 1)[1].split(">>\n", 1)[1].split("\n<<END REVIEW_STATE_DIGEST>>", 1)[0])
        self.assertEqual([], digest["files_read"])
        self.assertTrue(all(row["credit"] == "none_read_in_full" for row in digest["rules_manifest"]))
        self.assertNotIn("digest", json.loads((round_dir.parent / "state.json").read_text()))

    def test_digest_lists_predecessor_reads_for_unchanged_rules_and_is_in_context(self):
        case = self.flow()
        rule = str((case.project / "rule.md").resolve())
        code, _, meta, round_dir, first = case.later_round(
            5, extra=["--fresh-above-tokens", "100"], child_rows=[
                usage_row(500),
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": rule, "offset": 1, "limit": 80}}]}},
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": str(case.project / "code.txt")}}]}}])
        self.assertEqual(0, code)
        context = json.loads((round_dir / "context.json").read_text())
        self.assertEqual(meta["briefing"]["review_state_digest_sha256"], context["request"]["review_state_digest"]["sha256"])
        # 実reviewerが読むreview_context(current)にdigest本体(規則manifestとRead台帳)が入る
        current = review.review_context(round_dir, "current")["text"]
        self.assertIn('"rules_manifest"', current)
        self.assertIn(rule, current)
        self.assertEqual(json.loads(current)["review_state_digest"]["digest"]["rules_manifest"][0]["path"], rule)
        briefing = (round_dir / "briefing.md").read_text()
        digest = json.loads(briefing.split("<<REVIEW_STATE_DIGEST", 1)[1].split(">>\n", 1)[1].split("\n<<END REVIEW_STATE_DIGEST>>", 1)[0])
        row = next(r for r in digest["rules_manifest"] if r["path"] == rule)
        self.assertEqual(("unchanged", [[1, 80]], "predecessor_read_supplied"), (row["status"], row["predecessor_read_requests"], row["credit"]))
        self.assertEqual(["code.txt"], [Path(f["path"]).name for f in digest["files_read"]])
        snapshot = json.loads((Path(first["artifacts"]) / "snapshot.json").read_text())
        expected = next(sha for p, view, _mode, sha in snapshot["paths"] if p == "code.txt" and view == "worktree")
        self.assertEqual(expected, digest["files_read"][0]["blob_sha256_at_predecessor_snapshot"])
        self.assertEqual({"finding_ids": ["CR-01"], "handoffs": {"E2E-H1": {"owner": "e2e-qa", "status": "open", "weight": "🟢"}}}, digest["open_items"])

    def test_digest_is_deterministic_and_does_not_credit_a_changed_rule(self):
        old = {"snapshot_id": "S1", "paths": [["a.py", "worktree", "100644", "h1"]], "rules": [["/r/CLAUDE.md", "sha-old"], ["/r/other.md", "sha-same"]]}
        reads = {"/r/CLAUDE.md": [[1, 100], [None, None]], "/r/other.md": [[1, 50]], "/p/a.py": [[10, 20]]}
        args = ("/p", old, [["/r/CLAUDE.md", "sha-NEW"], ["/r/other.md", "sha-same"]], "S2", ["a.py"], ["/r/CLAUDE.md"], reads,
                {"parent_session_id": "P", "reviewer_id": "C"}, {"start": 0, "length": 1, "sha256": "x"}, ["CR-02", "CR-01"], {})
        first, second = sdigest.build(*args), sdigest.build(*args)
        self.assertEqual(first, second)
        digest = json.loads(first[0])
        manifest = {r["path"]: r for r in digest["rules_manifest"]}
        self.assertEqual(("changed", [], "none_read_in_full"), (manifest["/r/CLAUDE.md"]["status"], manifest["/r/CLAUDE.md"]["predecessor_read_requests"], manifest["/r/CLAUDE.md"]["credit"]))
        self.assertEqual(("unchanged", [[1, 50]]), (manifest["/r/other.md"]["status"], manifest["/r/other.md"]["predecessor_read_requests"]))
        self.assertEqual(["CR-01", "CR-02"], digest["open_items"]["finding_ids"])
        self.assertEqual("a.py", digest["files_read"][0]["path"].split("/p/")[-1])
        self.assertEqual("h1", digest["files_read"][0]["blob_sha256_at_predecessor_snapshot"])
        self.assertEqual(["a.py"], digest["delta"]["changed_paths"])

    def test_round_two_resume_briefing_is_smaller_than_round_one_and_inlines_no_history(self):
        case = self.flow()
        big = "User request: review cr only\n" + "Acceptance criterion line.\n" * 200
        code, argv, second, round_dir, first = case.later_round(5, summary=big)
        self.assertIn("--resume", argv)
        self.assertGreater(first["briefing"]["chars"], second["briefing"]["chars"])
        self.assertGreater(first["briefing"]["chars"] - second["briefing"]["chars"], len(big) // 2)
        self.assertEqual([], second["briefing"]["inlined"])
        briefing = (round_dir / "briefing.md").read_text()
        self.assertNotIn("Acceptance criterion line.", briefing)
        self.assertNotIn("REVIEW_STATE_DIGEST", briefing)  # 再開した担当にdigestは不要
        self.assertNotIn("\nrule\n", briefing)  # 規則ファイルの本文は同梱しない(pathだけ)
        self.assertEqual(["current"], json.loads((round_dir / "context.json").read_text())["request"]["reading_plan"]["required_sections"])


class UsageGuardTests(unittest.TestCase):
    def test_cost_class_and_usage_record(self):
        self.assertEqual("high", provenance.estimate_cost_class(["adv"], 1))
        self.assertEqual("high", provenance.estimate_cost_class(["qa", "cr"], 30))
        self.assertEqual("medium", provenance.estimate_cost_class(["qa", "cr"], 3))
        self.assertEqual("medium", provenance.estimate_cost_class(["cr"], 30))
        self.assertEqual("low", provenance.estimate_cost_class(["cr"], 3))
        self.assertEqual({"claude_usage": "unknown"}, provenance.usage_record(None, "codex-claude-review", ["cr", "adv"]))
        self.assertEqual({}, provenance.usage_record(None, "codex-claude-review", ["cr"]))
        self.assertEqual({}, provenance.usage_record(None, "claude-codex-review", ["cr", "adv"]))
        self.assertEqual({"claude_usage_before": "62% of window, resets 14:00 JST"},
                         provenance.usage_record(" 62% of window, resets 14:00 JST ", "codex-claude-review", ["cr", "adv"]))
        self.assertEqual({"claude_usage": "unknown"}, provenance.usage_record("Unknown", "codex-claude-review", ["cr"]))
        with self.assertRaises(ValueError):
            provenance.usage_record("a\nb", "codex-claude-review", ["cr"])

    def test_unknown_usage_starts_only_the_first_layer_until_user_confirms(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.init("--layers", "cr", "qa")
        self.assertEqual("unknown", review.load_run(case.run)[1]["claude_usage"])
        env, records, _ = case.claude_round("ok", code=0)
        self.assertEqual(1, len(records))
        marker = case.temp / "started"
        env["FAKE_MARKER"] = str(marker)
        stopped = case.cli("start_md_review.py", "--run-dir", case.run, "--phase", "qa", code=2, env=env)
        self.assertIn("--confirm-more-layers", stopped.stderr)
        self.assertIn("推定コスト区分=", stopped.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(1, len(list(case.run.glob("*/execution.json"))))
        case.cli("start_md_review.py", "--run-dir", case.run, "--phase", "qa", "--confirm-more-layers", code=2, env=env)
        self.assertTrue(marker.exists())  # ゲートを通り、qaが起動された(判定欄の照合結果は別問題)

    def test_recorded_usage_reading_does_not_gate_additional_layers(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.init("--layers", "cr", "qa", "--claude-usage-before", "62% of window, resets 14:00 JST")
        config = review.load_run(case.run)[1]
        self.assertEqual("62% of window, resets 14:00 JST", config["claude_usage_before"])
        self.assertNotIn("claude_usage", config)
        env, _, _ = case.claude_round("ok", code=0)
        marker = case.temp / "started"
        env["FAKE_MARKER"] = str(marker)
        case.cli("start_md_review.py", "--run-dir", case.run, "--phase", "qa", code=2, env=env)
        self.assertTrue(marker.exists())


class RateLimitTests(unittest.TestCase):
    def test_signal_requires_a_failed_end_and_ignores_reviews_that_mention_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            round_dir = Path(folder)
            ok = {"type": "result", "result": "Review of the 429 rate limit handling\n```workflow-result\n{}\n```", "is_error": False}
            (round_dir / "stdout.jsonl").write_text(json.dumps(ok) + "\n")
            (round_dir / "stderr.log").write_text("")
            self.assertIsNone(launcher.rate_limit_signal(round_dir, 0))
            paraphrase = {"type": "result", "result": "You've hit your limit mention in prose without block", "is_error": False}
            (round_dir / "stdout.jsonl").write_text(json.dumps(paraphrase) + "\n")
            self.assertIsNone(launcher.rate_limit_signal(round_dir, 0))  # 正常終了は上限として扱わない
            tool_noise = {"type": "user", "message": {"content": "HTTP 429 too many requests in source"}}
            (round_dir / "stdout.jsonl").write_text(json.dumps(tool_noise) + "\n")
            self.assertIsNone(launcher.rate_limit_signal(round_dir, 1))  # 失敗でも、上限のシグナルはない
            limited = {"type": "result", "is_error": True, "result": "You've hit your limit · resets 2pm (Asia/Tokyo)"}
            (round_dir / "stdout.jsonl").write_text(json.dumps(limited) + "\n")
            signal = launcher.rate_limit_signal(round_dir, 1)
            self.assertEqual("2pm (Asia/Tokyo)", signal["reset_hint"])
            (round_dir / "stdout.jsonl").write_text("")
            (round_dir / "stderr.log").write_text("Claude AI usage limit reached|1767225600\n")
            self.assertIn("2026-01-01T00:00:00", launcher.rate_limit_signal(round_dir, 1)["reset_hint"])
            (round_dir / "stderr.log").write_text("API Error: 429 rate_limit_error\n")
            self.assertIsNone(launcher.rate_limit_signal(round_dir, 1)["reset_hint"])

    def test_internally_retried_429_notice_does_not_block_child_verbatim_recovery(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        _, _, meta = case.claude_round("paraphrase429", code=0)
        self.assertEqual(("child_verbatim", "REVIEWED"), (meta["result_source"], meta["status"]))
        self.assertNotIn("rate_limit", json.loads((case.run / "state.json").read_text()))
        self.assertIn("429", (next(case.run.glob("*/stderr.log"))).read_text())

    def test_rate_limited_round_is_recorded_without_retry_and_next_dispatch_needs_ack(self):
        case = Flow()
        case.setUp()
        self.addCleanup(case.doCleanups)
        env, records, meta = case.claude_round("ratelimit", code=3)
        self.assertEqual(("RATE_LIMITED", "rate_limited", "2pm (Asia/Tokyo)"), (meta["status"], meta["failure"], meta["reset_hint"]))
        self.assertEqual(1, len(records))
        state = json.loads((case.run / "state.json").read_text())
        self.assertEqual("RATE_LIMITED", state["phases"]["cr"]["status"])
        self.assertEqual("2pm (Asia/Tokyo)", state["rate_limit"]["reset_hint"])
        self.assertIn("RATE_LIMITED", (case.run / "review.md").read_text())
        # ack無しの次の起動は何も作らず拒否する
        marker = case.temp / "started"
        env["FAKE_MARKER"] = str(marker)
        env["FAKE_MODE"] = "ok"
        stopped = case.cli("start_md_review.py", "--run-dir", case.run, "--phase", "cr", code=2, env=env)
        self.assertIn("--after-rate-limit-ack", stopped.stderr)
        self.assertIn("2pm (Asia/Tokyo)", stopped.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(1, len(list(case.run.glob("*/execution.json"))))
        self.assertEqual(1, len([p for p in case.run.iterdir() if p.is_dir()]))
        # 利用者のackの後は再開でき、記録はackとして残る
        case.cli("start_md_review.py", "--run-dir", case.run, "--phase", "cr", "--after-rate-limit-ack", code=0, env=env)
        state = json.loads((case.run / "state.json").read_text())
        self.assertNotIn("rate_limit", state)
        self.assertEqual(1, len(state["rate_limit_acks"]))
        self.assertTrue(marker.exists())


class CodexLauncherSanitizeTests(unittest.TestCase):
    def test_start_codex_review_strips_signatures_but_leaves_unsigned_requests_verbatim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stub = root / "codex"
            stub.write_text('#!/usr/bin/env python3\nimport json,sys,pathlib\n'
                            'print(json.dumps({"request":sys.stdin.read()}))\n'
                            'pathlib.Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text("DEFER")\n')
            stub.chmod(0o700)
            env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
            import subprocess
            signed = root / "signed.txt"
            signed.write_text("adv: inspect snapshot X\nRequirement REQ-1\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\nCo-Authored-By: Claude <n@example.test>\n")
            plain = root / "plain.txt"
            plain.write_text("adv: inspect snapshot Y\n")
            seen = {}
            for name, request in (("signed", signed), ("plain", plain)):
                out = root / name
                done = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tools/start_codex_review.py"), "--project", str(root),
                                       "--request-file", str(request), "--out-dir", str(out)], text=True, capture_output=True, env=env)
                self.assertEqual(0, done.returncode, done.stderr)
                seen[name] = (json.loads((out / "stream.jsonl").read_text())["request"], (out / "request.txt").read_text(), done.stderr)
            self.assertEqual("adv: inspect snapshot X\nRequirement REQ-1\n", seen["signed"][0])
            self.assertEqual(seen["signed"][0], seen["signed"][1])
            self.assertIn("署名行を2行", seen["signed"][2])
            self.assertEqual(plain.read_text(), seen["plain"][0])  # 署名がなければ逐語のまま


class ContractTextTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_dispatch_limits_are_in_both_workflows_and_the_common_contract(self):
        claude = self.read(".codex/workflows/claude-review.yml")
        limits = claude.split("\ndispatch_limits:\n", 1)[1].split("\nhandoff:\n", 1)[0]
        for key in ("redispatch", "layers_cap", "sequential", "usage_reading", "cost_classes", "rate_limit", "enforced_by_tool"):
            self.assertIn("  " + key + ":", limits)
        for text in ("without a new user request", "Only three prohibitions apply.", "(1) Blind retries after a usage-limit signal.",
                     "(2) Launching layers beyond user selection.", "(3) More than three repair rounds without reporting the cause.", "claude_usage_before",
                     "--confirm-more-layers", "--after-rate-limit-ack", "no retry or additional child launch.", "model/effort stay unchanged."):
            self.assertIn(text, limits)
        self.assertNotIn("blind restarts after failure", limits)  # 一般の再起動禁止ではない
        self.assertIn("without a new user request", self.read(".codex/workflows/codex-review.yml"))
        self.assertIn("dispatch_limits:", self.read(".codex/workflows/codex-review.yml"))
        # eleven Workflow Result fieldsの検査範囲(response_contract〜pause_and_resume)にdispatch_limitsが入り込まない
        fields = claude.split("response_contract:\n", 1)[1].split("pause_and_resume:\n", 1)[0]
        self.assertNotIn("dispatch_limits", fields)
        common = self.read(".codex/workflows/md-review.md")
        for text in ("may automatically restart re-review without a new user request", "Only these three dispatch actions are prohibited", "## 利用量の上限とBIAS-1の来歴管理", "RATE_LIMITED", "claude_usage: unknown", "--author-model", "self_check"):
            self.assertIn(text, common)
        self.assertNotIn("利用量の上限とBIAS-1", claude.split("review_entry:", 1)[1].split("role_sections:", 1)[1].split("required_intake", 1)[0])

    def test_continuity_first_contract_and_unverified_cache_ttl_are_stated(self):
        common = self.read(".codex/workflows/md-review.md")
        for text in ("Continuity first (default)", "defaults to 0 (disabled)", "--fresh-above-tokens", "review_state_digest", "Prior approvals and judgments do not transfer",
                     "Actual token savings are unmeasured", "Neither offer it as an option nor claim it works", "never on a first pass"):
            self.assertIn(text, common)
        self.assertNotIn("defaults to 300", common)

    def test_bias1_is_in_lenses_and_codex_core_only_and_xrev1_is_intact(self):
        heading = "### BIAS-1: Provenance and self-preference controls"
        lenses = preloads.render(ROOT, "engineering-review-lenses")
        xrev = preloads.section(self.read(".claude/knowledge/engineering-governance.md"), "XREV-1: Cross-model review calibration lenses")
        bias = preloads.section(self.read(".claude/knowledge/engineering-governance.md"), "BIAS-1: Provenance and self-preference controls")
        self.assertEqual(1, lenses.count(bias))
        self.assertEqual(1, lenses.count(xrev))
        self.assertIn("BIAS-1", lenses.split("---", 2)[1])
        codex = preloads.render(ROOT, "engineering-review-core", "codex")
        self.assertEqual(1, codex.count(heading))
        self.assertEqual(1, codex.count("### XREV-1:"))
        self.assertLess(codex.index("### XREV-1:"), codex.index(heading))
        self.assertNotIn(heading, preloads.render(ROOT, "engineering-review-core"))
        for profile in preloads.PROFILES:
            self.assertEqual(preloads.render(ROOT, "engineering-review-lenses"), self.read(f"{profile}/skills/engineering-review-lenses/SKILL.md"))
        for phrase in ("not a measured effect", "do not claim to remove model bias", "style fingerprints", "`self_check`",
                       "disagreement between models is recorded as a disagreement", "never from who reported the finding"):
            self.assertIn(phrase, bias.replace("they do not claim", "do not claim"))
        self.assertLess(self.read(".claude/knowledge/engineering-governance.md").index(heading),
                        self.read(".claude/knowledge/engineering-governance.md").index("### Calibration examples"))
        self.assertGreater(self.read(".claude/knowledge/engineering-governance.md").index(heading),
                           self.read(".claude/knowledge/engineering-governance.md").index("### XREV-1:"))

    def test_governance_fresh_owner_sentence_keeps_first_pass_independent(self):
        governance = self.read(".claude/knowledge/engineering-governance.md")
        self.assertEqual(governance, self.read(".claude-company/knowledge/engineering-governance.md"))
        intake = governance.split("### Claude role-scoped intake", 1)[1].split("###", 1)[0]
        self.assertIn("the only exception is the host-built `review_state_digest` range credit", intake)
        self.assertIn("never as your own reading or an approval", intake)
        core = self.read(".claude/skills/engineering-review-core/SKILL.md")
        self.assertIn("the only exception is the host-built `review_state_digest` range credit", core)  # 注入される節にも届く
        self.assertIn("review_state_digest", self.read(".codex/workflows/claude-review.yml").split("rereview_reading:", 1)[1].split("rereview_inputs", 1)[0])
        for text in ("resuming the verified same-phase owner is the default", "`review_state_digest`", "never as its own approval or a transferred verdict",
                     "A first pass receives no digest"):
            self.assertIn(text, governance)


if __name__ == "__main__":
    unittest.main()
