"""実行担当・変更範囲・環境再利用の指示を静的に確認します。"""

from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """同じ階層以上の見出しまでを取り出します。"""
    marker = heading + "\n"
    if text.count(marker) != 1:
        raise ValueError(f"見出しが一意ではありません: {heading}")
    body = text.split(marker, 1)[1]
    level = len(heading.split(" ", 1)[0])
    end = re.search(r"(?m)^#{1," + str(level) + r"} ", body)
    return body[:end.start()] if end else body


class TargetedVerificationTests(unittest.TestCase):
    def setUp(self):
        self.parent = read(".codex/AGENTS.md")
        self.policy = section(self.parent, "## Targeted verification and delegation")
        self.hq_config = tomllib.loads(read(".codex/agents/hq-coder.toml"))
        self.hq = self.hq_config["developer_instructions"]

    def test_policy_is_shared_with_delegates_without_changing_review_permissions(self):
        for text in ("authorized implementation-side verification", "local CI and Playwright",
                     "Pass the applicable rules and chosen test scope to delegated owners once",
                     "Read-only reviews remain read-only"):
            self.assertIn(text, self.policy)
        self.assertNotIn("When `multi_agent_v2`", self.policy)
        self.assertIn("In `claude-codex-review`, Codex remains a read-only review receiver", self.parent)
        self.assertEqual(self.hq_config["model"], "gpt-6.1-sol")
        self.assertEqual(self.hq_config["model_reasoning_effort"], "high")

    def test_execution_alone_does_not_create_a_new_agent(self):
        assignment = section(self.policy, "### Meaningful test assignments")
        for text in ("The parent HQ runs already-defined commands",
                     "Do not spawn a new agent solely to run tests, prepare the test environment",
                     "Duration, parallel command execution, and a fresh task title",
                     "An existing test author may run its own changed tests",
                     "Honor explicitly requested agent assignments within their permissions"):
            self.assertIn(text, assignment)
        self.assertIn("do not create a run-only QA/E2E/HQ child", self.hq)

    def test_consultation_requires_work_and_preserves_mandatory_reviews(self):
        assignment = section(self.policy, "### Meaningful test assignments")
        for text in ("concrete unresolved test-design question", "bounded test-code change",
                     "substantive failure analysis", "unchanged accepted plan",
                     "responsibility, phase and evidence set",
                     "Mandatory React/Nest consultation and independent QA/E2E/CR/ADV review"):
            self.assertIn(text, assignment)
        self.assertIn("A request for execution evidence alone stays with the authorized execution owner", self.hq)
        self.assertNotIn("- a review finding asks for test evidence", self.hq)

    def test_selection_includes_affected_dependencies_and_actual_runner_results(self):
        selection = section(self.policy, "### Select affected tests before execution")
        for text in ("callers/consumers, shared helpers, fixtures and configuration",
                     "not limited to edited test files", "happy/fail paths",
                     "wrapper/setup hooks", "selected tests actually ran",
                     "zero-match filter", "NOT_RUN/BLOCKED, not PASS",
                     "do not fall back to an unfiltered run"):
            self.assertIn(text, selection)

    def test_batching_keeps_source_bound_evidence_without_retesting_everything(self):
        selection = section(self.policy, "### Select affected tests before execution")
        for text in ("Batch cohesive edits", "Focused red/green runs",
                     "original source identity and a valid impact basis",
                     "Do not relabel old results for a new snapshot",
                     "Reapproval by each reviewer does not itself require rerunning every test"):
            self.assertIn(text, selection)
        self.assertNotIn("HQ does not own broad L0/L1 QA", self.hq)
        self.assertNotIn("unless explicitly requested or needed to unblock the edit", self.hq)
        self.assertIn("Follow `Targeted verification and delegation`", self.hq)

    def test_full_suite_needs_request_or_gate_not_an_automatic_fallback(self):
        selection = section(self.policy, "### Select affected tests before execution")
        for text in ("Run a full suite only for an explicit user request",
                     "cited mandatory project/release gate at the point it applies",
                     "Shared-code changes first expand the affected set",
                     "obtain a scope decision before a full run",
                     "Do not weaken mandatory CI gates"):
            self.assertIn(text, selection)

    def test_test_layers_keep_distinct_guarantees_without_duplicate_matrices(self):
        selection = section(self.policy, "### Select affected tests before execution")
        for text in ("lowest layer that proves the rule", "distinct integration guarantees",
                     "Do not repeat the same matrix at every layer",
                     "Preserve genuinely different happy/fail obligations",
                     "test count alone is not a reduction criterion"):
            self.assertIn(text, selection)

    def test_environment_reuse_preserves_isolation_and_rebuild_exceptions(self):
        environment = section(self.policy, "### Reuse safe test environments")
        for text in ("Reuse the existing authorized worktree", "compatible with the target source",
                     "deterministic setup/teardown", "Do not create a fresh sandbox/worktree",
                     "concrete incompatibility, contamination, required isolation rule",
                     "smallest affected component first",
                     "never disables permission sandboxes, read-only controls or test isolation",
                     "never permits production/shared-data mutation or conflicting concurrent runs",
                     "NOT_RUN/FAILED/PARTIAL"):
            self.assertIn(text, environment)
        self.assertIn("do not recreate it per edit", self.hq)


if __name__ == "__main__":
    unittest.main()
