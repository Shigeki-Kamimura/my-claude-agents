"""規則の抜粋保持、更新検知、両profileへの配布を確認します。"""

import importlib.util
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preloads", ROOT / "tools/sync_engineering_preloads.py")
preloads = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preloads)


class PreloadTests(unittest.TestCase):
    def test_isolated_generation_refuses_output_symlinks_before_any_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "candidate"
            self.copy_sources(root)
            outside = Path(folder) / "active-skills"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("active configuration")
            (root / ".agents").mkdir()
            (root / ".agents/skills").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "root外"):
                preloads.sync(root, write=True)
            self.assertEqual(sentinel.read_text(), "active configuration")
            self.assertEqual(list(outside.iterdir()), [sentinel])
            self.assertFalse((root / ".claude/skills").exists())
            self.assertFalse((root / ".claude-company/skills").exists())

    def test_cli_generates_isolated_copy_without_touching_active_rules(self):
        active = {p: p.read_bytes() for p in ROOT.glob(".agents/skills/*/SKILL.md")}
        active.update({ROOT / profile / relative: (ROOT / profile / relative).read_bytes()
                       for profile in preloads.PROFILES for relative in preloads.SOURCES.values()})
        with tempfile.TemporaryDirectory(prefix="isolated rules ") as folder:
            root = Path(folder)
            self.copy_sources(root)
            command = [sys.executable, "-I", "-B", str(ROOT / "tools/sync_engineering_preloads.py"),
                       "--root", str(root)]
            check = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(check.returncode, 1, check.stderr)
            self.assertFalse((root / ".agents").exists())
            write = subprocess.run(command + ["--write"], capture_output=True, text=True)
            self.assertEqual(write.returncode, 0, write.stderr)
            self.assertEqual(preloads.sync(root), [])
            self.assertEqual(len(list(root.glob(".agents/skills/*/SKILL.md"))), 3)
        for path, before in active.items():
            self.assertEqual(path.read_bytes(), before, str(path))

    def test_codex_excerpts_keep_actual_source_paths_bytes_and_permissions(self):
        for name, sources in preloads.CODEX_SECTIONS.items():
            rendered = preloads.render(ROOT, name, "codex")
            self.assertNotIn(".Codex", rendered)
            self.assertNotIn("codex-Codex-review", rendered)
            self.assertNotIn("Never run Bash/git merely", rendered)
            for source, titles in sources.items():
                relative = preloads.SOURCES[source]
                data = (ROOT / ".claude" / relative).read_bytes()
                self.assertIn(f"`.claude/{relative}`", rendered)
                self.assertIn(hashlib.sha256(data).hexdigest(), rendered)
                for title in titles:
                    self.assertIn(preloads.section(data.decode(), title), rendered)
        self.assertIn("Never run Bash/git merely", preloads.render(ROOT, "engineering-nest-rules"))

    def test_claude_partition_preserves_complete_originals_and_universal_rules(self):
        core = preloads.render(ROOT, "engineering-review-core")
        governance = (ROOT / ".claude" / preloads.SOURCES["governance"]).read_text()
        for title in ("Core rules for Claude preload", "Claude role-scoped intake",
                      "Pinned source and reconciliation", "User-directed execution permissions",
                      "Shared evidence and reporting", "Conditional UI rule intake"):
            self.assertIn(preloads.section(governance, title), core)
        for name, sources in preloads.SECTIONS.items():
            rendered = preloads.render(ROOT, name)
            for source, titles in sources.items():
                relative = preloads.SOURCES[source]
                data = (ROOT / ".claude" / relative).read_bytes()
                self.assertIn(f"`.claude/{relative}`", rendered)
                self.assertIn(hashlib.sha256(data).hexdigest(), rendered)
                for title in titles:
                    self.assertEqual(rendered.count(preloads.section(data.decode(), title)), 1)
        for title in ("Review objective and evidence", "Mandatory UI consistency and task usability",
                      "Review-layer approval and handoffs"):
            self.assertNotIn(f"### {title}\n", core)
        self.assertNotIn("## Responsibility Separation\n", core)
        delivery = preloads.section(governance, "Preloaded rule delivery")
        for name in preloads.SECTIONS:
            self.assertIn(f"`{name}`", delivery)

    def test_role_supplements_preserve_the_former_core_sections(self):
        governance = (ROOT / ".claude" / preloads.SOURCES["governance"]).read_text()
        human = (ROOT / ".claude" / preloads.SOURCES["human"]).read_text()
        principles = preloads.render(ROOT, "engineering-principles")
        self.assertIn(preloads.section(governance, "Review objective and evidence"), principles)
        for title in ("Responsibility Separation", "Exception Handling", "Type Safety",
                      "Refactoring Scope", "Design Document Alignment"):
            self.assertIn(preloads.section(human, title), principles)
        self.assertIn(preloads.section(governance, "Review-layer approval and handoffs"),
                      preloads.render(ROOT, "engineering-review-evidence"))
        self.assertIn(preloads.section(governance, "Mandatory UI consistency and task usability"),
                      preloads.render(ROOT, "engineering-ui-rules"))

    def test_ops_supplement_is_codex_core_only(self):
        heading = "### OPS-1: Release, operability and data-lifecycle boundaries"
        self.assertIn(heading, preloads.render(ROOT, "engineering-review-core", "codex"))
        self.assertNotIn(heading, preloads.render(ROOT, "engineering-review-core"))

    def test_cross_review_supplement_is_codex_core_only(self):
        heading = "### XREV-1: Cross-model review calibration lenses"
        self.assertIn(heading, preloads.render(ROOT, "engineering-review-core", "codex"))
        self.assertNotIn(heading, preloads.render(ROOT, "engineering-review-core"))
        phrases = ("read the class, do not assume",
                   "restore/spy-restore does not necessarily clear call history",
                   "Trace the parent route guard/role gate with the NEW state",
                   "co-occurring updates in the same request/transaction")
        codex = preloads.render(ROOT, "engineering-review-core", "codex")
        for profile in preloads.PROFILES:
            source = (ROOT / profile / preloads.SOURCES["governance"]).read_text()
            for phrase in phrases:
                self.assertIn(phrase, source)
                self.assertIn(phrase, codex)

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
            codex = root / ".agents/skills/engineering-nest-rules/SKILL.md"
            codex.write_text(codex.read_text().replace(".claude/knowledge", ".Codex/knowledge"))
            self.assertEqual(preloads.sync(root), [str(codex.relative_to(root))])
            preloads.sync(root, write=True)
            core = root / ".claude/skills/engineering-review-core/SKILL.md"
            core_before = core.read_bytes()
            output = root / ".claude/skills/engineering-principles/SKILL.md"
            before = output.read_bytes()
            for profile in preloads.PROFILES:
                source = root / profile / preloads.SOURCES["human"]
                source.write_text(source.read_text() + "\nSource revision changed.\n")
            self.assertTrue(preloads.sync(root))
            self.assertEqual(output.read_bytes(), before)
            preloads.sync(root, write=True)
            self.assertNotEqual(output.read_bytes(), before)
            self.assertEqual(core.read_bytes(), core_before)
            self.assertEqual(preloads.sync(root), [])

    def test_missing_original_or_profile_mirror_refuses_all_writes(self):
        for profile in preloads.PROFILES:
            for relative in preloads.SOURCES.values():
                with self.subTest(profile=profile, source=relative), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    self.copy_sources(root)
                    (root / profile / relative).unlink()
                    with self.assertRaises(FileNotFoundError):
                        preloads.sync(root, write=True)
                    for destination in (*preloads.PROFILES, ".agents"):
                        self.assertFalse((root / destination / "skills").exists())

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
                self.assertEqual(len(names), len(set(names)), str(role))
                self.assertEqual(role.stem != "review-planner", "engineering-principles" in names,
                                 str(role))
                review_owners = {"test-qa", "e2e-qa", "code-quality-reviewer", "adviser", "reviewer"}
                self.assertEqual(role.stem in review_owners, "engineering-review-evidence" in names,
                                 str(role))
                ui_owners = {"react-ui-flow", "vue-frontend", "ux-qa"}
                self.assertEqual(role.stem in ui_owners, "engineering-ui-rules" in names, str(role))
                if role.stem == "review-planner":
                    self.assertEqual(names, ["engineering-review-core"])
                expected_extra = {"react-ui-flow": "engineering-react-rules",
                                  "nestjs-backend": "engineering-nest-rules"}.get(role.stem)
                if expected_extra:
                    self.assertIn(expected_extra, names)
                for name in names:
                    skill = ROOT / profile / "skills" / name / "SKILL.md"
                    self.assertTrue(skill.is_file(), str(skill))
                    self.assertNotIn("disable-model-invocation: true", skill.read_text())
        principles = (ROOT / ".claude/skills/engineering-principles/SKILL.md").read_text()
        self.assertIn("### Reject Condition", principles)
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
        self.assertIn("Same-owner resumes", source_rule[1])
        self.assertIn("update only when originals change", source_rule[1])
        self.assertIn("common_contract: md-review.md", workflow)
        self.assertIn("Summaries never replace originals not injected.", source_rule[1])
        common = (ROOT / ".codex/workflows/md-review.md").read_text()
        self.assertIn("all scope, cumulative coverage, all open IDs", common)
        self.assertIn("completed same-phase parent session", common)

    def test_xrev1_lenses_skill_reaches_only_four_claude_review_layers(self):
        name = "engineering-review-lenses"
        source = preloads.section((ROOT / ".claude" / preloads.SOURCES["governance"]).read_text(),
                                  "XREV-1: Cross-model review calibration lenses")
        self.assertIn("**HND-1: Handoff weight and evidence-first reporting", source)
        self.assertEqual(preloads.render(ROOT, name).count(source), 1)
        self.assertNotIn("### XREV-1", preloads.render(ROOT, "engineering-review-core"))
        self.assertNotIn(name, preloads.CODEX_SECTIONS)
        self.assertFalse((ROOT / ".agents/skills" / name).exists())
        reviewers = {"test-qa", "e2e-qa", "code-quality-reviewer", "adviser"}
        for profile in preloads.PROFILES:
            installed = (ROOT / profile / "skills" / name / "SKILL.md").read_text()
            self.assertEqual(installed, preloads.render(ROOT, name))
            for role in preloads.agent_files(ROOT, profile):
                header = role.read_text().split("---", 2)[1]
                self.assertEqual(role.stem in reviewers,
                                 re.search(rf"(?m)^  - {name}$", header) is not None, f"{profile}/{role.stem}")

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
