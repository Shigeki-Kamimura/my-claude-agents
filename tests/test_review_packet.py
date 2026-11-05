import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "review_packet.py"


class ReviewPacketTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.write("a.py", "def alpha():\n    return 1\n")
        self.write("old.txt", "".join("line %d\n" % i for i in range(20)))
        self.write("gone.txt", "bye\n")
        self.write("big.py", "".join("x%d = %d\n" % (i, i) for i in range(300)))
        self.write("user.py", "from a import alpha\nprint(alpha())\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "feature")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout

    def write(self, name, content):
        (self.repo / name).write_text(content)

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def packet(self, *extra, base="main", head="feature"):
        return subprocess.run([sys.executable, "-I", "-B", str(TOOL), "--repo", str(self.repo), "--base", base, "--head", head, *extra],
                              capture_output=True, text=True)

    def change(self):
        self.write("a.py", "def alpha(x=0):\n    return 2\n")
        self.git("mv", "old.txt", "new.txt")
        self.git("rm", "-q", "gone.txt")
        lines = ["x%d = %d\n" % (i, i) for i in range(300)]
        lines[150] = "x150 = 'changed'\n"
        self.write("big.py", "".join(lines))
        self.commit("change")

    def test_normal_diff_and_identity(self):
        self.change()
        r = self.packet()
        self.assertEqual(r.returncode, 0, r.stderr)
        base, head = self.git("rev-parse", "main").strip(), self.git("rev-parse", "feature").strip()
        self.assertIn(base, r.stdout)
        self.assertIn(head, r.stdout)
        self.assertIn("merge-base: " + base, r.stdout)
        self.assertIn("return 2", r.stdout)
        self.assertLess(r.stdout.index("## 1."), r.stdout.index("## 2."))
        self.assertLess(r.stdout.index("## 3."), r.stdout.index("## 7."))
        # symbol reference found in the other file, not the defining file
        self.assertIn("user.py", r.stdout.split("## 5.")[1].split("## 6.")[0])

    def test_rename_and_delete(self):
        self.change()
        r = self.packet()
        self.assertIn("old.txt -> new.txt", r.stdout)
        self.assertRegex(r.stdout, r"D\tgone\.txt")
        self.assertIn("gone.txt (deleted at head)", r.stdout)

    def test_large_file_partial(self):
        self.change()
        r = self.packet("--max-file-lines", "100")
        self.assertIn("PARTIAL: lines", r.stdout)
        self.assertIn("x150 = 'changed'", r.stdout.split("## 4.")[1])
        self.assertNotIn("x10 = 10", r.stdout.split("## 4.")[1])

    def test_worktree_untracked(self):
        self.change()
        self.write("a.py", "def alpha():\n    return 3\n")
        self.write("fresh.txt", "brand new\n")
        r = self.packet("--worktree")
        self.assertEqual(r.returncode, 0, r.stderr)
        section = r.stdout.split("## W.")[1]
        self.assertIn("return 3", section)
        self.assertIn("untracked fresh.txt", section)
        self.assertIn("brand new", section)
        self.assertNotIn("## W.", self.packet().stdout)

    def test_whole_packet_truncation_and_manifest(self):
        self.change()
        r = self.packet("--max-chars", "6000")
        self.assertEqual(r.returncode, 0, r.stderr)
        manifest = r.stdout.split("## 7.")[1]
        self.assertIn("TRUNCATED: section", manifest)
        self.assertIn("PACKET TRUNCATED", r.stdout)
        self.assertIn("estimated tokens", manifest)
        self.assertIn("return 2", r.stdout)  # diff is never truncated

    def test_manifest_lists_ref_cap(self):
        self.change()
        self.write("many.py", "".join("alpha()\n" for _ in range(1)) + "".join("# alpha %d\n" % i for i in range(20)))
        self.commit("more refs")
        r = self.packet("--max-refs", "2")
        self.assertIn("TRUNCATED: references for `alpha`", r.stdout)

    def test_req_from_head_tree(self):
        self.write("REQ.md", "must do things\n")
        self.commit("req")
        r = self.packet("--req", "feature:REQ.md")
        self.assertIn("must do things", r.stdout)

    def test_bad_refs_rejected(self):
        for base, head in (("--output=/tmp/x", "feature"), ("main", "nosuchref"), ("main", "-h")):
            r = self.packet(base=base, head=head)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("error:", r.stderr)
            self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
