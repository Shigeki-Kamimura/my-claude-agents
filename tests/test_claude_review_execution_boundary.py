#!/usr/bin/env python3
"""MD方式へ移行したレビュー契約と、継続する独立確認義務を検証します。"""
import re
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")

class ClaudeReviewExecutionBoundaryTests(unittest.TestCase):
    def test_directions_share_md_contract_and_user_selected_layers(self):
        common = read(".codex/workflows/md-review.md")
        for path, direction in (("claude-review.yml", "codex-claude-review"), ("codex-review.yml", "claude-codex-review")):
            workflow = read(".codex/workflows/" + path)
            self.assertIn("workflow_id: " + direction, workflow)
            self.assertIn("common_contract: md-review.md", workflow)
            self.assertIn("既定層も自動昇格もありません", workflow)
            self.assertIn("利用者が選択した実agentだけ", workflow)
            fields = workflow.split("response_contract:\n", 1)[1].split("pause_and_resume:\n", 1)[0]
            self.assertEqual({"workflow_id", "phase", "reviewer", "snapshot_id", "native_verdict", "coverage", "decision", "open_item_ids", "questions", "handoffs", "invocation_evidence"}, set(re.findall(r"(?m)^    ([a-z_]+):", fields)))
        for text in ("Infoは本文にもMDにも記載しません", "Ready for review", "gitignore", "全必須handoff", "REQUIRES_OWNER_RESULT_CHECK"):
            self.assertIn(text, common)

    def test_pipeline_preserves_actual_owners_and_human_ready(self):
        common = read(".codex/workflows/md-review.md")
        for text in ("実装担当がprojectの実Local-ci手順を実行", "実際のCodex `ci-reviewer`", "**draft**", "AIは`gh pr ready`や同等APIを呼びません", "全対象blob/mode", "終了コード0やMD本文のApproveという文字だけ"):
            self.assertIn(text, common)
        for path in ("AGENTS.md", ".codex/AGENTS.md", ".claude/CLAUDE.md", ".claude-company/CLAUDE.md"):
            self.assertIn("md-review.md", read(path))

    def test_profiles_keep_source_read_only_and_finite_lifecycle(self):
        common = read(".codex/workflows/md-review.md")
        for text in ("Bash/Edit/Write/NotebookEditは禁止", "修正待ち、Local-ci待ち、Codex待ち", "NEW_UNRELATEDのLow", "NEEDS_USER_INPUT", "必須React/Nest相談", "実装時の相談は独立したL2相談の代わり"):
            self.assertIn(text, common)
        for role in ("hq-coder", "code-quality-reviewer", "adviser", "test-qa", "e2e-qa"):
            a = read(".claude/agents/" + role + ".md")
            self.assertEqual(a, read(".claude-company/agents/" + role + ".md"))
            self.assertIn("## MD cross-model review", a)
            self.assertIn("eleven Workflow Result fields", a)
            self.assertIn("Omit Info entirely", a)
            self.assertIn("never keep Claude AI waiting", a)
        for text in ("毎roundで新しいexec", "exec resumeや--lastを使いません"):
            self.assertIn(text, read(".codex/workflows/codex-review.yml"))

    def test_governance_has_no_conflicting_git_or_hash_execution_instruction(self):
        for profile in (".claude", ".claude-company"):
            with self.subTest(profile=profile):
                governance = read(f"{profile}/knowledge/engineering-governance.md")
                self.assertNotIn("gets its own Git diff/status", governance)
                self.assertNotIn("the receiver runs the same command", governance)
                self.assertNotIn("this is not a Read/Grep/Glob-only", governance)
                self.assertIn("Restricted Claude reviewers never run a hash/Git command", governance)
                self.assertIn("Matching identity permits reuse only for complete sections", governance)
                self.assertIn("independent first owners for new phases", governance)
                self.assertIn("reverse `claude-codex-review` fresh-round contract", governance)

    def test_batched_delivery_is_scoped_and_reaches_both_preloads(self):
        for profile in (".claude", ".claude-company"):
            with self.subTest(profile=profile):
                governance = read(f"{profile}/knowledge/engineering-governance.md")
                batch = governance.split("### Batched re-review evidence\n", 1)[1].split("\n### ", 1)[0]
                self.assertIn("For `codex-claude-review` only", batch)
                self.assertIn("not that every test passed", batch)
                self.assertIn("necessary assertions and import/load target", batch)
                self.assertIn("NOT_RUN / FAILED / PARTIAL", batch)
                core = read(f"{profile}/skills/engineering-review-core/SKILL.md")
                self.assertIn("Re-review delivery (codex-claude-review only)", core)
                self.assertIn("they are not success or closure", core)
        cases = read("tests/agent-review-contract-cases.yml")
        for case in ("batched-rereview-default", "batched-verifier-readable",
                     "batched-rereview-failed-verification", "batched-rereview-early-question",
                     "batched-rereview-waived-or-interrupted"):
            self.assertEqual(cases.count("  - id: " + case + "\n"), 1)

    def test_qa_e2e_intake_and_reachability_keep_review_only_scope(self):
        for role in ("test-qa", "e2e-qa"):
            canonical = read(f".claude/agents/{role}.md")
            self.assertEqual(canonical, read(f".claude-company/agents/{role}.md"))
            block = canonical.split("## First-pass intake and finding evidence\n", 1)[1].split("## Engineering principles\n", 1)[0]
            for obligation in ("before test-adequacy judgment", "Rules loaded", "including exceptions",
                               "required non-injected originals", "UNCONFIRMED", "same-owner continuation",
                               "Reachable Failure Evidence", "branch precedence", "observable regression",
                               "equivalent existing assertions", "fault-injection tests remain valid",
                               "never claim a mutation", "no execution tools or additional review layers"):
                self.assertIn(obligation, block)
            if role == "e2e-qa":
                self.assertIn("Do not infer visible copy from an API title", block)
            else:
                self.assertIn("hand off browser and HTTP/module-boundary obligations", block)

    def test_cr_handoff_count_and_existing_four_fields_are_consistent(self):
        codex = read(".codex/AGENTS.md")
        self.assertNotIn("at most 2 L2+ handoff cues", codex)
        self.assertIn("handoffs without a count limit", codex)
        for path in (".claude/agents/code-quality-reviewer.md", ".claude-company/agents/code-quality-reviewer.md",
                     ".codex/agents/code-quality-reviewer.toml"):
            cr = read(path)
            self.assertIn("without a count limit", cr)
            self.assertIn("Owner/route | Question | Evidence | Required confirmation", cr)
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            self.assertIn("CR handoffs have no count limit", governance)
            self.assertIn("scope changes need new evidence", governance)
        self.assertEqual(1, read("tests/agent-review-contract-cases.yml").count("  - id: cr-handoff-count-and-scope\n"))

    def test_injected_self_definition_reuse_keeps_missing_rules_pending(self):
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            intake = governance.split("### Claude role-scoped intake\n", 1)[1].split("\n### ", 1)[0]
            for required in ("own system prompt", "current original path/version", "invocation/source evidence",
                             "parent's summary", "is insufficient", "including exceptions",
                             "keep dependent approval pending", "combined results", "on truncation",
                             "missing/uncertain ranges", "Explicit project whole-file requirements still apply",
                             "does not transfer QA/E2E adequacy ownership to L2"):
                self.assertIn(required, intake)
            core = read(f"{profile}/skills/engineering-review-core/SKILL.md")
            self.assertIn("### Claude role-scoped intake\n", core)
            self.assertTrue(intake.strip() in core, "原文の節本文が生成物に保持されていません")
            self.assertNotIn("## Mandatory framework consultation\n", core)

    def test_ci_playwright_wait_ownership_needs_no_waiting_agent(self):
        codex = read(".codex/AGENTS.md")
        wait = codex.split("## Bounded subagent waiting\n", 1)[1].split(
            "\n## Mandatory Agent Routing", 1)[0]
        for required in ("CI", "Playwright", "exit status",
                         "Do not spawn a separate child", "QA/E2E"):
            self.assertIn(required, wait)

        for profile in (".claude", ".claude-company"):
            with self.subTest(profile=profile):
                parent = read(f"{profile}/CLAUDE.md")
                cost = parent.split("## Cost Awareness\n", 1)[1].split(
                    "\n## Model Allocation", 1)[0]
                for required in ("CI", "Playwright", "exit status",
                                 "Never launch a separate subagent", "QA/E2E"):
                    self.assertIn(required, cost)

if __name__ == "__main__":
    unittest.main()
