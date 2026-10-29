"""規則の抜粋保持、更新検知、両profileへの配布を確認します。"""

import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preloads", ROOT / "tools/sync_engineering_preloads.py")
preloads = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preloads)


class PreloadTests(unittest.TestCase):
    def test_nested_conditions_and_exceptions_are_preserved(self):
        source = "## Rule\nRequired.\n### Exception\nConditional.\n## Next\nUnrelated.\n"
        self.assertEqual(preloads.section(source, "Rule"),
                         "## Rule\nRequired.\n### Exception\nConditional.")
        self.assertEqual(preloads.section(source, "Exception"), "### Exception\nConditional.")
        for text in ("## Other\n", "## Rule\nOne\n## Rule\nTwo\n"):
            with self.assertRaises(ValueError):
                preloads.section(text, "Rule")

    def test_document_tables_are_not_agent_frontmatter(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / ".claude/agents"
            directory.mkdir(parents=True)
            document = directory / "REVIEW_ARCHITECTURE.md"
            original = "# Architecture\n\n| Role | Scope |\n|---|---|\n| reviewer | convergence |\n"
            document.write_text(original)
            role = directory / "reviewer.md"
            role.write_text("---\nname: reviewer\nmodel: sonnet\n---\nRole body.\n")
            self.assertEqual(preloads.agent_files(root, ".claude"), [role])
            self.assertEqual(document.read_text(), original)

    def copy_sources(self, target):
        for profile in preloads.PROFILES:
            shutil.copytree(ROOT / profile / "knowledge", target / profile / "knowledge")

    def test_generation_detects_source_changes_and_never_writes_by_default(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.copy_sources(root)
            self.assertTrue(preloads.sync(root))
            self.assertFalse((root / ".claude/skills").exists())
            preloads.sync(root, write=True)
            self.assertEqual(preloads.sync(root), [])
            output = root / ".claude/skills/engineering-review-core/SKILL.md"
            before = output.read_bytes()
            for profile in preloads.PROFILES:
                source = root / profile / preloads.SOURCES["human"]
                source.write_text(source.read_text() + "\nSource revision changed.\n")
            self.assertTrue(preloads.sync(root))
            self.assertEqual(output.read_bytes(), before)
            preloads.sync(root, write=True)
            self.assertNotEqual(output.read_bytes(), before)
            self.assertEqual(preloads.sync(root), [])

    def test_conflicting_profile_sources_refuse_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.copy_sources(root)
            source = root / ".claude-company" / preloads.SOURCES["human"]
            source.write_text(source.read_text() + "\nDifferent company policy.\n")
            with self.assertRaises(ValueError):
                preloads.sync(root, write=True)
            self.assertFalse((root / ".claude/skills").exists())

    def test_checked_in_skills_and_role_references_are_current(self):
        self.assertEqual(preloads.sync(ROOT), [])
        for profile in preloads.PROFILES:
            roles = preloads.agent_files(ROOT, profile)
            self.assertTrue(roles)
            for role in roles:
                header = role.read_text().split("---", 2)[1]
                match = re.search(r"(?m)^skills:\n((?:  - [^\n]+\n)+)", header)
                self.assertIsNotNone(match, str(role))
                names = [line[4:] for line in match[1].splitlines()]
                self.assertIn("engineering-review-core", names)
                expected_extra = {"react-ui-flow": "engineering-react-rules",
                                  "nestjs-backend": "engineering-nest-rules"}.get(role.stem)
                if expected_extra:
                    self.assertIn(expected_extra, names)
                for name in names:
                    skill = ROOT / profile / "skills" / name / "SKILL.md"
                    self.assertTrue(skill.is_file(), str(skill))
                    self.assertNotIn("disable-model-invocation: true", skill.read_text())
        core = (ROOT / ".claude/skills/engineering-review-core/SKILL.md").read_text()
        self.assertIn("### Reject Condition", core)
        react = (ROOT / ".claude/skills/engineering-react-rules/SKILL.md").read_text()
        self.assertIn("### Required Check", react)

    def test_workflow_supplies_source_identity_once_and_preserves_resumes(self):
        workflow = (ROOT / ".codex/workflows/claude-review.yml").read_text()
        ownership = workflow.split("\nownership:\n", 1)[1].split("\nclaude_cli:\n", 1)[0]
        source_rule = re.search(r"(?m)^  preloaded_rule_sources: (.+)$", ownership)
        self.assertIsNotNone(source_rule)
        for source in preloads.SOURCES.values():
            self.assertIn(".claude/" + source, source_rule[1])
        self.assertIn("SHA-256", source_rule[1])
        self.assertIn("同一ownerの再開", source_rule[1])
        self.assertIn("変更時だけ更新", source_rule[1])
        for name, end in (("single_layer", "authority"), ("claude_cli", "review_entry")):
            block = workflow.split("\n" + name + ":\n", 1)[1].split("\n" + end + ":\n", 1)[0]
            initial = block.split("  prompt_template: |\n", 1)[1].split("  resume_prompt_template: |\n", 1)[0]
            resume = block.split("  resume_prompt_template: |\n", 1)[1]
            self.assertIn("{rule_source_identity}", initial)
            self.assertNotIn("{rule_source_identity}", resume)
            self.assertIn("{changed_rule_source_identity}", resume)

    def test_existing_setup_links_skills_for_both_profiles(self):
        with tempfile.TemporaryDirectory(prefix="preload setup ") as folder:
            base = Path(folder)
            source = base / "config source"
            source.mkdir()
            shutil.copyfile(ROOT / "setup.sh", source / "setup.sh")
            for profile in preloads.PROFILES:
                for subdir in ("agents", "skills", "knowledge"):
                    (source / profile / subdir).mkdir(parents=True)
                for name in preloads.SECTIONS:
                    shutil.copytree(ROOT / profile / "skills" / name,
                                    source / profile / "skills" / name)
                for role in (ROOT / profile / "agents").glob("*.md"):
                    shutil.copyfile(role, source / profile / "agents" / role.name)
            for profile in ("personal", "company"):
                target = base / profile
                subprocess.run(["git", "init", "--quiet", str(target)], check=True)
                command = ["bash", str(source / "setup.sh"), "--profile", profile, str(target)]
                first = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
                selected = ".claude" if profile == "personal" else ".claude-company"
                for name in preloads.SECTIONS:
                    link = target / ".claude/skills" / name
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(link.resolve(), source / selected / "skills" / name)
                    self.assertTrue((link / "SKILL.md").is_file())
                second = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(second.returncode, 0, second.stdout + second.stderr)


if __name__ == "__main__":
    unittest.main()
