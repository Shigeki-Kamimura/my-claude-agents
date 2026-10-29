#!/usr/bin/env python3
"""Codex→Claudeレビュー専用の実行禁止設定を静的に検証します。"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ClaudeReviewExecutionBoundaryTests(unittest.TestCase):
    def test_cli_forbids_execution_tools(self):
        workflow = read(".codex/workflows/claude-review.yml")
        section = workflow.split("\nclaude_cli:\n", 1)[1].split("\nreview_entry:\n", 1)[0]
        match = re.search(r"(?ms)^  argv:\n((?:  - .*\n)+)", section)
        self.assertIsNotNone(match, "CLI引数が見つかりません")
        args = [line[4:] for line in match.group(1).splitlines()]
        mode = args.index("--permission-mode")
        self.assertEqual(args[mode + 1], "dontAsk")
        tools = args.index("--tools")
        self.assertEqual(set(args[tools + 1].split(",")), {"Read", "Glob", "Grep", "Agent"})
        denied = args[args.index("--disallowedTools") + 1:]
        self.assertTrue({"Bash", "Edit", "Write", "NotebookEdit", "mcp__*"}.issubset(set(denied)))
        self.assertNotIn("bypassPermissions", section)

    def test_workflow_assigns_every_execution_to_codex(self):
        workflow = read(".codex/workflows/claude-review.yml")
        self.assertIn("codex_execution_owner:", workflow)
        self.assertIn("qa_e2e:", workflow)
        self.assertIn("QA/E2EもRead/Glob/Grep", workflow)
        self.assertIn("初回と--resumeの全回", workflow)
        self.assertNotIn("必要な検証を判断・実行できます", workflow)

    def test_both_profiles_inherit_review_only_contract(self):
        for profile in (".claude", ".claude-company"):
            with self.subTest(profile=profile):
                parent = read(f"{profile}/CLAUDE.md")
                governance = read(f"{profile}/knowledge/engineering-governance.md")
                self.assertIn("codex-claude-review", parent)
                self.assertIn("Codex exclusively runs typecheck", parent)
                self.assertIn("codex-claude-review", governance)
                self.assertIn("Codex/HQ alone gathers Git", governance)
                for name in ("code-quality-reviewer", "adviser", "test-qa", "e2e-qa"):
                    owner = read(f"{profile}/agents/{name}.md")
                    self.assertIn("codex-claude-review", owner)
                    self.assertIn("Codex", owner)
                    self.assertTrue("Never" in owner or "forbidden" in owner)

    def test_reverse_workflow_still_has_its_own_owner(self):
        reverse = read(".codex/workflows/codex-review.yml")
        self.assertIn("claude-codex-review", reverse)
        self.assertIn("Claude Codeが修正と必要な検証を行い", reverse)


if __name__ == "__main__":
    unittest.main()
