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

    def test_initial_continuation_and_fix_requests_keep_distinct_evidence(self):
        workflow = read(".codex/workflows/claude-review.yml")
        for name, end in (("single_layer", "authority"), ("claude_cli", "review_entry")):
            with self.subTest(template=name):
                block = workflow.split("\n" + name + ":\n", 1)[1].split("\n" + end + ":\n", 1)[0]
                templates = {}
                for key in ("prompt_template", "resume_prompt_template", "continuation_prompt_template"):
                    match = re.search(r"(?m)^  " + key + r": \|\n((?:    [^\n]*\n)+)", block)
                    self.assertIsNotNone(match, key)
                    templates[key] = match[1]
                self.assertIn("{review_source_evidence}", templates["prompt_template"])
                self.assertIn("{fix_and_verification_evidence}", templates["resume_prompt_template"])
                continuation = templates["continuation_prompt_template"]
                for field in ("continuation_reason", "retained_record_reference", "new_evidence"):
                    self.assertIn("{" + field + "}", continuation)
                self.assertNotIn("{fix_and_verification_evidence}", continuation)
                self.assertIn("SendMessage", continuation)
                self.assertIn("再開不能", continuation)
                for key in ("resume_prompt_template", "continuation_prompt_template"):
                    for field in ("parent_session_id", "owner_agent_id"):
                        self.assertIn("{" + field + "}", templates[key])
                if name == "single_layer":
                    self.assertIn("Mode: single-layer {phase}", continuation)

    def test_diff_delivery_and_resume_failure_do_not_expand_permissions(self):
        workflow = read(".codex/workflows/claude-review.yml")
        delivery = re.search(r"(?m)^  source_delivery: (.+)$", workflow)[1]
        for required in ("実base", "HEAD", "working source", "除外", "staged", "unstaged",
                         "untracked", "rename/削除", "元版", "Supplied", "未確認", "巨大manifest"):
            self.assertIn(required, delivery)
        self.assertIn("親の--resumeだけでは子の再開証拠になりません", workflow)
        self.assertIn("新規Agentへの自動置換や再試行ループを行いません", workflow)
        self.assertIn("phaseをまたぐ再開はしません", workflow)
        self.assertIn("安全上の新規起動例外は維持します", workflow)

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

    def test_claude_role_sections_preserve_independent_original_reading(self):
        workflow = read(".codex/workflows/claude-review.yml")
        entry = workflow.split("\nreview_entry:\n", 1)[1].split("\nexecution:\n", 1)[0]
        delivery = entry.split("  contract_delivery: ", 1)[1].split("\n  role_sections:", 1)[0]
        for required in ("原本のpath/版", "自分で確認", "例外", "Rules loaded",
                         "親の要約だけでは既読にしません", "切詰め", "承認を保留"):
            self.assertIn(required, delivery)
        roles = entry.split("  role_sections:\n", 1)[1].split("  required_intake:", 1)[0]
        common = roles.split("    phase_common: ", 1)[1].splitlines()[0]
        for required in ("authority", "ownership", "review_entry", "review_cycle", "review_gates",
                         "findings", "questions", "response_contract", "handoff", "staged_baseline",
                         "single_layer", "例外"):
            self.assertIn(required, common)
        for phase, extra in (("l1_5", "execution.cr_adv"), ("qa", "qa_contract"),
                             ("e2e", "qa_contract"), ("l2", "consultation")):
            line = roles.split(f"    {phase}: ", 1)[1].splitlines()[0]
            self.assertIn("phase_common", line)
            self.assertIn(extra, line)
        self.assertIn("11項目の代理作成はしません", roles)
        for profile in (".claude", ".claude-company"):
            for role in ("adviser", "code-quality-reviewer", "test-qa", "e2e-qa"):
                owner = read(f"{profile}/agents/{role}.md")
                self.assertIn("review_entry.role_sections", owner)
                self.assertIn("including direct invocation, apply `Claude role-scoped intake`", owner)
                self.assertNotIn("including direct invocation, read `.claude/knowledge/engineering-governance.md`", owner)
            for role in ("react-ui-flow", "nestjs-backend"):
                owner = read(f"{profile}/agents/{role}.md")
                self.assertIn("Read only missing applicable governance sections", owner)
                self.assertIn("Stay read-only", owner)

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

    def test_foreground_consultation_requires_real_results_without_widening_tools(self):
        workflow = read(".codex/workflows/claude-review.yml")
        consultation = workflow.split("\nconsultation:\n", 1)[1].split("\nqa_contract:\n", 1)[0]
        for required in ("最小限の実境界", "依頼を遅らせません", "run_in_background", "false",
                         "model/effortや許可toolは変更しません", "SPECIALIST_REQUEST",
                         "同じadviser", "起動確認や回答待ちは未完了", "tool追加",
                         "取得不能", "承認しません", "実回答の受領後", "11項目"):
            self.assertIn(required, consultation)
        for profile in (".claude", ".claude-company"):
            adviser = read(f"{profile}/agents/adviser.md")
            for required in ("Immediately batch", "Do not finish the full framework investigation",
                             "exposed Agent schema", "`false`", "actual replies", "same owner",
                             "precise missing capability", "adoption/rejection reasons"):
                self.assertIn(required, adviser)
            parent = read(f"{profile}/CLAUDE.md")
            for required in ("foreground Agent", "only when exposed", "actual replies",
                             "do not add tools or waiting agents", "eleven `Workflow Result` fields",
                             "For active `codex-claude-review` only", "does not activate a workflow"):
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
