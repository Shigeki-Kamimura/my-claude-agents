"""待機・再レビュー・既定モデルの説明の整合性を確認します。"""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (
    "AGENTS.md", ".codex/AGENTS.md",
    ".claude/CLAUDE.md", ".claude-company/CLAUDE.md",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """同じ階層か上位の見出しまでを返します。"""
    marker = heading + "\n"
    if text.count(marker) != 1:
        raise ValueError(f"見出しが一意ではありません: {heading}")
    body = text.split(marker, 1)[1]
    level = len(heading.split(" ", 1)[0])
    end = re.search(r"(?m)^#{1," + str(level) + r"} ", body)
    return body[:end.start()] if end else body


class InstructionScopeTests(unittest.TestCase):
    def test_common_wait_rules_are_unconditional(self):
        waiting = section(read(".codex/AGENTS.md"), "## Bounded subagent waiting")
        self.assertEqual(waiting.split("### Common waiting rules\n", 1)[0].strip(), "")
        common = section(waiting, "### Common waiting rules")
        self.assertIn("regardless of `multi_agent_v2` availability", common)
        for required in ("local CI", "Playwright", "exit status", "`write_stdin`",
                         "Do not spawn a separate child", "continue/resume",
                         "QA/E2E", "higher-priority limits"):
            self.assertIn(required, common)
        self.assertNotIn("When `multi_agent_v2`", common)
        self.assertNotIn("`wait_agent`", common)

    def test_optional_agent_wait_is_separate(self):
        tools = section(read(".codex/AGENTS.md"), "### Tool-specific subagent waits")
        self.assertIn("When `multi_agent_v2` subagents and `wait_agent` are available:", tools)
        for required in ("unfinished agents", "180000", "300000", "where supported",
                         "higher-priority limits", "`list_agents`", "do not enable"):
            self.assertIn(required, tools)
        self.assertNotIn("For local CI", tools)

    def test_rereview_direction_is_explicit_in_each_entrypoint(self):
        for path in ENTRYPOINTS:
            with self.subTest(path=path):
                direction = section(read(path), "### Re-review direction")
                lines = direction.splitlines()
                forward = [line for line in lines if line.startswith("- `codex-claude-review`:")]
                reverse = [line for line in lines if line.startswith("- `claude-codex-review`:")]
                self.assertEqual(len(forward), 1)
                self.assertEqual(len(reverse), 1)
                for required in ("Resume the same restricted Claude parent/child",
                                 "same phase only", "planned verification", "secure-resume exceptions"):
                    self.assertIn(required, forward[0])
                for required in ("fresh read-only `codex exec` every round",
                                 "Do not use `exec resume` or `--last`",
                                 "cumulative coverage", "all pending findings"):
                    self.assertIn(required, reverse[0])
                self.assertIn("Standalone reviews use their own continuation rules.", direction)

    def test_manual_resume_excludes_reverse_workflow(self):
        for path in ENTRYPOINTS:
            with self.subTest(path=path):
                operating = section(read(path), "## Review Operating Model")
                rules = [line for line in operating.splitlines()
                         if line.startswith(("- Re-review within", "- After fixes within"))]
                self.assertEqual(len(rules), 1)
                self.assertIn("outside `claude-codex-review`", rules[0])
                self.assertIn("fresh Codex rounds", rules[0])
                self.assertIn("`rev:`", rules[0])

    def test_codex_model_description_matches_settings(self):
        config = read(".codex/config.toml")
        model = re.findall(r'(?m)^model = "([^"]+)"$', config)
        effort = re.findall(r'(?m)^model_reasoning_effort = "([^"]+)"$', config)
        self.assertEqual(model, ["gpt-6.1-sol"])
        self.assertEqual(effort, ["high"])
        label = "GPT-6.1 Sol / " + effort[0]
        allocation = section(read(".codex/AGENTS.md"), "## Model Allocation")
        self.assertIn("- main coordinator -> " + label, allocation)
        self.assertIn("# - Keep the primary coordinator on " + label + ".", config)
        self.assertNotIn("main coordinator -> GPT-6 Luna", allocation)
        self.assertNotIn("primary coordinator on GPT-6 Luna", config)

    def test_claude_profiles_keep_shared_guidance_and_guards(self):
        personal = read(".claude/CLAUDE.md")
        company = read(".claude-company/CLAUDE.md")
        self.assertEqual(personal.rstrip(), company.split("## GuildBoard固有の成果物保存先", 1)[0].rstrip())
        for required in ("Codex exclusively runs typecheck", "Never resume an old unrestricted",
                         "happy/fail checks", "eleven `Workflow Result` fields",
                         "An unavailable rule, tool or required consultant blocks approval."):
            self.assertIn(required, personal)


if __name__ == "__main__":
    unittest.main()
