"""SEC-IMPL-1とTEST-TRUTH-1の静的な整合性検査です。実機品質は未計測です。"""

from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = ".claude/knowledge/implementation-security-and-test-integrity.md"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class SecurityTestIntegrityTests(unittest.TestCase):
    def test_policy_mirrors(self):
        policy = read(POLICY)
        self.assertEqual(
            policy,
            read(".claude-company/knowledge/implementation-security-and-test-integrity.md"),
        )
        for required in (
            "SEC-IMPL-1", "TEST-TRUTH-1", "every authorized task",
            "actual changed-file inventory", "SEC_CLEAR", "SEC_PENDING",
            "ADV_REQUIRED", "ADV_NOT_APPLICABLE", "Do not obtain passing tests",
            "original protected behavior", "equivalent or stronger guarantee", "NOT_RUN",
        ):
            with self.subTest(required=required):
                self.assertIn(required, policy)

    def test_implementation_and_pl_security(self):
        for role in ("hq-coder", "req-pl", "sec-arch"):
            codex = read(f".codex/agents/{role}.toml")
            claude = read(f".claude/agents/{role}.md")
            self.assertEqual(claude, read(f".claude-company/agents/{role}.md"))
            self.assertIn("SEC-IMPL-1", codex)
            self.assertIn("SEC-IMPL-1", claude)
        for path in (
            ".codex/agents/hq-coder.toml", ".claude/agents/hq-coder.md",
            ".codex/agents/sec-arch.toml", ".claude/agents/sec-arch.md",
        ):
            self.assertIn("SEC_CLEAR", read(path))
            self.assertIn("SEC_PENDING", read(path))

    def test_sec_arch_permissions_unchanged(self):
        role = tomllib.loads(read(".codex/agents/sec-arch.toml"))
        self.assertEqual(role["sandbox_mode"], "read-only")
        self.assertEqual(role["model"], "gpt-6.1-sol")

    def test_qa_e2e_detect_weakened_tests(self):
        for role in ("test-qa", "e2e-qa"):
            claude = read(f".claude/agents/{role}.md")
            self.assertEqual(claude, read(f".claude-company/agents/{role}.md"))
            for path in (f".claude/agents/{role}.md", f".codex/agents/{role}.toml"):
                with self.subTest(path=path):
                    text = read(path)
                    self.assertIn("TEST-TRUTH-1", text)
                    self.assertIn("assertions", text)
                    self.assertIn("snapshots", text)
                    self.assertIn("NOT_RUN", text)

    def test_pcr_security_gate_and_risk_based_adv(self):
        flow = read(".codex/workflows/pcr-development.md")
        for required in (
            "SEC-IMPL-1", "TEST-TRUTH-1", "current-snapshot SEC_CLEAR",
            "ADV_REQUIRED", "ADV_NOT_APPLICABLE",
            "Claude Code", "independent Claude Code",
            "No extra CR or ci-reviewer", "no invented owner",
        ):
            with self.subTest(required=required):
                self.assertIn(required, flow)
        self.assertNotIn(chr(92) + chr(96), flow)
        for path in (".codex/AGENTS.md", ".claude/CLAUDE.md", ".claude-company/CLAUDE.md"):
            text = read(path)
            self.assertIn(POLICY, text)
            self.assertIn("SEC-IMPL-1", text)

    def test_desktop_sync_refers_to_original_policy(self):
        sync = read("sync_codex_desktop.py")
        self.assertIn("SEC_TEST_POLICY =", sync)
        self.assertIn("SEC_TEST_POLICY,", sync)
        self.assertIn("{source}/{SEC_TEST_POLICY}", sync)
        self.assertIn("Shared governance fallback", sync)

    def test_test_weakenings_not_approvable(self):
        policy = read(POLICY)
        for term in (".only/.todo", "lowering thresholds", "mocks", "fixtures",
                     "skipping", "coverage percentage alone", "authoritative"):
            self.assertIn(term.lower(), policy.lower())


if __name__ == "__main__":
    unittest.main()
