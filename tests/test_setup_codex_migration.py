"""旧Codexリンクの移行と、利用者の定義の保護を確認します。"""

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
        self.temp = tempfile.TemporaryDirectory(prefix="codex migration ")
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
                f'name = "{name}"\n', encoding="utf-8"
            )
        for filename in ("AGENTS.md", "config.toml"):
            (self.source / ".codex" / filename).write_text("", encoding="utf-8")
        (self.source / ".copilot" / "agents").mkdir(parents=True)
        (self.source / ".copilot" / "copilot-instructions.md").write_text(
            "", encoding="utf-8"
        )
        self.target_agents = self.target / ".codex" / "agents"
        self.target_agents.mkdir(parents=True)

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

    def assert_canonical_links(self):
        self.assertEqual(
            sorted(path.name for path in self.target_agents.iterdir()),
            sorted(f"{name}.toml" for name in CANONICAL_NAMES),
        )
        for name in CANONICAL_NAMES:
            path = self.target_agents / f"{name}.toml"
            self.assertTrue(path.is_symlink())
            self.assertEqual(path.resolve(), self.source_agents / path.name)

    def test_fresh_install_and_repeat(self):
        self.run_setup()
        self.assert_canonical_links()
        before = (self.target / ".git" / "info" / "exclude").read_bytes()
        self.run_setup()
        self.assert_canonical_links()
        self.assertEqual(
            (self.target / ".git" / "info" / "exclude").read_bytes(), before
        )

    def test_retired_links_and_stale_source_are_migrated(self):
        for name in RETIRED_NAMES:
            destination = self.target_agents / f"{name}.toml"
            source = self.source_agents / destination.name
            if name == "pl":
                destination.symlink_to(os.path.relpath(source, destination.parent))
            else:
                destination.symlink_to(source)
        # 生きた旧リンクも移行し、残存する旧ソースを再展開しません。
        (self.source_agents / "qa.toml").write_text('name = "test-qa"\n')
        output = self.run_setup()
        self.assertEqual(output.count("[REMOVE retired]"), 3)
        self.assert_canonical_links()
        self.run_setup()
        self.assert_canonical_links()

    def test_local_files_and_foreign_links_are_preserved(self):
        foreign = self.root / "other config"
        foreign.mkdir()
        contents = {
            "hq.toml": b'original retired definition\n',
            "hq-coder.toml": b'original canonical definition\n',
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
            (self.target_agents / "test-qa.toml").resolve(),
            self.source_agents / "test-qa.toml",
        )


class BashSetupTests(SetupChecks, unittest.TestCase):
    runner = "bash"


@unittest.skipUnless(shutil.which("pwsh"), "PowerShellがないため実行対象外です")
class PowerShellSetupTests(SetupChecks, unittest.TestCase):
    runner = "pwsh"


if __name__ == "__main__":
    unittest.main()
