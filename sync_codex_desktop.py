#!/usr/bin/env python3
"""Desktop 用の定義を検査し、明示指定時だけコピーします。Python 3.11+。"""
import argparse
import contextlib
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import tomllib

BEGIN = '<!-- codex-desktop-sync:begin -->'
END = '<!-- codex-desktop-sync:end -->'
MODEL = {'model', 'model_reasoning_effort', 'model_reasoning_summary', 'model_verbosity'}
CORE = {'name', 'description', 'developer_instructions'}
REFS = ('.codex/AGENTS.md', '.codex/workflows/claude-review.yml',
        '.codex/workflows/codex-review.yml', '.claude/knowledge/engineering-governance.md',
        '.claude/knowledge/human-review-patterns.md')


class Stop(RuntimeError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return path.read_bytes() if path.exists() else None


def toml(data, label):
    try:
        result = tomllib.loads(data.decode('utf-8'))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise Stop(f'{label}: invalid TOML: {exc}') from exc
    return result


def scalar(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return '[' + ', '.join(scalar(v) for v in value) + ']'
    if isinstance(value, dict):
        return '{' + ', '.join(json.dumps(k) + ' = ' + scalar(v) for k, v in value.items()) + '}'
    raise Stop(f'Unsupported TOML value type: {type(value).__name__}')


def encode(role):
    # 意味は保持し、長い指示の比較は別途行単位で表示します。
    return ('\n'.join(k + ' = ' + scalar(v) for k, v in role.items()) + '\n').encode()


def safe(root, relative):
    part = Path(relative)
    if part.is_absolute() or '..' in part.parts:
        raise Stop(f'Unsafe managed path: {relative}')
    target = root / part
    for current in [root, *reversed(list(target.parents)[:len(part.parts) - 1]), target]:
        if current.is_symlink():
            raise Stop(f'Symlink is not writable by this updater: {current}')
    if not target.resolve().is_relative_to(root.resolve()):
        raise Stop(f'Path escapes destination: {target}')
    return target


def inventory(root):
    result = {}
    folder = safe(root, 'agents')
    if folder.exists():
        for item in folder.rglob('*'):
            if item.is_symlink():
                raise Stop(f'Agent discovery contains a symlink: {item}')
            if item.is_file() and item.suffix == '.toml':
                result[str(item.relative_to(root))] = item.read_bytes()
    return result


def roles(files):
    seen = {}
    parsed = {}
    for name, data in files.items():
        role = toml(data, name)
        for key in CORE:
            if not isinstance(role.get(key), str) or not role[key].strip():
                raise Stop(f'{name}: requires nonempty string {key}')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', role['name']):
            raise Stop(f'{name}: unsafe role name')
        if role['name'] in seen:
            raise Stop(f'Duplicate role {role["name"]}: {seen[role["name"]]} and {name}')
        seen[role['name']] = name
        parsed[name] = role
    return parsed


def git_state(source):
    def run(*args):
        p = subprocess.run(['git', '-C', str(source), *args], capture_output=True, text=True)
        if p.returncode:
            raise Stop('Source must be an existing Git worktree')
        return p.stdout.strip()
    return {'revision': run('rev-parse', 'HEAD'), 'branch': run('branch', '--show-current'),
            'status': run('status', '--porcelain')}


def snapshot(source):
    result = {}
    for rel in REFS:
        path = source / rel
        if not path.is_file() or not path.resolve().is_relative_to(source):
            raise Stop(f'Missing or external shared reference: {path}')
        result[rel] = path.read_bytes()
    result['.codex/config.toml'] = read(source / '.codex/config.toml')
    if result['.codex/config.toml']:
        config = toml(result['.codex/config.toml'], 'source config')
        if any(isinstance(v, dict) for v in config.get('agents', {}).values()):
            raise Stop('Source has explicit agent registrations; resolve mapping before syncing')
    folder = source / '.codex/agents'
    if not folder.is_dir():
        raise Stop('Source .codex/agents is missing')
    for path in folder.rglob('*'):
        if path.is_symlink():
            raise Stop(f'Source role symlink is ambiguous: {path}')
        if path.is_file() and path.suffix == '.toml':
            if path.parent != folder:
                raise Stop('Nested source role files require an explicit mapping')
            result[str(path.relative_to(source))] = path.read_bytes()
    if not any(k.startswith('.codex/agents/') for k in result):
        raise Stop('Source has no role definitions')
    return result


def block(source):
    return f'''{BEGIN}
Desktop shared references (project-specific rules/profile remain authoritative):
- Routing and explicit cross-model review contracts: {source}/.codex/AGENTS.md
- Codex implementation / Claude review: {source}/.codex/workflows/claude-review.yml
- Claude implementation / Codex review: {source}/.codex/workflows/codex-review.yml
- Shared governance fallback: {source}/.claude/knowledge/engineering-governance.md
- Shared review knowledge fallback: {source}/.claude/knowledge/human-review-patterns.md
Use project-local configured references first. If a shared local link is absent,
read the applicable shared original above and report the fallback and setup gap.
For an explicitly authorized cross-model workflow, read the matching contract and
pass its active marker, phase, actual request and required role to the actual owner.
Keep the project working directory. Quoted markers do not activate a workflow.
Missing project requirements or mandatory evidence remain pending. References do
not authorize test execution, a review chain, or permission changes. Standalone
commands retain their behavior. Parent read-only requirements remain mandatory.
These shared references are live source files; installed TOML definitions are snapshots.
{END}'''


def legacy_global(source):
    # 既存一回限りの導入ブロックだけを完全一致で移行します。
    template = Path(__file__).with_name('desktop_sync_legacy.txt')
    return template.read_text().replace('@SOURCE@', str(source))


def owned(text, replacement, source, global_file=False):
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise Stop('Malformed owned reference markers')
        start, stop = text.index(BEGIN), text.index(END) + len(END)
        if stop < start:
            raise Stop('Reversed owned reference markers')
        return text[:start] + replacement + text[stop:]
    if global_file and '## Desktop independent QA and E2E review references' in text:
        old = legacy_global(source)
        if not text.endswith(old) or text.count('## Desktop independent QA and E2E review references') != 1:
            raise Stop('Legacy global block was edited; migrate it manually into owned markers')
        return text[:-len(old)] + replacement + '\n'
    return text.rstrip('\n') + '\n\n' + replacement + '\n'


def plan(source, destination):
    state = git_state(source)
    src = snapshot(source)
    existing = inventory(destination)
    installed = roles(existing)
    supplied = roles({k.removeprefix('.codex/'): v for k, v in src.items()
                      if k.startswith('.codex/agents/')})
    original = {**existing, 'AGENTS.md': read(safe(destination, 'AGENTS.md')),
                'config.toml': read(safe(destination, 'config.toml'))}
    if original['config.toml'] and any(isinstance(v, dict) for v in
            toml(original['config.toml'], 'destination config').get('agents', {}).values()):
        raise Stop('Destination has explicit role registrations; resolve mapping before syncing')
    changes = {}
    notes = []
    for filename, incoming in supplied.items():
        if Path(filename).stem != incoming['name']:
            raise Stop(f'{filename}: filename must match canonical name; aliases are input routing only')
        for oldfile, oldrole in installed.items():
            if oldrole['name'] == incoming['name'] and oldfile != filename:
                raise Stop(f'Canonical name collision: {filename} / {oldfile}; nothing deleted')
        merged = dict(incoming)
        before = installed.get(filename)
        if before is not None and before['name'] != incoming['name']:
            raise Stop(f'{filename}: existing custom role has another name; nothing overwritten')
        security = (set(incoming) | set(before or {})) - CORE - MODEL
        for key in security:
            if before is not None:
                if key in incoming and incoming[key] != before.get(key):
                    raise Stop(f'{filename}: security/config delta at {key}; separate approval required')
                if key in before:
                    merged[key] = before[key]
            elif key == 'sandbox_mode' and incoming[key] == 'read-only':
                pass
            elif key == 'features' and isinstance(incoming[key], dict) and all(v is False for v in incoming[key].values()):
                pass
            else:
                raise Stop(f'{filename}: new role setting {key} needs separate review')
        for key in MODEL:
            if before is not None and key in before:
                merged[key] = before[key]
                if incoming.get(key) != before[key]:
                    notes.append(f'{filename}: preserved local {key}')
        instructions = merged['developer_instructions']
        bad = '.Codex/knowledge/human-review-patterns.md'
        if bad in instructions:
            instructions = instructions.replace(bad, str(source / '.claude/knowledge/human-review-patterns.md'))
            notes.append(f'{filename}: repaired legacy .Codex knowledge reference')
        for ref in re.findall(r'(?<![A-Za-z0-9_/])(?:\.claude|\.codex|\.Codex)/(?:knowledge|workflows)/[A-Za-z0-9_.-]+\.(?:md|yml)', instructions):
            if not (source / ref).is_file():
                raise Stop(f'{filename}: unresolved shared source reference {ref}')
        merged['developer_instructions'] = owned(instructions, block(source), source)
        data = encode(merged)
        if parse_equal(existing.get(filename), data):
            data = existing[filename]
        changes[filename] = data
    text = (original['AGENTS.md'] or b'').decode('utf-8')
    changes['AGENTS.md'] = owned(text, block(source), source, global_file=True).encode()
    final = {**existing, **{k: v for k, v in changes.items() if k.startswith('agents/')}}
    roles(final)
    for filename, data in changes.items():
        safe(destination, filename)
        for ref in re.findall(r'/[^\s`<>"\']+/(?:AGENTS\.md|[^/\s`<>"\']+\.(?:md|yml))', data.decode()):
            # 機械管理する共有原本の参照だけを検査し、例のプロジェクトパスは解釈しません。
            if ref.startswith(str(source) + '/') and not Path(ref).is_file():
                raise Stop(f'{filename}: missing shared reference {ref}')
    changes = {k: v for k, v in changes.items() if original.get(k) != v}
    return {'source': source, 'destination': destination, 'source_state': state,
            'source_bytes': src, 'original': original, 'changes': changes, 'notes': notes}


def parse_equal(a, b):
    return a is not None and toml(a, 'installed') == toml(b, 'planned')


def display(p):
    print('Source:', p['source'], json.dumps(p['source_state'], ensure_ascii=False))
    print('Destination:', p['destination'])
    for note in p['notes']:
        print('KEEP:', note)
    for name, data in p['changes'].items():
        old = p['original'].get(name) or b''
        def lines(raw):
            if name.endswith('.toml') and raw:
                d = toml(raw, name)
                return [f'{k} = {scalar(v)}\n' for k, v in d.items() if k != 'developer_instructions'] + d['developer_instructions'].splitlines(True)
            return raw.decode().splitlines(True)
        print(''.join(difflib.unified_diff(lines(old), lines(data), fromfile='installed/' + name,
                                         tofile='planned/' + name)), end='')
    print(f'Planned files: {len(p["changes"])}. No app restart or session reload is performed.')


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, name = tempfile.mkstemp(prefix='.' + path.name, suffix='.sync-tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def lock(destination):
    path = safe(destination, '.desktop-agent-sync.lock')
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise Stop(f'Updater lock exists: {path}; check another updater before removing a stale lock') from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink()


def check_plan(p):
    if snapshot(p['source']) != p['source_bytes'] or git_state(p['source']) != p['source_state']:
        raise Stop('Source changed after planning; rerun dry-run')
    if inventory(p['destination']) != {k: v for k, v in p['original'].items() if k.startswith('agents/')}:
        raise Stop('Destination agent discovery changed after planning')
    for name, data in p['original'].items():
        if read(safe(p['destination'], name)) != data:
            raise Stop(f'Destination changed after planning: {name}')


def apply(p):
    if not p['changes']:
        print('No changes; no backup created.')
        return None
    dest = p['destination']
    with lock(dest):
        check_plan(p)
        root = safe(dest, 'backups/desktop-agent-sync')
        if root.exists():
            for path in root.glob('*/manifest.json'):
                if json.loads(path.read_text()).get('status') in {'prepared', 'applying', 'rollback_failed'}:
                    raise Stop(f'Unfinished transaction: {path.parent}; inspect and --restore it first')
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        backup = safe(dest, 'backups/desktop-agent-sync/' + stamp)
        backup.mkdir(parents=True)
        manifest = {'version': 1, 'destination': str(dest), 'source': str(p['source']),
                    'source_state': p['source_state'], 'status': 'prepared', 'files': {}}
        for name, data in p['changes'].items():
            old = p['original'].get(name)
            entry = {'before': sha(old) if old is not None else None, 'after': sha(data)}
            if old is not None:
                atomic(safe(backup, name), old)
                if read(backup / name) != old:
                    raise Stop('Backup verification failed')
            manifest['files'][name] = entry
        meta = backup / 'manifest.json'
        atomic(meta, json.dumps(manifest, indent=2).encode())
        written = []
        try:
            check_plan(p)
            manifest['status'] = 'applying'
            atomic(meta, json.dumps(manifest, indent=2).encode())
            for name, data in p['changes'].items():
                target = safe(dest, name)
                if read(target) != p['original'].get(name):
                    raise Stop(f'Concurrent edit: {name}')
                atomic(target, data)
                written.append(name)
            if snapshot(p['source']) != p['source_bytes'] or git_state(p['source']) != p['source_state']:
                raise Stop('Source changed during apply')
            for name, data in p['changes'].items():
                if read(safe(dest, name)) != data:
                    raise Stop(f'Write verification failed: {name}')
            manifest['status'] = 'applied'
            atomic(meta, json.dumps(manifest, indent=2).encode())
        except BaseException:
            try:
                for name in reversed(written):
                    target = safe(dest, name)
                    if read(target) != p['changes'][name]:
                        raise Stop(f'Refusing to overwrite concurrent edit during rollback: {name}')
                    old = p['original'].get(name)
                    if old is None:
                        target.unlink()
                    else:
                        atomic(target, old)
                manifest['status'] = 'rolled_back'
            except BaseException:
                manifest['status'] = 'rollback_failed'
                raise
            finally:
                atomic(meta, json.dumps(manifest, indent=2).encode())
                print('Recovery backup:', backup, file=sys.stderr)
            raise
        print('Applied. Verified backup:', backup)
        return backup


def restore(destination, backup, do_apply):
    backup = backup.absolute()
    base = safe(destination, 'backups/desktop-agent-sync').resolve()
    if backup.parent.resolve() != base or backup.is_symlink():
        raise Stop('Restore requires an immediate backup under destination/backups/desktop-agent-sync')
    meta = safe(backup, 'manifest.json')
    m = json.loads(meta.read_text())
    if m.get('version') != 1 or m.get('destination') != str(destination):
        raise Stop('Backup destination/version mismatch')
    actions = []
    for name, entry in m['files'].items():
        if name != 'AGENTS.md' and not re.fullmatch(r'agents/[A-Za-z0-9_-]+\.toml', name):
            raise Stop('Backup contains an unmanaged path')
        target = safe(destination, name)
        old = read(safe(backup, name)) if entry['before'] is not None else None
        if (sha(old) if old is not None else None) != entry['before']:
            raise Stop(f'Backup hash mismatch: {name}')
        current = read(target)
        current_hash = sha(current) if current is not None else None
        if current_hash not in (entry['before'], entry['after']):
            raise Stop(f'Restore would overwrite subsequent edits: {name}')
        if current_hash != entry['before']:
            actions.append((name, old))
    print('Restore plan:', [name for name, _ in actions])
    if do_apply:
        with lock(destination):
            for name, old in actions:
                target = safe(destination, name)
                if sha(read(target)) != m['files'][name]['after']:
                    raise Stop(f'Concurrent edit before restore: {name}')
                if old is None:
                    target.unlink()
                else:
                    atomic(target, old)
            m['status'] = 'restored'
            atomic(meta, json.dumps(m, indent=2).encode())
        print('Restored verified original files; later edits were not overwritten.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='configuration repository root')
    parser.add_argument('--destination', required=True, type=Path, help='effective CODEX_HOME (not agents directory)')
    parser.add_argument('--apply', action='store_true', help='write the displayed plan; default is read-only')
    parser.add_argument('--dry-run', action='store_true', help='explicit read-only plan (also the default)')
    parser.add_argument('--restore', type=Path, help='verified backup to restore; also requires --apply to write')
    args = parser.parse_args(argv)
    if args.apply and args.dry_run:
        parser.error('--dry-run and --apply are mutually exclusive')
    dest = args.destination.expanduser().absolute()
    if not dest.is_dir() or dest.is_symlink():
        raise Stop('Destination must be an existing, non-symlink Codex home')
    # 入力経路の途中もリンクを拒否し、想定外の場所への書き込みを防ぎます。
    if any(x.is_symlink() for x in [dest, *dest.parents]):
        raise Stop('Destination path contains a symlink')
    if args.restore:
        restore(dest, args.restore, args.apply)
        return
    if not args.source:
        parser.error('--source is required unless --restore is used')
    source = args.source.expanduser().resolve()
    if source.is_relative_to(dest.resolve()) or dest.resolve().is_relative_to(source):
        raise Stop('Source and destination must not overlap')
    p = plan(source, dest)
    display(p)
    if args.apply:
        apply(p)
    else:
        print('DRY RUN: no files written. Add --apply only after reviewing this diff.')


if __name__ == '__main__':
    try:
        main()
    except (Stop, OSError, ValueError) as exc:
        print('STOP:', exc, file=sys.stderr)
        sys.exit(2)
