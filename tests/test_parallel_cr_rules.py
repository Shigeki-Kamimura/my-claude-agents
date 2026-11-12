"""PCR-1の静的な配布・記載契約だけを確認します。"""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = Path(".claude/knowledge/parallel-cr-review.md")
SKILL_PATH = Path(".claude/skills/parallel-cr/SKILL.md")


class ParallelCrRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rule = (ROOT / RULE_PATH).read_text(encoding="utf-8")
        cls.skill = (ROOT / SKILL_PATH).read_text(encoding="utf-8")
        cls.guide = (ROOT / "docs/parallel-cr-review.md").read_text(encoding="utf-8")
        cls.cases = json.loads(
            (ROOT / "docs/examples/parallel-cr-cases.json").read_text(encoding="utf-8")
        )

    def test_profile_rules_match(self):
        self.assertEqual(
            (ROOT / RULE_PATH).read_bytes(),
            (ROOT / ".claude-company/knowledge/parallel-cr-review.md").read_bytes(),
        )

    def test_skill_mirrors_match(self):
        for path in (".claude-company/skills/parallel-cr/SKILL.md", ".agents/skills/parallel-cr/SKILL.md"):
            with self.subTest(path=path):
                self.assertEqual(self.skill, (ROOT / path).read_text(encoding="utf-8"))

    def test_explicit_activation_only(self):
        self.assertIn("Plain `cr:` remains a single", self.rule)
        self.assertIn("not new agent types", self.rule)
        self.assertIn("not a registered agent or executable orchestrator", self.skill)

    def test_actual_roles_and_frozen_inputs(self):
        for token in ("actual merge-base SHA", "immutable snapshot", "actual invocation/owner", "Freeze both initial reports"):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)

    def test_rule_intake_is_required(self):
        for token in ("VERIFIED_PRELOADED", "applicability and exceptions", "coding-guidelines §16", "review-prompt", "XREV-1/HND-1", "CLAUDE.md 5-A/5-I", "NEEDS_CONFIRMATION"):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)

    def test_separate_judgments(self):
        for token in ("`fact`", "`change_origin`", "`pr_scope`", "`rule_status`", "`severity`", "`disposition`"):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)
        self.assertIn("does not by itself", self.rule)
        self.assertIn("higher-priority project diff restriction", self.rule)

    def test_validation_includes_coverage(self):
        for token in ("findings AND missing coverage", "third whole-PR review", "single-owner finding", "no majority threshold"):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)

    def test_permissions_and_closure(self):
        for token in ("never grants Bash", "original owner confirms withdrawal", "No majority", "no automatic full rediscovery"):
            with self.subTest(token=token):
                self.assertIn(token.lower(), self.rule.lower())

    def test_binary_is_not_inferred(self):
        self.assertIn("Changed-line counts", self.rule)
        self.assertIn("no-Bash/no-script", self.rule)
        self.assertIn("workbook/sheet/case/cell", self.rule)

    def test_runtime_and_bias_limits(self):
        for token in ("NOT_MEASURED", "self_check", "does not prove", "Static contract tests do not establish"):
            with self.subTest(token=token):
                self.assertIn(token, self.rule)
        self.assertEqual(self.cases["agent_execution"], "NOT_RUN")

    def test_completion_prompt_is_pinned(self):
        for token in ("ae6b2dc526263f7f93fcae2a897ad2112b2577d5", "47df5af9f0544a78ede6e3b6e7355991293d5d0c", "F-03/F-04", "原文・適用条件・例外", "PARTIAL"):
            with self.subTest(token=token):
                self.assertIn(token, self.guide)

    def test_cases_cover_missing_validation_and_controls(self):
        expected = {
            "mandatory_rule_unread", "preload_identity_unverified", "unchanged_doc_new_mismatch",
            "same_cell_old_defect", "rule_condition_not_met", "xlsx_unread",
            "semantic_equality_not_counts", "severity_disagreement", "single_owner_finding",
            "validator_rejection_not_closure", "coverage_gap_no_findings", "ci_not_local_cr",
            "restricted_tool", "correct_negative_control", "same_family_not_cross_model",
            "repairs_not_fresh_discovery", "source_mismatch", "unrequested_expansion",
        }
        cases = self.cases["cases"]
        self.assertEqual(len(cases), len(expected))
        self.assertEqual({case["id"] for case in cases}, expected)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertGreater(len(case["input"]), 20)
                self.assertGreater(len(case["expected"]), 20)


if __name__ == "__main__":
    unittest.main()
