"""レビュー効率の集計と出力の安全性を合成ログで検証します。"""
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'review_efficiency_report.py'
spec = importlib.util.spec_from_file_location('review_efficiency_report', SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class EfficiencyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.parent = self.root / 'parent-session.jsonl'
        child = self.root / 'parent-session' / 'subagents' / 'agent-abc.jsonl'
        child.parent.mkdir(parents=True)
        child.with_suffix('.meta.json').write_text(
            json.dumps({'agentType': 'adviser'}), encoding='utf-8')

        def assistant(message_id, tools):
            return {'type': 'assistant', 'message': {
                'id': message_id, 'model': 'fixture-sonnet',
                'usage': {'input_tokens': 10, 'output_tokens': 4},
                'content': [{'type': 'tool_use', 'id': tool_id, 'name': name, 'input': args}
                            for tool_id, name, args in tools]}}

        def result(tool_id, error):
            return {'type': 'user', 'message': {
                'content': [{'type': 'tool_result', 'tool_use_id': tool_id, 'is_error': error}]}}

        first_slice = {'file_path': '/x/.claude/knowledge/engineering-governance.md',
                       'offset': 1, 'limit': 100}
        second_slice = {'file_path': first_slice['file_path'], 'offset': 101, 'limit': 100}
        self.parent.write_text('\n'.join(json.dumps(row) for row in [
            assistant('p1', [('pa', 'Agent', {'subagent_type': 'adviser'}),
                             ('r1', 'Read', first_slice)]),
            assistant('p1', [('pa', 'Agent', {'subagent_type': 'adviser'}),
                             ('r1', 'Read', first_slice)]),
            assistant('p2', [('s1', 'SendMessage', {'to': 'abc'})]),
            result('s1', False)
        ]) + '\n', encoding='utf-8')
        child.write_text('\n'.join(json.dumps(row) for row in [
            assistant('c1', [('r2', 'Read', first_slice),
                             ('r3', 'Read', second_slice),
                             ('grep1', 'Bash', {
                                 'command': 'rg governance.md /x/.claude/knowledge/engineering-governance.md'})]),
            assistant('c2', [('r4', 'Read', first_slice),
                             ('r5', 'Read', {
                                 'file_path': '/x/.claude/knowledge/human-review-patterns.md'})])
        ]) + '\n', encoding='utf-8')

    def test_distinguishes_owners_slices_and_search(self):
        value = report.scan_session(self.parent)
        self.assertEqual(1, value['new_agent_calls'])
        self.assertEqual(1, value['send_calls'])
        self.assertEqual(1, value['send_result_ok'])
        self.assertEqual(1, value['same_agent_rule_repeat_accesses'])
        actor = ('adviser (agent-abc)', 'engineering-governance.md')
        self.assertEqual(3, value['access_per_agent'][actor])
        self.assertEqual(1, value['search_per_agent'][actor])
        self.assertEqual(0, value['exact_read_repeat_per_agent'][
            ('parent', 'engineering-governance.md')])
        html = report.html_report([value])
        self.assertIn('同じ読み取り範囲', html)
        self.assertNotIn('rg governance.md', html)

    def test_only_private_excluded_repo_output(self):
        out = self.root / 'outside' / 'report.html'
        report.safe_output(out)
        report.private_write(out, 'private')
        self.assertEqual(0o600, stat.S_IMODE(out.stat().st_mode))
        repo = self.root / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        with self.assertRaises(ValueError):
            report.safe_output(repo / 'report.html')
        excluded = repo / '.git' / 'info' / 'exclude'
        excluded.write_text(excluded.read_text() + '\n.codex\n', encoding='utf-8')
        report.safe_output(repo / '.codex' / 'review-records' / 'record.html')
        with self.assertRaises(ValueError):
            report.safe_output(repo / 'unrelated' / 'record.html')


if __name__ == '__main__':
    unittest.main()
