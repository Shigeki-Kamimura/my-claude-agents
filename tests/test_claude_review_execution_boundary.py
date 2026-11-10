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
            self.assertIn("No default layers or automatic progression.", workflow)
            self.assertIn("Invoke only user-selected actual qa/e2e agents", workflow)
            fields = workflow.split("response_contract:\n", 1)[1].split("pause_and_resume:\n", 1)[0]
            self.assertEqual({"workflow_id", "phase", "reviewer", "snapshot_id", "native_verdict", "coverage", "decision", "open_item_ids", "questions", "handoffs", "invocation_evidence"}, set(re.findall(r"(?m)^    ([a-z_]+):", fields)))
        for text in ("Omit Info from both the response and MD", "Ready for review", "gitignore", "all mandatory handoffs closed", "state.json"):
            self.assertIn(text, common)

    def test_pipeline_preserves_actual_owners_and_human_ready(self):
        common = read(".codex/workflows/md-review.md")
        for text in ("The implementer runs the project's actual Local-ci procedure", "actual Codex `ci-reviewer`", "**draft**", "AI never calls `gh pr ready` or an equivalent API", "every in-scope blob/mode", "Exit code 0 or the word Approve in MD alone"):
            self.assertIn(text, common)
        for path in ("AGENTS.md", ".codex/AGENTS.md", ".claude/CLAUDE.md", ".claude-company/CLAUDE.md"):
            self.assertIn("md-review.md", read(path))

    def test_profiles_keep_source_read_only_and_finite_lifecycle(self):
        common = read(".codex/workflows/md-review.md")
        for text in ("Bash/Edit/Write/NotebookEdit remain prohibited", "waiting for fixes, Local-ci or Codex", "NEW_UNRELATED Low", "NEEDS_USER_INPUT", "mandatory React/Nest consultations", "Implementation consultation cannot replace independent L2 consultation"):
            self.assertIn(text, common)
        for role in ("hq-coder", "code-quality-reviewer", "adviser", "test-qa", "e2e-qa"):
            a = read(".claude/agents/" + role + ".md")
            self.assertEqual(a, read(".claude-company/agents/" + role + ".md"))
            self.assertIn("## MD cross-model review", a)
            self.assertIn("eleven Workflow Result fields", a)
            self.assertIn("Omit Info entirely", a)
            self.assertIn("never keep Claude AI waiting", a)
        for text in ("Start a fresh exec every round.", "Never use exec resume or --last in this workflow."):
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

    def test_hnd1_handoff_weight_contract_is_consistent(self):
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            for text in ("**HND-1: Handoff weight and evidence-first reporting", "Evidence becomes a finding",
                         "never as Info", "prevents a clean result", "n=1, PR #1024"):
                self.assertIn(text, governance)
            for role in ("code-quality-reviewer", "adviser", "test-qa", "e2e-qa"):
                self.assertIn("HND-1", read(f"{profile}/agents/{role}.md"))
        for role in ("code-quality-reviewer", "adviser", "test-qa", "e2e-qa"):
            self.assertIn("HND-1", read(f".codex/agents/{role}.toml"))
        for path in (".codex/workflows/claude-review.yml", ".codex/workflows/codex-review.yml"):
            self.assertIn("HND-1", read(path))
        contract = read(".codex/workflows/md-review.md")
        for text in ("weight", "Any unresolved 🟡/🔴 handoff", "Legacy ledger"):
            self.assertIn(text, contract)
        self.assertIn('"weight"(🔴|🟡|🟢)', read("tools/start_md_review.py"))

    def test_claude_layers_must_read_xrev1_hnd1_and_project_rules(self):
        # XREV-1/HND-1は4層だけにengineering-review-lensesで注入される。注入に頼らず、定義側にも判定前の実読を明記します。
        clause = ("Before the first judgment, actually Read XREV-1 and HND-1 (HND-1 is a standing rule, "
                  "not a triggered lens) from `.claude/knowledge/engineering-governance.md`, and the applicable "
                  "project rule sections (e.g. the work copy's CLAUDE.md); do not rely only on this role "
                  "definition, and state in `Rules loaded` what was read.")
        for profile in (".claude", ".claude-company"):
            for role, layer in (("test-qa", "QA"), ("e2e-qa", "E2E"),
                                ("code-quality-reviewer", "CR"), ("adviser", "ADV")):
                text = read(f"{profile}/agents/{role}.md")
                self.assertEqual(1, text.count(clause), f"{profile}/{role}")
                self.assertIn(f"Apply the XREV-1 {layer} lenses only when triggered. {clause}", text)

    def test_e2e_must_fully_read_files_and_project_rules_before_gap_verdict(self):
        clause = ('Before declaring any E2E coverage gap, fully Read each affected E2E file (a grep-only search '
                  'yields "not found by grep", never a gap verdict), and list in `Rules loaded` the resolved '
                  'applicable project rule sources and complete sections verified by original reading or exact '
                  'preloaded delivery, with source identity and line ranges or section names; if any required '
                  'clause, including exceptions, is unavailable or unverified, dependent design-alignment '
                  'judgments are UNCONFIRMED and no clean or approve result may be returned.')
        for profile in (".claude", ".claude-company"):
            text = read(f"{profile}/agents/e2e-qa.md")
            self.assertEqual(1, text.count(clause), profile)
            self.assertIn("an open 🟡/🔴 handoff prevents a clean result." + " " + clause, text)
            self.assertNotIn("if that CLAUDE.md was not Read", text)

    def test_adviser_changed_source_read_status_gate_bars_approve(self):
        gate = ("Before the verdict, list every changed non-test source file with its Read status (full / partial / not read). "
                "When the project requires whole-file reading of changed files, any partial or unread changed source file "
                "makes coverage PARTIAL (not COMPLETE) and bars `APPROVE`: use the existing DEFER (or REQUEST_CHANGES when a "
                "confirmed violation exists) with the exact unread files named, unless the unread part is demonstrably "
                "unrelated to the change and the reason is recorded. Changed test files are read by the test layers; skip "
                "their full reading only when QA/E2E own them, and say so.")
        for profile in (".claude", ".claude-company"):
            text = read(f"{profile}/agents/adviser.md")
            self.assertEqual(1, text.count(gate), profile)
            self.assertIn("never turn missing requirements into an assumed acceptance criterion. " + gate, text)
            header = text.split("---", 2)[1]
            self.assertIn("model: claude-opus-5-5", header)
            self.assertIn("effort: high", header)

    def test_xrev1_central_behavior_gap_floor_is_pinned(self):
        floor = ("If no test can distinguish the new behavior from the old, the gap is at least 🟡. "
                 "This is an evidence-based floor, not a rule to raise severity without evidence; gaps in "
                 "peripheral controls, message text or secondary negative cases may be 🟢 Low.")
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            for layer in ("QA", "E2E"):
                row = next(line for line in governance.splitlines()
                           if line.startswith(f"| {layer} | A coverage gap on a behavior the PR itself states"))
                self.assertIn(floor, row)
        # Codex側は再生成されたプリロード経由で受け取り、Claude側の事前読込には含まれません。
        self.assertEqual(2, read(".agents/skills/engineering-review-core/SKILL.md").count(floor))
        self.assertNotIn(floor, read(".claude/skills/engineering-review-core/SKILL.md"))

    def test_approval_label_boundary_open_low_never_approves(self):
        # 未解決のLow(DEFER指定を含む)は承認系ラベルを許さず、Infoだけなら清浄な承認です。
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            self.assertIn("Approval-label boundary", governance)
            self.assertIn("allows no approval-class label", governance)
            self.assertIn("Origin: FIX_INDUCED", governance)
            cr = read(f"{profile}/agents/code-quality-reviewer.md")
            self.assertIn("any 🟢 Low finding is open (including one labeled DEFER)", cr)
            self.assertNotIn("non-blocking notes", cr)
            self.assertIn("any open owned 🟢 Low finding", read(f"{profile}/agents/adviser.md"))
        cr_toml = read(".codex/agents/code-quality-reviewer.toml")
        self.assertIn("any 🟢 Low finding is open (including one labeled DEFER)", cr_toml)
        self.assertNotIn("non-blocking notes", cr_toml)
        self.assertIn("any open owned 🟢 Low finding", read(".codex/agents/adviser.toml"))
        self.assertIn("including DEFER", read(".codex/workflows/md-review.md"))
        cases = read("tests/agent-review-contract-cases.yml")
        for case in ("approval-info-only-clean-label", "approval-open-low-defer-no-approve-label"):
            self.assertEqual(cases.count("  - id: " + case + "\n"), 1)

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

    def test_every_claude_review_role_states_the_reviewer_no_execution_rule(self):
        review_roles = ("test-qa", "e2e-qa", "code-quality-reviewer", "adviser", "reviewer",
                        "sec-arch", "data-platform", "react-ui-flow", "nestjs-backend",
                        "vue-frontend", "spring-boot")
        for profile in (".claude", ".claude-company"):
            governance = read(f"{profile}/knowledge/engineering-governance.md")
            permissions = governance.split("### User-directed execution permissions\n", 1)[1].split("\n### ", 1)[0]
            for required in ("Reviewer no-execution rule", "never runs unit/integration/E2E/Playwright/Cypress tests",
                             "directly or through another agent", "Supplied evidence", "NOT_RUN",
                             "not to a role acting as a reviewer"):
                with self.subTest(profile=profile, required=required):
                    self.assertIn(required, permissions)
            core = read(f"{profile}/skills/engineering-review-core/SKILL.md")
            self.assertIn("Reviewer no-execution rule", core)
            for role in review_roles:
                with self.subTest(profile=profile, role=role):
                    text = read(f"{profile}/agents/{role}.md")
                    self.assertIn("Reviewer no-execution rule (governance `User-directed execution permissions`)", text)
                    self.assertRegex(text, r"(?s)Reviewer no-execution rule.*(?:typecheck|lint)")
                    self.assertRegex(text, r"directly or through (?:another agent|a consultant)")
                    self.assertIn("NOT_RUN", text)
            hq = read(f"{profile}/agents/hq-coder.md")
            self.assertNotIn("Reviewer no-execution rule", hq)
            self.assertIn("Bash", hq.split("---", 2)[1])
        e2e = read(".claude/agents/e2e-qa.md")
        self.assertIn("write the spec but do not run it", e2e)
        self.assertNotIn("running targeted E2E commands\n", e2e)
        self.assertNotIn("explicit user request to verify or add Playwright", e2e)

    def test_reviewer_no_execution_rule_is_text_only_not_a_frontmatter_block(self):
        # git読取を残す必要があり、frontmatterでのBashパターン制限は未検証のため、技術的強制はしていないことを固定する
        for profile in (".claude", ".claude-company"):
            for role in ("test-qa", "e2e-qa", "code-quality-reviewer", "adviser", "reviewer"):
                with self.subTest(profile=profile, role=role):
                    front = read(f"{profile}/agents/{role}.md").split("---", 2)[1]
                    self.assertNotIn("disallowedTools", front)

if __name__ == "__main__":
    unittest.main()
