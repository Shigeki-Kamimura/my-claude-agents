"""一時設定だけを使い、上書き・権限・復旧の境界を確認します。"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'sync_codex_desktop.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).with_name('sync_codex_desktop.py')
spec = importlib.util.spec_from_file_location('sync_desktop', SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class DesktopSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='desktop sync ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.dest = self.root / 'desktop'
        self.source.mkdir()
        self.dest.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        for name in sync.REFS:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# fixture shared contract\n')
        (self.source / sync.PCR_SKILL_SOURCE).write_text(
            '---\nname: parallel-cr\ndescription: Explicit PCR-1 fixture.\n---\n\n# parallel-cr\nRead the PCR-1 contract.\n')
        (self.source / '.codex/config.toml').write_text('[agents]\nmax_threads=6\n')
        (self.source / '.codex/agents').mkdir()
        self.put('worker')
        subprocess.run(['git', '-C', str(self.source), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.source), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        (self.dest / 'config.toml').write_text('model="local-model"\n')
        (self.dest / 'AGENTS.md').write_text('Human instructions remain.\n')

    def put(self, name, instructions='Old source instructions.\n', extra=None, filename=None):
        role = {'name': name, 'description': 'Scoped role', 'developer_instructions': instructions}
        role.update(extra or {})
        (self.source / '.codex/agents' / (filename or name + '.toml')).write_bytes(sync.encode(role))

    def plan(self):
        return sync.plan(self.source, self.dest)

    def apply(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.apply(self.plan())

    def tree(self, root):
        return {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file()}

    def test_default_dry_run_has_no_writes(self):
        before = self.tree(self.dest)
        with contextlib.redirect_stdout(io.StringIO()):
            sync.main(['--source', str(self.source), '--destination', str(self.dest)])
        self.assertEqual(self.tree(self.dest), before)
        self.assertFalse((self.dest / '.desktop-agent-sync.lock').exists())

    def test_apply_backup_upgrade_noop_and_custom_preserved(self):
        (self.dest / 'agents').mkdir()
        custom = sync.encode({'name': 'personal', 'description': 'mine', 'developer_instructions': 'Keep.'})
        (self.dest / 'agents/custom.toml').write_bytes(custom)
        config = (self.dest / 'config.toml').read_bytes()
        backup = self.apply()
        m = json.loads((backup / 'manifest.json').read_text())
        self.assertEqual(m['status'], 'applied')
        self.assertEqual((backup / 'AGENTS.md').read_text(), 'Human instructions remain.\n')
        self.assertEqual(self.plan()['changes'], {})
        self.assertIsNone(self.apply())
        self.put('worker', 'New source obligation.\n')
        self.assertIn('New source obligation.', self.plan()['changes']['agents/worker.toml'].decode())
        self.apply()
        self.assertEqual((self.dest / 'agents/custom.toml').read_bytes(), custom)
        self.assertEqual((self.dest / 'config.toml').read_bytes(), config)

    def test_override_security_and_model_retained(self):
        (self.dest / 'agents').mkdir()
        old = {'name': 'worker', 'description': 'old', 'developer_instructions': 'old',
               'model': 'my-model', 'model_reasoning_effort': 'xhigh', 'sandbox_mode': 'read-only',
               'features': {'shell_tool': False}}
        (self.dest / 'agents/worker.toml').write_bytes(sync.encode(old))
        self.put('worker', extra={'model': 'new-source-model'})
        after = sync.toml(self.plan()['changes']['agents/worker.toml'], 'planned')
        for key in ['model', 'model_reasoning_effort', 'sandbox_mode', 'features']:
            self.assertEqual(after[key], old[key])
        self.put('worker', extra={'sandbox_mode': 'workspace-write'})
        with self.assertRaisesRegex(sync.Stop, 'security/config delta'):
            self.plan()

    def test_existing_service_tier_and_unspecified_state_are_preserved(self):
        (self.dest / 'agents').mkdir()
        for local, incoming in [('flex', 'fast'), ('fast', 'fast'), ('fast', None), (None, 'fast')]:
            with self.subTest(local=local, incoming=incoming):
                old = {'name': 'worker', 'description': 'old', 'developer_instructions': 'old'}
                if local is not None:
                    old['service_tier'] = local
                (self.dest / 'agents/worker.toml').write_bytes(sync.encode(old))
                self.put('worker', 'Updated source instructions.',
                         extra={'service_tier': incoming} if incoming is not None else {})
                before = self.tree(self.dest)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    sync.main(['--source', str(self.source), '--destination', str(self.dest), '--dry-run'])
                self.assertEqual(self.tree(self.dest), before)
                if local != incoming:
                    self.assertIn('KEEP:', output.getvalue())
                    self.assertIn('service_tier', output.getvalue())
                self.apply()
                after = sync.toml((self.dest / 'agents/worker.toml').read_bytes(), 'installed')
                self.assertEqual(after.get('service_tier'), local)
                self.assertEqual('service_tier' in after, local is not None)
                self.assertIn('Updated source instructions.', after['developer_instructions'])
                self.assertEqual(self.plan()['changes'], {})

    def test_new_role_service_tier_is_installed(self):
        self.put('worker', extra={'service_tier': 'fast'})
        self.apply()
        after = sync.toml((self.dest / 'agents/worker.toml').read_bytes(), 'installed')
        self.assertEqual(after['service_tier'], 'fast')
        self.assertEqual(self.plan()['changes'], {})

    def test_new_permission_expansion_stops(self):
        self.put('worker', extra={'sandbox_mode': 'workspace-write', 'service_tier': 'fast'})
        with self.assertRaisesRegex(sync.Stop, 'separate review'):
            self.plan()
        self.put('worker', extra={'features': {'shell_tool': True}, 'service_tier': 'fast'})
        with self.assertRaises(sync.Stop):
            self.plan()

    def test_aliases_are_not_extra_definitions(self):
        self.put('worker', filename='alias.toml')
        with self.assertRaisesRegex(sync.Stop, 'Duplicate role'):
            self.plan()
        (self.source / '.codex/agents/alias.toml').unlink()
        (self.source / '.codex/agents/worker.toml').rename(self.source / '.codex/agents/alias.toml')
        with self.assertRaisesRegex(sync.Stop, 'filename must match'):
            self.plan()

    def test_duplicate_custom_role_name_stops_without_delete(self):
        self.apply()
        path = self.dest / 'agents/alias.toml'
        path.write_bytes((self.dest / 'agents/worker.toml').read_bytes())
        before = path.read_bytes()
        with self.assertRaisesRegex(sync.Stop, 'Duplicate role'):
            self.plan()
        self.assertEqual(path.read_bytes(), before)

    def test_same_filename_with_custom_name_is_not_overwritten(self):
        (self.dest / 'agents').mkdir()
        path = self.dest / 'agents/worker.toml'
        path.write_bytes(sync.encode({'name': 'my-special-worker', 'description': 'mine',
                                     'developer_instructions': 'custom'}))
        with self.assertRaisesRegex(sync.Stop, 'existing custom role'):
            self.plan()

    def test_malformed_source_missing_reference_and_registration(self):
        path = self.source / '.codex/agents/worker.toml'
        path.write_text('name= [broken')
        with self.assertRaisesRegex(sync.Stop, 'invalid TOML'):
            self.plan()
        self.put('worker')
        ref = self.source / sync.REFS[0]
        ref.unlink()
        with self.assertRaisesRegex(sync.Stop, 'Missing or external'):
            self.plan()
        ref.write_text('restored')
        (self.source / '.codex/config.toml').write_text('[agents.custom]\nconfig_file="x.toml"\n')
        with self.assertRaisesRegex(sync.Stop, 'registrations'):
            self.plan()

    def test_source_dirty_is_recorded_and_not_modified(self):
        self.put('worker', 'uncommitted instruction')
        before = self.tree(self.source)
        p = self.plan()
        self.assertTrue(p['source_state']['status'])
        with contextlib.redirect_stdout(io.StringIO()):
            sync.apply(p)
        self.assertEqual(self.tree(self.source), before)

    def test_concurrent_source_or_target_change_stops(self):
        p = self.plan()
        self.put('worker', 'concurrent source edit')
        with self.assertRaisesRegex(sync.Stop, 'Source changed'):
            sync.apply(p)
        p = self.plan()
        (self.dest / 'AGENTS.md').write_text('human concurrent edit')
        with self.assertRaisesRegex(sync.Stop, 'Destination changed'):
            sync.apply(p)

    def test_target_and_backup_path_escape_and_symlink_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.dest / 'agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(sync.Stop, 'Symlink'):
            self.plan()
        (self.dest / 'agents').unlink()
        (self.dest / 'backups').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(sync.Stop, 'Symlink'):
            self.apply()
        with self.assertRaises(sync.Stop):
            sync.safe(self.dest, '../escape')

    def test_global_owned_block_and_legacy_migration(self):
        legacy = sync.legacy_global(self.source)
        path = self.dest / 'AGENTS.md'
        path.write_text('Human exact prefix.\n' + legacy)
        p = self.plan()
        text = p['changes']['AGENTS.md'].decode()
        self.assertTrue(text.startswith('Human exact prefix.\n'))
        self.assertEqual(text.count(sync.BEGIN), 1)
        self.apply()
        self.assertEqual(self.plan()['changes'], {})
        path.write_text('Human exact prefix.\n' + legacy.replace('Keep the target project', 'Edited target project'))
        with self.assertRaisesRegex(sync.Stop, 'Legacy global block was edited'):
            self.plan()

    def test_global_user_suffix_preserved_and_bad_markers_rejected(self):
        self.apply()
        path = self.dest / 'AGENTS.md'
        path.write_text(path.read_text() + '\nHuman suffix.\n')
        self.assertEqual(self.plan()['changes'], {})
        path.write_text(path.read_text() + sync.BEGIN)
        with self.assertRaisesRegex(sync.Stop, 'Malformed owned'):
            self.plan()

    def test_qa_reference_repaired_without_changing_source(self):
        text = 'Read .Codex/knowledge/human-review-patterns.md\n'
        self.put('worker', text)
        after = sync.toml(self.plan()['changes']['agents/worker.toml'], 'planned')
        self.assertIn(str(self.source / '.claude/knowledge/human-review-patterns.md'), after['developer_instructions'])
        self.assertEqual(sync.toml((self.source / '.codex/agents/worker.toml').read_bytes(), 'source')['developer_instructions'], text)

    def test_unresolved_instruction_reference_stops(self):
        self.put('worker', 'Read .claude/knowledge/not-installed.md')
        with self.assertRaisesRegex(sync.Stop, 'unresolved shared source reference'):
            self.plan()

    def test_failure_rolls_back_and_leaves_verified_backup(self):
        before = self.tree(self.dest)
        actual = sync.atomic
        def fail(path, data):
            if path == self.dest / 'AGENTS.md':
                raise OSError('simulated write failure')
            return actual(path, data)
        with patch.object(sync, 'atomic', side_effect=fail), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(OSError):
                sync.apply(self.plan())
        for name, data in before.items():
            self.assertEqual((self.dest / name).read_bytes(), data)
        self.assertFalse((self.dest / 'agents/worker.toml').exists())
        manifest = next((self.dest / 'backups/desktop-agent-sync').glob('*/manifest.json'))
        self.assertEqual(json.loads(manifest.read_text())['status'], 'rolled_back')

    def test_restore_hash_integrity_and_later_edit_protection(self):
        backup = self.apply()
        before = self.tree(self.dest)
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, False)
        self.assertEqual(self.tree(self.dest), before)
        target = self.dest / 'agents/worker.toml'
        installed = target.read_bytes()
        target.write_text('user later edit')
        with self.assertRaisesRegex(sync.Stop, 'subsequent edits'):
            sync.restore(self.dest, backup, True)
        target.write_bytes(installed)
        # バックアップ改変は実設定に触れる前に停止します。
        (backup / 'AGENTS.md').write_text('corrupt backup')
        with self.assertRaisesRegex(sync.Stop, 'Backup hash mismatch'):
            sync.restore(self.dest, backup, True)

    def test_source_mutation_during_apply_rolls_back(self):
        before = self.tree(self.dest)
        actual = sync.atomic
        def mutate(path, data):
            actual(path, data)
            if path == self.dest / 'agents/worker.toml':
                self.put('worker', 'concurrent source modification')
        with patch.object(sync, 'atomic', side_effect=mutate), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(sync.Stop, 'Source changed during apply'):
                self.apply()
        self.assertFalse((self.dest / 'agents/worker.toml').exists())
        self.assertEqual((self.dest / 'AGENTS.md').read_bytes(), before['AGENTS.md'])

    def test_partial_rollback_has_recoverable_manifest(self):
        self.apply()
        self.put('worker', 'upgraded')
        original = (self.dest / 'agents/worker.toml').read_bytes()
        actual = sync.atomic
        def deny(path, data):
            if path == self.dest / 'AGENTS.md' or (path == self.dest / 'agents/worker.toml' and data == original):
                raise OSError('simulated denial including rollback')
            return actual(path, data)
        # AGENTS を変更対象にし、最初の定義を書いた後で失敗させます。
        (self.dest / 'AGENTS.md').write_text('User replacement without owned block.\n')
        with patch.object(sync, 'atomic', side_effect=deny), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(OSError):
                self.apply()
        backups = sorted((self.dest / 'backups/desktop-agent-sync').glob('*/manifest.json'))
        failed = backups[-1]
        self.assertEqual(json.loads(failed.read_text())['status'], 'rollback_failed')
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, failed.parent, True)
        self.assertEqual((self.dest / 'agents/worker.toml').read_bytes(), original)

    def test_tampered_restore_path_and_active_lock_are_refused(self):
        backup = self.apply()
        meta = backup / 'manifest.json'
        m = json.loads(meta.read_text())
        m['files']['../escape'] = {'before': None, 'after': 'x'}
        meta.write_text(json.dumps(m))
        with self.assertRaisesRegex(sync.Stop, 'unmanaged path'):
            sync.restore(self.dest, backup, True)
        self.put('worker', 'next update')
        (self.dest / '.desktop-agent-sync.lock').write_text('another process')
        with self.assertRaisesRegex(sync.Stop, 'Updater lock exists'):
            self.apply()

    def test_restore_applied_and_interrupted_transaction(self):
        backup = self.apply()
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, True)
        self.assertFalse((self.dest / 'agents/worker.toml').exists())
        self.assertEqual((self.dest / 'AGENTS.md').read_text(), 'Human instructions remain.\n')
        backup = self.apply()
        meta = backup / 'manifest.json'
        m = json.loads(meta.read_text())
        m['status'] = 'applying'
        meta.write_text(json.dumps(m))
        self.put('worker', 'another update')
        with self.assertRaisesRegex(sync.Stop, 'Unfinished transaction'):
            self.apply()
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, True)

    def test_parallel_skill_and_parent_entry_are_installed(self):
        p = self.plan()
        skill = p['changes'][sync.PCR_SKILL].decode()
        self.assertTrue(skill.startswith('---\nname: parallel-cr\n'))
        for path in (sync.PCR_SKILL_SOURCE, sync.PCR_CONTRACT, sync.PCR_GUIDE):
            self.assertIn(str(self.source / path), skill)
        self.assertIn('Read the PCR-1 contract.', skill)
        self.assertIn('Preserve mandatory rule/exception checks.', skill)
        self.assertIn('Project rules, disabled skills', p['changes']['AGENTS.md'].decode())
        self.assertIn(str(self.dest / sync.PCR_SKILL), p['changes']['AGENTS.md'].decode())
        self.assertIn('Plain cr: remains a single reviewer.', p['changes']['AGENTS.md'].decode())
        worker = sync.toml(p['changes']['agents/worker.toml'], 'planned')
        self.assertNotIn('Parent-only explicit PCR-1', worker['developer_instructions'])
        self.assertNotIn('agents/parallel-cr.toml', p['changes'])
        self.assertEqual(set(p['changes']), {'agents/worker.toml', 'AGENTS.md', sync.PCR_SKILL, sync.PCR_STATE})
        self.apply()
        state = json.loads((self.dest / sync.PCR_STATE).read_text())
        self.assertEqual(state['sha256'], sync.sha((self.dest / sync.PCR_SKILL).read_bytes()))
        self.assertEqual(self.plan()['changes'], {})

    def test_repository_skill_body_and_front_matter_are_preserved(self):
        raw = (SCRIPT.parent / sync.PCR_SKILL_SOURCE).read_bytes()
        header, separator, body = raw.decode().partition('\n---\n')
        installed = sync.parallel_skill(self.source, raw).decode()
        self.assertTrue(installed.startswith(header + separator))
        self.assertTrue(installed.endswith(body.lstrip('\n')))
        self.assertIn(sync.sha(raw), installed)
        self.assertIn('only the PCR-1 contract, not missing project requirements', installed)

    def test_existing_desktop_receives_only_parent_and_skill_changes(self):
        (self.dest / 'agents').mkdir()
        old = sync.toml((self.source / '.codex/agents/worker.toml').read_bytes(), 'source')
        old['developer_instructions'] = sync.owned(old['developer_instructions'], sync.block(self.source), self.source)
        (self.dest / 'agents/worker.toml').write_bytes(sync.encode(old))
        (self.dest / 'AGENTS.md').write_text(sync.owned('Human instructions remain.\n', sync.block(self.source), self.source))
        p = self.plan()
        self.assertEqual(set(p['changes']), {'AGENTS.md', sync.PCR_SKILL, sync.PCR_STATE})
        self.apply()
        self.assertTrue((self.dest / 'AGENTS.md').read_text().startswith('Human instructions remain.\n'))

    def test_missing_parallel_source_files_stop_before_writes(self):
        before = self.tree(self.dest)
        for rel in (sync.PCR_SKILL_SOURCE, sync.PCR_CONTRACT, sync.PCR_GUIDE):
            with self.subTest(path=rel):
                path = self.source / rel
                old = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(sync.Stop, 'Missing or external'):
                    self.plan()
                path.write_bytes(old)
        self.assertEqual(self.tree(self.dest), before)

    def test_invalid_parallel_skill_front_matter_stops(self):
        path = self.source / sync.PCR_SKILL_SOURCE
        for text in ('missing header', '---\nname: wrong\ndescription: Invalid.\n---\nBody\n',
                     '---\nname: parallel-cr\nname: parallel-cr\ndescription: Duplicate.\n---\nBody\n',
                     '---\nname: parallel-cr\n---\nBody\n',
                     '---\nname: parallel-cr\ndescription: Empty body.\n---\n'):
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaisesRegex(sync.Stop, 'front matter'):
                    self.plan()
        self.assertFalse((self.dest / sync.PCR_SKILL).exists())

    def test_unmanaged_parallel_skill_is_not_overwritten(self):
        path = self.dest / sync.PCR_SKILL
        path.parent.mkdir(parents=True)
        path.write_text('User-owned skill.\n')
        before = self.tree(self.dest)
        with self.assertRaisesRegex(sync.Stop, 'Unmanaged parallel-cr'):
            self.apply()
        self.assertEqual(self.tree(self.dest), before)

    def test_identical_unmanaged_skill_can_be_adopted(self):
        data = self.plan()['changes'][sync.PCR_SKILL]
        path = self.dest / sync.PCR_SKILL
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        self.assertNotIn(sync.PCR_SKILL, self.plan()['changes'])
        self.apply()
        self.assertEqual(path.read_bytes(), data)
        self.assertEqual(self.plan()['changes'], {})

    def test_managed_parallel_skill_edits_and_deletion_are_protected(self):
        self.apply()
        path = self.dest / sync.PCR_SKILL
        path.write_text(path.read_text() + '\nUser edit.\n')
        with self.assertRaisesRegex(sync.Stop, 'edited or removed'):
            self.plan()
        path.unlink()
        with self.assertRaisesRegex(sync.Stop, 'edited or removed'):
            self.plan()

    def test_invalid_parallel_ownership_is_not_ignored(self):
        self.apply()
        path = self.dest / sync.PCR_STATE
        for raw in ('{bad', '[]', '{"version": 1}',
                    json.dumps({'version': 1, 'path': '../outside', 'sha256': '0' * 64}),
                    json.dumps({'version': 1, 'path': sync.PCR_SKILL, 'sha256': 'bad'})):
            with self.subTest(raw=raw):
                path.write_text(raw)
                with self.assertRaisesRegex(sync.Stop, 'ownership record'):
                    self.plan()

    def test_parallel_paths_reject_symlinks(self):
        outside = self.root / 'outside'
        outside.mkdir()
        for rel in ('skills', 'skills/parallel-cr', sync.PCR_SKILL, sync.PCR_STATE):
            with self.subTest(path=rel):
                target = self.dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(sync.Stop, 'Symlink'):
                    self.plan()
                target.unlink()

    def test_concurrent_parallel_destination_change_stops(self):
        self.apply()
        for rel in (sync.PCR_SKILL, sync.PCR_STATE):
            with self.subTest(path=rel):
                self.put('worker', 'An update to make apply check the plan.\n')
                p = self.plan()
                path = self.dest / rel
                original = path.read_bytes()
                path.write_bytes(original + b'\nConcurrent edit.\n')
                with self.assertRaisesRegex(sync.Stop, 'Destination changed'):
                    sync.apply(p)
                path.write_bytes(original)

    def test_concurrent_parallel_source_change_stops(self):
        for rel in (sync.PCR_SKILL_SOURCE, sync.PCR_CONTRACT, sync.PCR_GUIDE):
            with self.subTest(path=rel):
                p = self.plan()
                path = self.source / rel
                old = path.read_bytes()
                path.write_bytes(old + b'\nConcurrent edit.\n')
                with self.assertRaisesRegex(sync.Stop, 'Source changed'):
                    sync.apply(p)
                path.write_bytes(old)

    def test_parallel_source_update_and_restore_preserve_old_skill(self):
        self.apply()
        skill = (self.dest / sync.PCR_SKILL).read_bytes()
        state = (self.dest / sync.PCR_STATE).read_bytes()
        source = self.source / sync.PCR_SKILL_SOURCE
        source.write_text(source.read_text() + '\nNew scoped obligation.\n')
        backup = self.apply()
        self.assertIn(b'New scoped obligation.', (self.dest / sync.PCR_SKILL).read_bytes())
        self.assertEqual(self.plan()['changes'], {})
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, True)
        self.assertEqual((self.dest / sync.PCR_SKILL).read_bytes(), skill)
        self.assertEqual((self.dest / sync.PCR_STATE).read_bytes(), state)

    def test_parallel_first_install_restore_removes_managed_files_only(self):
        other = self.dest / 'skills/personal/SKILL.md'
        other.parent.mkdir(parents=True)
        other.write_text('Unrelated skill.\n')
        backup = self.apply()
        before = self.tree(self.dest)
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, False)
        self.assertEqual(self.tree(self.dest), before)
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, True)
        self.assertFalse((self.dest / sync.PCR_SKILL).exists())
        self.assertFalse((self.dest / sync.PCR_STATE).exists())
        self.assertEqual(other.read_text(), 'Unrelated skill.\n')
        self.assertEqual((self.dest / 'config.toml').read_text(), 'model="local-model"\n')

    def test_parallel_write_failure_rolls_back(self):
        actual = sync.atomic
        def fail(path, data):
            if path == self.dest / sync.PCR_STATE:
                raise OSError('simulated ownership write failure')
            return actual(path, data)
        with patch.object(sync, 'atomic', side_effect=fail), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(OSError):
                self.apply()
        self.assertFalse((self.dest / sync.PCR_SKILL).exists())
        self.assertFalse((self.dest / sync.PCR_STATE).exists())
        self.assertFalse((self.dest / 'agents/worker.toml').exists())
        self.assertEqual((self.dest / 'AGENTS.md').read_text(), 'Human instructions remain.\n')
        meta = next((self.dest / 'backups/desktop-agent-sync').glob('*/manifest.json'))
        self.assertEqual(json.loads(meta.read_text())['status'], 'rolled_back')

    def test_parallel_restore_refuses_subsequent_skill_edits(self):
        backup = self.apply()
        path = self.dest / sync.PCR_SKILL
        path.write_text(path.read_text() + '\nUser edit.\n')
        before = self.tree(self.dest)
        with self.assertRaisesRegex(sync.Stop, 'subsequent edits'):
            sync.restore(self.dest, backup, True)
        self.assertEqual(self.tree(self.dest), before)

    def test_restore_does_not_allow_arbitrary_skill_paths(self):
        backup = self.apply()
        meta = backup / 'manifest.json'
        state = json.loads(meta.read_text())
        state['files']['skills/personal/SKILL.md'] = {'before': None, 'after': 'x'}
        meta.write_text(json.dumps(state))
        with self.assertRaisesRegex(sync.Stop, 'unmanaged path'):
            sync.restore(self.dest, backup, True)

    def test_legacy_backup_without_skill_files_is_restorable(self):
        backup = self.apply()
        meta = backup / 'manifest.json'
        state = json.loads(meta.read_text())
        for rel in (sync.PCR_SKILL, sync.PCR_STATE):
            del state['files'][rel]
        meta.write_text(json.dumps(state))
        skill = (self.dest / sync.PCR_SKILL).read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            sync.restore(self.dest, backup, True)
        self.assertEqual((self.dest / sync.PCR_SKILL).read_bytes(), skill)
        self.assertFalse((self.dest / 'agents/worker.toml').exists())


if __name__ == '__main__':
    unittest.main()
