"""Codex TOMLのコピー同期と、upstreamの保護を確認します。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_NAMES = ("hq-coder", "req-pl", "test-qa")
RETIRED_NAMES = ("hq", "pl", "qa")


class SetupChecks:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex sync ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "config source"
        self.target = self.root / "target project"
        self.source.mkdir()
        self.target.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.target)], check=True)
        for filename in ("setup.sh", "setup.ps1"):
            shutil.copyfile(REPO_ROOT / filename, self.source / filename)
        for profile in (".claude", ".claude-company"):
            for folder in ("agents", "skills", "knowledge"):
                (self.source / profile / folder).mkdir(parents=True)
            for filename in ("CLAUDE.md", "SKILL.md", "settings.json"):
                (self.source / profile / filename).write_text("", encoding="utf-8")

        self.source_agents = self.source / ".codex" / "agents"
        self.source_agents.mkdir(parents=True)
        for name in CANONICAL_NAMES:
            (self.source_agents / f"{name}.toml").write_text(
                f'name = "{name}"\ndescription = "sample"\n', encoding="utf-8"
            )
        (self.source / ".codex" / "AGENTS.md").write_text("", encoding="utf-8")
        self.source_config = self.source / ".codex" / "config.toml"
        self.source_config.write_text('model = "gpt-6.1-sol"\n', encoding="utf-8")

        (self.source / ".copilot" / "agents").mkdir(parents=True)
        (self.source / ".copilot" / "copilot-instructions.md").write_text(
            "", encoding="utf-8"
        )
        self.target_agents = self.target / ".codex" / "agents"
        self.target_agents.mkdir(parents=True)
        self.target_config = self.target / ".codex" / "config.toml"
        self.state_file = self.target / ".git" / "info" / "codex-setup-managed.tsv"

    def run_setup(self):
        if self.runner == "bash":
            command = [
                "bash", str(self.source / "setup.sh"),
                "--profile", "company", str(self.target),
            ]
        else:
            command = [
                "pwsh", "-NoProfile", "-File", str(self.source / "setup.ps1"),
                "-Profile", "company", "-Target", str(self.target),
            ]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def assert_canonical_copies(self):
        self.assertEqual(
            sorted(path.name for path in self.target_agents.iterdir()),
            sorted(f"{name}.toml" for name in CANONICAL_NAMES),
        )
        for name in CANONICAL_NAMES:
            path = self.target_agents / f"{name}.toml"
            self.assertFalse(path.is_symlink(), path)
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_bytes(), (self.source_agents / path.name).read_bytes())

        self.assertFalse(self.target_config.is_symlink())
        self.assertEqual(self.target_config.read_bytes(), self.source_config.read_bytes())

    def assert_clean_target(self):
        status = subprocess.run(
            ["git", "-C", str(self.target), "status", "--porcelain", "--untracked-files=all"],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(status.stdout, "", status.stdout)
        self.assertFalse((self.target / ".gitignore").exists())

    def test_fresh_install_and_repeat(self):
        self.run_setup()
        self.assert_canonical_copies()
        self.assertTrue(self.state_file.is_file())
        self.assertIn("agents/hq-coder.toml", self.state_file.read_text())
        self.assertIn("config.toml", self.state_file.read_text())
        self.assert_clean_target()

        exclude_file = self.target / ".git" / "info" / "exclude"
        before_exclude = exclude_file.read_bytes()
        before_state = self.state_file.read_bytes()
        self.run_setup()
        self.assert_canonical_copies()
        self.assertEqual(exclude_file.read_bytes(), before_exclude)
        self.assertEqual(self.state_file.read_bytes(), before_state)
        self.assert_clean_target()

    def test_retired_links_and_stale_source_are_migrated(self):
        for name in RETIRED_NAMES:
            destination = self.target_agents / f"{name}.toml"
            source = self.source_agents / destination.name
            if name == "pl":
                destination.symlink_to(os.path.relpath(source, destination.parent))
            else:
                destination.symlink_to(source)
        # 旧名の原本が残っても再展開しません。
        (self.source_agents / "qa.toml").write_text('name = "test-qa"\n')
        output = self.run_setup()
        self.assertEqual(output.count("[REMOVE retired]"), 3)
        self.assert_canonical_copies()
        self.run_setup()
        self.assert_canonical_copies()

    def test_existing_managed_links_are_converted(self):
        self.target_config.symlink_to(self.source_config)
        for name in CANONICAL_NAMES:
            file = self.source_agents / f"{name}.toml"
            (self.target_agents / file.name).symlink_to(file)
        self.run_setup()
        self.assert_canonical_copies()
        self.assert_clean_target()

    def test_local_files_and_foreign_links_are_preserved(self):
        foreign = self.root / "other config"
        foreign.mkdir()
        contents = {
            "hq.toml": b"original retired definition\n",
            "hq-coder.toml": b"original canonical definition\n",
        }
        for name, content in contents.items():
            (self.target_agents / name).write_bytes(content)
        targets = {}
        for name in ("pl.toml", "qa.toml", "req-pl.toml"):
            link_target = foreign / name
            if name != "qa.toml":
                link_target.write_text("external definition\n")
            (self.target_agents / name).symlink_to(link_target)
            targets[name] = os.readlink(self.target_agents / name)

        for _ in range(2):
            output = self.run_setup()
            self.assertIn("[CONFLICT preserved]", output)
            self.assertIn("統合完了ではありません", output)
            self.assertIn("[SKIP upstream]", output)
            for name, content in contents.items():
                self.assertEqual((self.target_agents / name).read_bytes(), content)
            for name, link_target in targets.items():
                self.assertTrue((self.target_agents / name).is_symlink())
                self.assertEqual(os.readlink(self.target_agents / name), link_target)
        self.assertEqual(
            (self.target_agents / "test-qa.toml").read_bytes(),
            (self.source_agents / "test-qa.toml").read_bytes(),
        )

    def test_new_agent_update_and_modified_copy_protection(self):
        self.run_setup()
        new_file = self.source_agents / "future-specialist.toml"
        new_file.write_text('name = "future-specialist"\nmodel = "v1"\n')
        output = self.run_setup()
        copied = self.target_agents / new_file.name
        self.assertFalse(copied.is_symlink())
        self.assertIn("[COPY] .codex/agents/future-specialist.toml", output)
        self.assertEqual(copied.read_bytes(), new_file.read_bytes())

        new_file.write_text('name = "future-specialist"\nmodel = "v2"\n')
        self.run_setup()
        self.assertEqual(copied.read_bytes(), new_file.read_bytes())

        copied.write_text('name = "local override"\n', encoding="utf-8")
        new_file.write_text('name = "future-specialist"\nmodel = "v3"\n')
        output = self.run_setup()
        self.assertIn("[CONFLICT preserved]", output)
        self.assertEqual(copied.read_text(), 'name = "local override"\n')
        self.assert_clean_target()

    def test_identical_manual_copy_is_adopted_and_refreshed(self):
        manual_copy = self.target_agents / "hq-coder.toml"
        shutil.copyfile(self.source_agents / manual_copy.name, manual_copy)
        output = self.run_setup()
        self.assertIn("[CURRENT] .codex/agents/hq-coder.toml", output)
        self.source_agents.joinpath(manual_copy.name).write_text(
            'name = "hq-coder"\nmodel = "new-version"\n',
            encoding="utf-8",
        )
        self.run_setup()
        self.assertEqual(
            manual_copy.read_bytes(),
            (self.source_agents / manual_copy.name).read_bytes(),
        )

    def test_config_is_synced_on_source_change(self):
        self.run_setup()
        self.source_config.write_text('model = "gpt-6.1-sol"\nmax_threads = 4\n')
        self.run_setup()
        self.assertEqual(self.target_config.read_bytes(), self.source_config.read_bytes())
        self.assertFalse(self.target_config.is_symlink())

    def test_git_tracked_files_are_never_overwritten(self):
        self.target_config.write_text('model = "upstream"\n', encoding="utf-8")
        own = self.target_agents / "hq-coder.toml"
        own.write_text('name = "owned-by-project"\n', encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.target), "add", "-f",
             ".codex/config.toml", ".codex/agents/hq-coder.toml"],
            check=True,
        )
        output = self.run_setup()
        self.assertIn("[SKIP tracked]", output)
        self.assertEqual(self.target_config.read_text(), 'model = "upstream"\n')
        self.assertEqual(own.read_text(), 'name = "owned-by-project"\n')
        self.assertEqual(
            (self.target_agents / "req-pl.toml").read_bytes(),
            (self.source_agents / "req-pl.toml").read_bytes(),
        )
        self.assertFalse((self.target / ".gitignore").exists())


class BashSetupTests(SetupChecks, unittest.TestCase):
    runner = "bash"


@unittest.skipUnless(shutil.which("pwsh"), "PowerShellがないため実行対象外です")
class PowerShellSetupTests(SetupChecks, unittest.TestCase):
    runner = "pwsh"


if __name__ == "__main__":
    unittest.main()
