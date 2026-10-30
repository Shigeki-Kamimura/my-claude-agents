"""親HQの責務、独立レビュー、固定プロンプトの順序を確認します。"""

from pathlib import Path
import re
from string import Formatter
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    marker = heading + "\n"
    if text.count(marker) != 1:
        raise ValueError(f"見出しが一意ではありません: {heading}")
    body = text.split(marker, 1)[1]
    level = len(heading.split(" ", 1)[0])
    end = re.search(r"(?m)^#{1," + str(level) + r"} ", body)
    return body[:end.start()] if end else body


def review_prompt(text: str) -> str:
    body = text.split("  prompt_template: |\n", 1)[1].split("  result_handling:\n", 1)[0]
    lines = body.splitlines()
    if not all(line.startswith("    ") for line in lines):
        raise ValueError("プロンプトの字下げが不正です")
    return "\n".join(line[4:] for line in lines) + "\n"


class ParentHqContractTests(unittest.TestCase):
    def setUp(self):
        self.codex = read(".codex/AGENTS.md")
        self.root = read("AGENTS.md")
        self.hq = tomllib.loads(read(".codex/agents/hq-coder.toml"))
        self.ownership = section(self.codex, "### Parent implementation ownership")
        self.workflow = read(".codex/workflows/codex-review.yml")

    def test_cohesive_implementation_and_aliases_use_parent(self):
        self.assertIn("main session owns the HQ role by default", self.ownership)
        for alias in ("`h:`", "`hq:`", "`hq-coder`"):
            self.assertIn(alias, self.ownership)
        self.assertIn("Keep cohesive implementation and scoped verification in the parent", self.ownership)
        self.assertIn("`codex-claude-review`", self.ownership)
        for text in (self.root, self.codex):
            self.assertNotIn("All task execution must be delegated", text)
            self.assertNotIn("coordinator, not the worker", text)
        self.assertIn("HQ role in the parent by default", self.root)

    def test_read_only_receiver_cannot_become_implementer(self):
        guard = next(line for line in self.ownership.splitlines()
                     if line.startswith("- In `claude-codex-review`"))
        for required in ("read-only review receiver", "delegate the real requested reviewer",
                         "parent HQ execution is unavailable", "BLOCKED", "Never widen tool permissions"):
            self.assertIn(required, guard)
        self.assertIn("Read-only reviewer ownership takes precedence", self.codex)
        self.assertIn("receiver remains read-only", self.root)
        self.assertIn("these implementation instructions grant no execution permission",
                      self.hq["developer_instructions"])

    def test_contract_loading_and_missing_contract_are_explicit(self):
        for required in (".codex/agents/hq-coder.toml", "beside the resolved `.codex/AGENTS.md`",
                         "before editing", "design, test, staged-baseline, evidence and consultation",
                         "missing contract is BLOCKED"):
            self.assertIn(required.lower(), self.ownership.lower())
        self.assertIn("source/section -> responsibility or invariant -> inspected evidence -> result",
                      self.hq["developer_instructions"])

    def test_specialist_calls_do_not_require_relay_hq(self):
        for required in ("parent invokes required React/Nest", "directly", "real invocation evidence",
                         "not a second coordinator", "`SPECIALIST_REQUEST`", "No parent -> HQ relay"):
            self.assertIn(required, self.ownership)
        contract = section(self.hq["developer_instructions"], "## Framework Consultation Contract")
        self.assertIn("Matching routine changes require consultation", contract)
        self.assertIn("An isolated HQ worker always returns `SPECIALIST_REQUEST`", contract)
        self.assertNotIn("Otherwise return `SPECIALIST_REQUEST`", contract)
        self.assertIn("NOT_APPLICABLE", contract)
        self.assertIn("PENDING / UNAVAILABLE", contract)

    def test_explicit_worker_and_isolated_slices_remain_available(self):
        for required in ("explicit request for a separate HQ child", "explicit file/ownership boundaries",
                         "Do not duplicate", "concurrent edits to the same files"):
            self.assertIn(required, self.ownership)
        self.assertEqual(self.hq["name"], "hq-coder")
        self.assertEqual(self.hq["model"], "gpt-6.1-sol")
        self.assertEqual(self.hq["model_reasoning_effort"], "high")
        self.assertIn("context-isolated HQ worker handles only its assigned slice", self.hq["developer_instructions"])

    def test_parent_self_check_never_replaces_independent_review(self):
        for required in ("implementer self-check, never independent review", "QA/E2E happy/fail",
                         "CR/ADV", "cross-model evidence", "final-snapshot approvals",
                         "Other explicit role routes remain delegated", "Missing delegation never becomes approval"):
            self.assertIn(required, self.ownership)
        for role in ("req-pl", "review-planner", "test-qa", "e2e-qa", "code-quality-reviewer",
                     "adviser", "reviewer", "sol-escalation"):
            self.assertIn(f"`{role}`", self.ownership)
        self.assertIn("Claude implementation", self.root)
        self.assertIn("retain `.claude/CLAUDE.md` routing and HQ child ownership", self.root)

    def test_no_fabricated_child_or_permission_changes(self):
        self.assertIn("EXECUTION: <parent | subagent>", self.codex)
        self.assertIn("without inventing a child ID", self.ownership)
        self.assertIn("No model, effort or permission settings change", self.ownership)
        self.assertIn("actual invocation evidence", self.root)

    def test_rule_reuse_does_not_skip_first_pass(self):
        rules = section(self.hq["developer_instructions"], "# Engineering Principles")
        for required in ("Nishiguchi", "Principle application", "ASYNC-1 / HTTP-1",
                         "including exceptions", "your own retained, verified unchanged readings",
                         "A separate worker must perform its own initial reading", "NEEDS_CONFIRMATION"):
            self.assertIn(required, rules)
        self.assertNotIn("An explicit mandatory-rule violation is not merely style", rules)
        self.assertIn("mandatory-rule versus optional-preference distinction", rules)

    def test_single_preflight_and_handoff_keep_pending_evidence(self):
        preflight = section(self.hq["developer_instructions"], "## Tech Lead Preflight Rule")
        self.assertIn("one preflight", preflight)
        self.assertNotIn("Required questions:", preflight)
        self.assertIn("Stop and consult specialists before editing", preflight)
        handoff = section(self.codex, "### Compact handoffs")
        for required in ("one finding/coverage record", "all open findings", "evidence gaps",
                         "native verdicts", "Workflow Result fields", "necessary original excerpts",
                         "independent first-pass inspection", "Required role output sections remain"):
            self.assertIn(required, handoff)

    def test_review_prompt_keeps_all_input_fields(self):
        fields = [name for _, name, _, _ in Formatter().parse(review_prompt(self.workflow)) if name]
        expected = {
            "prefix", "phase", "user_workflow_request", "project_root", "scope_and_base_head",
            "snapshot_id", "review_role", "reviewer", "model_and_invocation_evidence",
            "requirements_and_rules", "findings_fixes_and_answers", "phase_scope_and_coverage_ledger",
            "verification_evidence", "authority_ownership_findings_questions_and_response_contracts",
            "review_gates_qa_contract_and_current_phase_contract",
        }
        self.assertEqual(set(fields), expected)
        self.assertEqual(len(fields), len(expected))

    def test_round_changes_do_not_change_fixed_prompt_prefix(self):
        template = review_prompt(self.workflow)
        names = [name for _, name, _, _ in Formatter().parse(template) if name]
        values = {name: "fixed:" + name for name in names}
        dynamic = {"user_workflow_request", "project_root", "scope_and_base_head", "snapshot_id",
                   "model_and_invocation_evidence", "requirements_and_rules", "findings_fixes_and_answers",
                   "phase_scope_and_coverage_ledger", "verification_evidence"}
        a = template.format_map(values)
        b = template.format_map({**values, **{key: "changed:" + key for key in dynamic}})
        before_a, after_a = a.split("今回の入力:\n", 1)
        before_b, after_b = b.split("今回の入力:\n", 1)
        self.assertEqual(before_a, before_b)
        self.assertNotEqual(after_a, after_b)
        self.assertIn("fixed:authority_ownership_findings_questions_and_response_contracts", before_a)
        self.assertIn("Snapshot ID: changed:snapshot_id", after_b)
        for key in dynamic:
            self.assertNotIn("fixed:" + key, before_a)
            self.assertIn("changed:" + key, after_b)
        changed_rule = template.format_map({**values,
            "authority_ownership_findings_questions_and_response_contracts": "updated rules"})
        self.assertNotEqual(before_a, changed_rule.split("今回の入力:\n", 1)[0])

    def test_reverse_transport_approval_and_result_fields_remain(self):
        for required in ("- read-only", "毎roundで新しいexec", "exec resumeや--lastを使いません",
                         "主セッションだけの代読は不可", "両方の実agentを必ず呼びます",
                         "正常系（happy path）と異常系（fail path）", "[qa, e2e, l1_5, l2]"):
            self.assertIn(required, self.workflow)
        result = self.workflow.split("response_contract:\n", 1)[1].split("pause_and_resume:\n", 1)[0]
        fields = set(re.findall(r"(?m)^    ([a-z_]+):", result))
        self.assertEqual(fields, {"workflow_id", "phase", "reviewer", "snapshot_id", "native_verdict",
                                  "coverage", "decision", "open_item_ids", "questions", "handoffs",
                                  "invocation_evidence"})
        self.assertIn("古い4段階の承認を失効", self.workflow)
        self.assertIn("キャッシュのために古い規則を維持しません", self.workflow)


if __name__ == "__main__":
    unittest.main()
