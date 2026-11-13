"""PCR-1の静的な配布・記載契約だけを確認します。"""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = Path(".claude/knowledge/parallel-cr-review.md")
SKILL_PATH = Path(".claude/skills/parallel-cr/SKILL.md")


ADDITIONAL_CASE_IDS = {
    "semantic_doc_search",
    "zero_hits_not_complete",
    "artifact_selected_cells",
    "artifact_schema_expansion",
    "whole_file_rule_preserved",
    "raw_extract_not_verdict",
    "duplicate_group_traceable",
    "candidate_complete_scope_partial",
    "guard_disproves_reachability",
    "manual_test_omission",
    "manual_test_explicit_rule",
    "api_vs_business_decision",
    "independent_green_handoff",
    "dependent_question_stays_local",
    "events_not_agent_listing",
    "wall_time_not_work_sum",
    "metrics_missing_not_gate",
    "authorized_owner_response",
    "unauthorized_owner_response",
    "reconcile_workflow_conflict",
}


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

    def test_full_diff_exception_is_limited_to_codex_pcr(self):
        for clause in (
            "Use existing role budgets for non-Codex PCR and ordinary standalone roles",
            "Codex PCR has no fixed file-count limit",
            "CR-A and CR-B each independently cover the complete assigned change inventory",
            "and any planner numeric cap only for Codex PCR",
            "Standalone PCR does not activate that sequence",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, self.rule)

    def test_codex_roles_preserve_the_limited_full_diff_exception(self):
        roles = {
            "code-quality-reviewer": (
                "For an explicitly assigned Codex PCR-1 CR-A/CR-B task, there is no fixed file-count limit",
                "Each discovery owner independently checks every changed hunk",
                "This exception changes neither standalone CR nor Claude CR/ADV/QA/E2E policy",
            ),
            "review-planner": (
                "For an explicitly selected Codex PCR flow, pass the full change inventory without a numeric file cap",
                "Its CR-A and CR-B each need complete cumulative coverage",
                "ordinary CR/ADV/QA/E2E limits below are unchanged",
            ),
        }
        for role, clauses in roles.items():
            instructions = (ROOT / f".codex/agents/{role}.toml").read_text(encoding="utf-8")
            for clause in clauses:
                with self.subTest(role=role, clause=clause):
                    self.assertIn(clause, " ".join(instructions.split()))

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
        expected |= ADDITIONAL_CASE_IDS
        self.assertEqual(len(cases), len(expected))
        self.assertEqual({case["id"] for case in cases}, expected)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertGreater(len(case["input"]), 20)
                self.assertGreater(len(case["expected"]), 20)


    def test_document_impact_requires_semantic_search(self):
        section = self.rule.split("### DOC-IMPACT:", 1)[1].split("### ARTIFACT-DELTA:", 1)[0]
        for text in ("old -> new behavior", "operation/screen/route", "operational/demo",
                     "semantic identifiers", "query/hits/disposition", "one bounded alternative",
                     "inaccessible or truncated", "not proof"):
            with self.subTest(text=text):
                self.assertIn(text, section)
        self.assertNotIn("STG_CASE_MANAGEMENT_DEMO", section)
        self.assertNotIn("TC12", section)

    def test_artifact_selection_precedes_reading(self):
        section = self.rule.split("### ARTIFACT-DELTA:", 1)[1].split("### RULE-SCOPE", 1)[0]
        for text in ("before reading data", "Case IDs, not row numbers alone",
                     "Do not compare every case/column", "Return only selected values",
                     "not a semantic audit of all rows", "Do not repeat the same full extraction",
                     "changed common template/schema", "Explicit whole-file requirements still apply"):
            with self.subTest(text=text):
                self.assertIn(text, section)

    def test_raw_reuse_preserves_independent_judgment(self):
        for text in ("raw source extracts may be shared", "never peer conclusions",
                     "Each owner still reads its own required originals",
                     "each owner evaluates its own assigned evidence",
                     "validator checks contested cells"):
            self.assertIn(text, self.rule)

    def test_scope_and_guard_before_new_blocker(self):
        for text in ("nearest guard", "does not establish a reachable failure",
                     "Do not erase previously tracked findings", "before deeper severity analysis",
                     "stop unrelated investigation"):
            self.assertIn(text, self.rule)

    def test_manual_adequacy_stays_with_qa(self):
        for text in ("QA/E2E test-adequacy ownership", "exact manual acceptance check",
                     "counterevidence, not universal proof", "omission alone"):
            self.assertIn(text, self.rule)

    def test_business_authority_and_handoff_gates(self):
        for text in ("API execution permission does not by itself",
                     "authorization-matrix audits", "essential to the local verdict",
                     "independently owned", "Never downgrade weight"):
            self.assertIn(text, self.rule)

    def test_dedup_preserves_all_ids_and_occurrences(self):
        for text in ("retaining every original owner/ID", "each distinct occurrence",
                     "every source ID", "reused ID"):
            self.assertIn(text, self.rule)

    def test_validator_checks_document_gap_not_only_candidates(self):
        for text in ("including DOC-IMPACT search evidence", "both owners omitted",
                     "even when no candidate mentions the document",
                     "does not make the whole PR COMPLETE"):
            self.assertIn(text, self.rule)

    def test_no_listing_or_polling_for_concurrency(self):
        self.assertIn("Do not call `list_agents`", self.rule)
        self.assertIn("dispatch/completion events", self.rule)
        self.assertIn("permitted long waits", self.rule)
        self.assertIn("not `list_agents` or short polling", self.skill)
        self.assertIn("list_agentsや短い間隔の確認は使わず", self.guide)

    def test_timing_usage_do_not_add_gate(self):
        for text in ("timestamps with timezone", "duration in seconds",
                     "not the sum of concurrent owner intervals",
                     "every child exactly once", "one fixed cutoff",
                     "never gate approval", "user-reported duration stays SUPPLIED"):
            self.assertIn(text, self.rule)

    def test_one_owner_response_requires_prior_permission(self):
        for text in ("reconcile_once: true", "Only under that authorization",
                     "once to each affected original owner", "no fresh discovery",
                     "does not authorize another round", "conflicting fresh-round contract"):
            self.assertIn(text, self.rule)
        self.assertIn("user explicitly sets `reconcile_once: true`", self.skill)
        self.assertIn("追加しなければ3担当で終了", self.guide)

    def test_skill_dispatch_passes_missing_coverage_contract(self):
        for text in ("DOC-IMPACT", "ARTIFACT-DELTA", "manual-test adequacy",
                     "group candidates", "mandatory-coverage gaps", "NOT_MEASURED",
                     "do not forward calibration examples or behavioral fixtures"):
            self.assertIn(text, self.skill)

    def test_guide_reports_trial_as_supplied_not_new_measurement(self):
        for text in ("約21分", "SUPPLIED", "内訳は未計測", "未発見か記載漏れか",
                     "新しい実機試行まで未測定", "sync_codex_desktop.py"):
            self.assertIn(text, self.guide)

    def test_skill_frontmatter_and_section_links(self):
        self.assertTrue(self.skill.startswith("---\nname: parallel-cr\n"))
        self.assertEqual(self.skill.split("---\n", 2)[1].count("name:"), 1)
        for number in range(1, 9):
            self.assertEqual(self.rule.count(f"## {number}. "), 1)
        self.assertNotIn("reconcile_once: true", self.rule.split("## 1.", 1)[0])


if __name__ == "__main__":
    unittest.main()
