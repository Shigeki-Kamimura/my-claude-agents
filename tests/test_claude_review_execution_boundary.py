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
        match = re.search(r"(?m)^  argv:\n((?:  - [^\n]*\n)+)", section)
        self.assertIsNotNone(match, "CLI引数が見つかりません")
        args = [line[4:] for line in match.group(1).splitlines()]
        mode = args.index("--permission-mode")
        self.assertEqual(args[mode + 1], "dontAsk")
        tools = args.index("--tools")
        self.assertEqual(set(args[tools + 1].split(",")), {"Read", "Glob", "Grep", "Agent", "SendMessage"})
        allowed = args[args.index("--allowedTools") + 1:args.index("--disallowedTools")]
        self.assertEqual(set(allowed), {"Read", "Glob", "Grep", "Agent", "SendMessage"})
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
        self.assertIn("新しいレビュー専用CLI制限を適用する前に起動した親/子", workflow)
        self.assertIn("旧承認を新承認として流用しません", workflow)

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

    def test_both_resume_templates_deliver_fix_and_verification_together(self):
        workflow = read(".codex/workflows/claude-review.yml")
        for name, end in (("single_layer", "authority"), ("claude_cli", "review_entry")):
            with self.subTest(template=name):
                block = workflow.split("\n" + name + ":\n", 1)[1].split("\n" + end + ":\n", 1)[0]
                initial = block.split("  prompt_template: |\n", 1)[1].split("  resume_prompt_template: |\n", 1)[0]
                resume = block.split("  resume_prompt_template: |\n", 1)[1]
                self.assertNotIn("{fix_and_verification_evidence}", initial)
                self.assertIn("{fix_and_verification_evidence}", resume)
                self.assertIn("{new_answers_or_constraints}", resume)
                self.assertIn("{rereview_exception}", resume)
                if name == "single_layer":
                    self.assertIn("Mode: single-layer {phase}", resume)

    def test_batched_delivery_keeps_verifier_scope_and_incomplete_states(self):
        workflow = read(".codex/workflows/claude-review.yml")
        cycle = workflow.split("\nreview_cycle:\n", 1)[1].split("\nconsultation:\n", 1)[0]
        values = dict(re.findall(r"(?m)^  ([a-z_]+): (.+)$", cycle))
        for field in ("fix", "rereview_inputs", "verification_evidence", "rereview_exceptions"):
            self.assertIn(field, values)
        for scope in ("staged", "unstaged", "untracked", "source", "終了コード"):
            self.assertIn(scope, values["rereview_inputs"])
        for obligation in ("assertion", "Read", "読み込んだ対象", "Codexの提示証拠"):
            self.assertIn(obligation, values["verification_evidence"])
        self.assertIn("失敗を含む", values["fix"])
        self.assertIn("全テスト成功を一律の再依頼条件にはしません", values["fix"])
        for state in ("NOT_RUN", "FAILED", "PARTIAL"):
            self.assertIn(state, values["rereview_exceptions"])
        self.assertIn("追加質問", values["rereview_exceptions"])
        self.assertIn("単層", values["rereview_exceptions"])

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

    def test_advisor_disabled_on_launch_and_resume_with_runtime_check(self):
        workflow = read(".codex/workflows/claude-review.yml")
        cli = workflow.split("\nclaude_cli:\n", 1)[1].split("\nreview_entry:\n", 1)[0]
        self.assertIn("CLAUDE_CODE_DISABLE_ADVISOR_TOOL: '1'", cli)
        self.assertIn('"env":{"CLAUDE_CODE_DISABLE_ADVISOR_TOOL":"1"}', cli)
        for expected in ("--check-review-boundary", "server_tool_use", "BLOCKED", "UNCONFIRMED", "--resume"):
            self.assertIn(expected, cli)
        for profile in (".claude", ".claude-company"):
            agent = read(f"{profile}/agents/code-quality-reviewer.md")
            self.assertIn("First-pass rule intake and bounded reading", agent)
            core = read(f"{profile}/skills/engineering-review-core/SKILL.md")
            self.assertIn("- Intake:", core)
            self.assertIn("User/project whole-file requirements", core)

    def test_intake_and_bounded_reading_keep_all_mandatory_obligations(self):
        workflow = read(".codex/workflows/claude-review.yml")
        entry = workflow.split("\nreview_entry:\n", 1)[1].split("\nexecution:\n", 1)[0]
        for required in ("required_intake:", "Rules loaded", "例外込み", "Readで直接", "UNCONFIRMED",
                         "reading_scope:", "変更hunk", "利用者やproject規則", "未確認の義務"):
            self.assertIn(required, entry)
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            intake = governance.split("### First-pass rule intake and bounded reading\n", 1)[1].split("\n### ", 1)[0]
            for required in ("not a substitute", "exceptions", "whole-file requirements still apply", "Same-owner"):
                self.assertIn(required, intake)

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

    def test_single_layer_separates_local_dependencies_from_other_handoffs(self):
        workflow = read(".codex/workflows/claude-review.yml")
        block = workflow.split("\nsingle_layer:\n", 1)[1].split("\nauthority:\n", 1)[0]
        for required in ("handoff_policy:", "result_consistency:", "自層判断に依存しない", "自層の未了義務",
                         "decisionをAPPROVE", "Codex自身が判定を書き換えません", "全必須handoffの解消"):
            self.assertIn(required, block)
        for profile in (".claude", ".claude-company"):
            cr = read(f"{profile}/agents/code-quality-reviewer.md")
            self.assertIn("report `decision: APPROVE`", cr)
            self.assertIn("your own judgment depends on remains a local obligation", cr)
            self.assertIn("never rewrites the verdict itself", cr)
            core = read(f"{profile}/skills/engineering-review-core/SKILL.md")
            self.assertIn("independent other-layer handoffs remain open", core)
            self.assertIn("stays local", core)
        cases = read("tests/agent-review-contract-cases.yml")
        for case in ("single-layer-handoff-only-approve", "single-layer-dependent-evidence-pending",
                     "single-layer-local-low-pending", "single-layer-result-correction-by-owner"):
            self.assertEqual(1, cases.count("  - id: " + case + "\n"))

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

    def test_reverse_workflow_still_has_its_own_owner(self):
        reverse = read(".codex/workflows/codex-review.yml")
        self.assertIn("claude-codex-review", reverse)
        self.assertIn("Claude Codeが修正と必要な検証を行い", reverse)


    def test_entrypoints_keep_review_gates_and_bounded_waits(self):
        root = read("AGENTS.md")
        self.assertIn(".codex/AGENTS.md", root)
        self.assertIn(".claude/CLAUDE.md", root)
        self.assertIn("engineering-governance.md", root)
        self.assertNotIn("## Opus Escalation", root)

        codex = read(".codex/AGENTS.md")
        for required in ("## Bounded subagent waiting", "wait_agent",
                         "list_agents", "180000", "300000", "## Model Allocation"):
            self.assertIn(required, codex)

        for profile in (".claude", ".claude-company"):
            parent = read(f"{profile}/CLAUDE.md")
            for required in ("codex-claude-review", "claude-codex-review",
                             "Codex exclusively runs typecheck",
                             "qa -> e2e -> cr -> adv", "--resume"):
                self.assertIn(required, parent)

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
