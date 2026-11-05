#!/usr/bin/env python3
"""レビューMDと固定したGit読取用snapshotを管理します。"""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid

LAYERS = {"qa": "test-qa", "e2e": "e2e-qa", "cr": "code-quality-reviewer", "adv": "adviser", "ci": "ci-reviewer"}
ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(project, *args):
    """objectとindexの読取りだけに使います。filterを実行しません。"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(["git", "--no-pager", "--literal-pathspecs", "-c", "core.fsmonitor=false", "-C", str(project), *args],
                            env=env, capture_output=True, timeout=30, check=True)
    return result.stdout


def private_write(path, content):
    with open(path, "x", encoding="utf-8", opener=lambda p, f: os.open(p, f, 0o600)) as stream:
        stream.write(content)


def secret_path(value):
    return any(p == ".env" or p.startswith(".env.") and p not in (".env.example", ".env.sample") for p in Path(value).parts)


def safe_path(value, allow_secret=False):
    path = Path(value)
    if path.is_absolute() or not path.parts or any(p in ("..", ".git") for p in path.parts):
        raise ValueError("対象はリポジトリ内の相対パスで指定してください")
    if secret_path(value) and not allow_secret:
        raise ValueError("秘密を含む環境ファイルはレビューsnapshotへ保存できません")
    return path.as_posix()


def excluded_path(name, exclusions):
    return any(name == path or name.startswith(path + "/") for path in exclusions)


def changed_paths(config):
    """Git拡張を起動せず、branch/index/生ファイル/未追跡を照合します。"""
    project = Path(config["project"])
    paths = set()
    for args in (("diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", config["base"], "HEAD", "--"),
                 ("diff", "--cached", "--name-only", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", "HEAD", "--"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        paths.update(os.fsdecode(p) for p in git(project, *args).split(b"\0") if p)
    algorithm = git(project, "rev-parse", "--show-object-format").decode().strip()
    if algorithm not in ("sha1", "sha256"):
        raise ValueError("Git object形式が未対応です")
    excluded = set(config.get("exclusions", {}))
    for entry in git(project, "ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        meta, raw_name = entry.split(b"\t", 1)
        mode, oid, stage = meta.decode().split()
        name = os.fsdecode(raw_name)
        if excluded_path(name, excluded) or secret_path(name):
            continue
        if stage != "0":
            raise ValueError(f"競合中のindexです: {name}")
        if mode == "160000":
            raise ValueError(f"submoduleの作業状態は未対応です。明示的な除外が必要です: {name}")
        source = project / safe_path(name)
        if any(p.is_symlink() for p in source.parents if p.is_relative_to(project) and p != project):
            raise ValueError(f"対象の親がsymlinkです: {name}")
        if source.is_symlink():
            actual_mode, data = "120000", os.fsencode(os.readlink(source))
        elif source.is_file():
            actual_mode = "100755" if source.stat().st_mode & stat.S_IXUSR else "100644"
            data = source.read_bytes()
        elif not source.exists():
            paths.add(name)
            continue
        else:
            raise ValueError(f"通常ファイルではありません: {name}")
        actual_oid = hashlib.new(algorithm, f"blob {len(data)}\0".encode() + data).hexdigest()
        if actual_mode != mode or actual_oid != oid:
            paths.add(name)
    paths = {safe_path(p, allow_secret=True) for p in paths}
    secrets = sorted(p for p in paths if secret_path(p))
    return sorted(p for p in paths if not excluded_path(p, excluded) and p not in secrets), secrets


def check_scope(config):
    if os.environ.get("GIT_INDEX_FILE"):
        raise ValueError("別indexの伝播は未対応です。元の設定を変更せず保留してください")
    overlap = {p for p in config["paths"] if excluded_path(p, config.get("exclusions", {}))}
    if overlap:
        raise ValueError("対象と除外が重複しています: " + ", ".join(sorted(overlap)))
    paths, secrets = changed_paths(config)
    missing = sorted(set(paths) - set(config["paths"]))
    if missing:
        raise ValueError("レビュー対象から変更が漏れています: " + ", ".join(missing))
    return {"changed_paths": paths, "secret_exclusions": secrets, "explicit_exclusions": config.get("exclusions", {})}


def atomic_text(path, text):
    if path.is_symlink() or path.exists() and path.stat().st_nlink != 1:
        raise ValueError("管理ファイルのリンクは更新できません")
    temporary = path.parent / (str(uuid.uuid4()) + ".tmp")
    private_write(temporary, text)
    os.replace(temporary, path)


def current_request(folder, request):
    path = folder / "review.md"
    body = path.read_text()
    body = re.sub(r"\A<!-- md-review-current:begin -->.*?<!-- md-review-current:end -->\n\n", "", body, count=1, flags=re.S)
    header = "<!-- md-review-current:begin -->\n## Current request\n\n```json\n" + json.dumps(request, ensure_ascii=False, indent=2) + "\n```\n<!-- md-review-current:end -->\n\n"
    atomic_text(path, header + body)


def journal_body(folder):
    text = (folder / "review.md").read_text()
    return re.sub(r"\A<!-- md-review-current:begin -->.*?<!-- md-review-current:end -->\n\n", "", text, count=1, flags=re.S)


def journal_reference(text, start, length):
    return {"start": start, "length": length, "sha256": digest(text[start:start + length].encode())}


def journal_read(folder, reference):
    start, length = reference["start"], reference["length"]
    if type(start) is not int or type(length) is not int or start < 0 or length < 1:
        raise ValueError("MD参照の範囲が不正です")
    content = journal_body(folder)[start:start + length]
    if len(content) != length or digest(content.encode()) != reference["sha256"]:
        raise ValueError("MD参照の本文が変更または欠落しています")
    return content


def journal_index(folder, config):
    """旧runは実記録で境界を確認します。本文の見出しを信用しません。"""
    if "summary_reference" not in config:
        body = journal_body(folder)
        entries = legacy_entries(folder, body)
        end = entries[0][0] if entries else len(body)
        config["summary_reference"] = journal_reference(body, 0, end)
        config["updates"] = []
        config["legacy_result_references"] = {}
        for start, text, kind in entries:
            reference = journal_reference(body, start, len(text))
            if kind == "update":
                config["updates"].append(reference)
            else:
                match = re.match(r"\n\n## (qa|e2e|cr|adv|ci) / ([0-9a-f-]{36})\n\n", text)
                config["legacy_result_references"][match[2]] = {"phase": match[1], "reference": reference}
        atomic_text(folder / "run.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    journal_read(folder, config["summary_reference"])
    for reference in config.get("updates", []):
        journal_read(folder, reference)
    for entry in config.get("legacy_result_references", {}).values():
        journal_read(folder, entry["reference"])


def legacy_entries(folder, body):
    entries = []
    for path in folder.glob("*/execution.json"):
        if not re.fullmatch(r"[0-9a-f-]{36}", path.parent.name):
            continue
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError("旧runの実行記録がsymlinkです")
        meta = json.loads(path.read_text())
        if meta.get("phase") not in LAYERS or meta.get("artifacts") != str(path.parent):
            raise ValueError("旧runの実行記録を確認できません")
        result = path.parent / "result.md"
        if result.is_symlink():
            raise ValueError("旧runの実応答がsymlinkです")
        if result.is_file():
            content = "```json\n" + json.dumps({k: v for k, v in meta.items() if k != "argv"}, ensure_ascii=False, indent=2) + "\n```\n\n" + result.read_text()
        elif meta.get("failure") == "CLI_CONFIGURATION_UNCONFIRMED":
            content = json.dumps(meta, ensure_ascii=False)
        else:
            raise ValueError("旧runの実応答が欠落しています")
        text = journal_entry(f"{meta['phase']} / {path.parent.name}", content)
        if body.count(text) != 1:
            raise ValueError("旧runの実結果の境界が曖昧です")
        entries.append((body.index(text), text, "result"))
    heading = "\n\n## Implementation update\n\n"
    for path in folder.glob("fix-*.md"):
        if not re.fullmatch(r"fix-[0-9a-f-]{36}\.md", path.name):
            continue
        if path.is_symlink():
            raise ValueError("旧runの修正原本がsymlinkです")
        note, matches = path.read_text().strip(), []
        if not note:
            raise ValueError("旧runの修正原本が空です")
        for match in re.finditer(re.escape(heading), body):
            tail = body[match.end():]
            line = tail.split("\n", 1)[0]
            try:
                meta = json.loads(line)
            except ValueError:
                continue
            if not isinstance(meta, dict) or set(meta) != {"snapshot_id", "added_paths", "added_rules"}:
                continue
            text = heading + line + "\n\n" + note + "\n"
            if body.startswith(text, match.start()):
                matches.append((match.start(), text, "update"))
        if len(matches) != 1:
            raise ValueError("旧runの修正記録の境界が曖昧です")
        entries.extend(matches)
    entries.sort()
    if not entries and re.search(r"\n\n## (Implementation update|(?:qa|e2e|cr|adv|ci) / [0-9a-f-]{36})\n\n", body):
        raise ValueError("旧runの履歴を裏付けるホスト記録がありません")
    for i, (start, text, _) in enumerate(entries):
        end = start + len(text)
        following = entries[i + 1][0] if i + 1 < len(entries) else len(body)
        if end > following or body[end:following].strip():
            raise ValueError("旧runに索引化できない履歴があります")
    return entries


def result_reference(folder, previous, phase, config):
    if "journal_reference" in previous:
        journal_read(folder, previous["journal_reference"])
        return previous["journal_reference"]
    # 移行済みの本文を旧形式で再解析しません。
    entry = config.get("legacy_result_references", {}).get(previous["round_id"])
    if not entry or entry["phase"] != phase:
        raise ValueError("前回結果のホスト記録を共通MDと照合できません")
    journal_read(folder, entry["reference"])
    return entry["reference"]


def review_context(round_dir, section, offset=0):
    context = json.loads((round_dir / "context.json").read_text())
    if section == "current":
        text = json.dumps(context["request"], ensure_ascii=False, indent=2)
    else:
        if section not in context["sections"]:
            raise ValueError("この回には指定したMD欄がありません")
        text = "\n\n".join(journal_read(round_dir.parent, ref) for ref in context["sections"][section])
    return {"section": section, "text": text[offset:offset + 12000],
            "next_offset": offset + 12000 if offset + 12000 < len(text) else None}


def safe_directory(path, project):
    path = path.absolute()
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("保存先のsymlinkは使用できません")
    path = path.resolve()
    if path.is_relative_to(project):
        relative = path.relative_to(project).as_posix()
        if not relative.startswith((".codex/", ".claude/")):
            raise ValueError("リポジトリ内の保存先は既存の除外済み設定フォルダーだけです")
        result = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", "--", relative + "/review.md"])
        if result.returncode != 0 or git(project, "ls-files", "--", relative):
            raise ValueError("保存先は除外されていません。gitignore/excludeを変更せず外部を指定してください")
    return path


def load_run(folder):
    folder = Path(folder).absolute()
    if folder.is_symlink() or any(p.is_symlink() for p in folder.parents):
        raise ValueError("runへのsymlinkは使用できません")
    if (folder / "run.json").is_symlink() or (folder / "review.md").is_symlink():
        raise ValueError("記録へのsymlinkは使用できません")
    config = json.loads((folder / "run.json").read_text())
    safe_directory(folder, Path(config["project"]))
    return folder, config


def journal_entry(title, body):
    return f"\n\n## {title}\n\n{body.rstrip()}\n"


def append(folder, title, body):
    """呼出し側がrunのlockを保持して追記します。"""
    target = folder / "review.md"
    before = journal_body(folder)
    entry = journal_entry(title, body)
    fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(fd, "a", encoding="utf-8") as stream:
        stream.write(entry)
    return journal_reference(before + entry, len(before), len(entry))


def capture(config, destination=None):
    project = Path(config["project"])
    head = git(project, "rev-parse", "HEAD").decode().strip()
    rows = []
    for name in config["paths"]:
        name = safe_path(name)
        source = project / name
        if any(p.is_symlink() for p in source.parents if p != project and p.is_relative_to(project)):
            raise ValueError(f"対象の親がsymlinkです: {name}")
        entries = git(project, "ls-files", "--stage", "-z", "--", name).split(b"\0")
        if any(entry and entry.split(b"\t", 1)[0].split()[-1] != b"0" for entry in entries):
            raise ValueError(f"競合中のindexです: {name}")
        for view, revision in (("base", config["base"]), ("head", head), ("index", None), ("worktree", None)):
            mode, data = None, None
            if view in ("base", "head"):
                entry = git(project, "ls-tree", "-z", revision, "--", name)
                if entry:
                    meta, actual = entry.rstrip(b"\0").split(b"\t", 1)
                    mode, kind, oid = meta.decode().split()
                    if kind != "blob" or actual.decode() != name:
                        raise ValueError("ファイル単位で対象を指定してください")
                    data = git(project, "cat-file", "blob", oid)
            elif view == "index" and entries[0]:
                meta, actual = entries[0].split(b"\t", 1)
                mode, oid, _stage = meta.decode().split()
                if actual.decode() != name or len([e for e in entries if e]) != 1 or mode == "160000":
                    raise ValueError("indexの対象をファイル単位で指定してください")
                data = git(project, "cat-file", "blob", oid)
            elif view == "worktree":
                if source.is_symlink():
                    mode, data = "120000", os.fsencode(os.readlink(source))
                elif source.exists():
                    if not source.is_file():
                        raise ValueError("対象は通常ファイルかsymlinkだけです")
                    mode = "100755" if source.stat().st_mode & stat.S_IXUSR else "100644"
                    data = source.read_bytes()
            rows.append([name, view, mode, digest(data) if data is not None else None])
            if destination is not None and data is not None:
                target = destination / view / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # symlinkも通常ファイル化し、リンク先の読取りを防ぎます。
                target.write_bytes(data)
                target.chmod(0o700 if mode == "100755" else 0o600)
    rules = [[p, digest(Path(p).read_bytes())] for p in config["rules"]]
    record = {"base": config["base"], "head": head, "paths": rows, "rules": rules, "exclusions": config.get("exclusions", {})}
    record["snapshot_id"] = digest(json.dumps(record, sort_keys=True).encode())
    return record


def frozen_diff(round_dir, view):
    pairs = {"branch": ("base", "head"), "staged": ("head", "index"), "unstaged": ("index", "worktree"), "delta": ("previous", "worktree")}
    if view not in pairs:
        raise ValueError("未対応のviewです")
    if view == "delta" and not (round_dir / "previous").is_dir():
        raise ValueError("前回の確認版がありません")
    left, right = pairs[view]
    # 元repoのconfig/attributes/hooks/filterを読み込まない場所で実行します。
    env = {"PATH": os.defpath, "GIT_DIR": str(round_dir / "absent-git-dir"),
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C.UTF-8"}
    result = subprocess.run(["git", "--no-pager", "-c", "core.attributesFile=/dev/null", "diff",
                             "--no-index", "--no-ext-diff", "--no-textconv", "--", left, right],
                            cwd=round_dir, env=env, capture_output=True, timeout=30)
    if result.returncode not in (0, 1):
        raise ValueError("固定snapshotのgit diffに失敗しました")
    return result.stdout.decode("utf-8", errors="replace")


def serve(round_dir):
    """自由なcommand/pathを書けない、小さなstdio MCPです。"""
    info = json.loads((round_dir / "snapshot.json").read_text())
    tool = {"name": "git_diff", "description": "固定snapshotのgit diffを取得します。全3viewとmode/状態を確認してください。",
            "inputSchema": {"type": "object", "properties": {"view": {"enum": ["branch", "staged", "unstaged", "delta"]},
                "offset": {"type": "integer", "minimum": 0}}, "required": ["view"], "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}}
    context_tool = {"name": "review_context", "description": "共通review.mdの必要欄だけを読みます。最初はcurrent、そのreading_planに従ってください。",
                    "inputSchema": {"type": "object", "properties": {
                        "section": {"enum": ["current", "summary", "updates", "previous_result", "previous_attempt"]},
                        "offset": {"type": "integer", "minimum": 0}}, "required": ["section"], "additionalProperties": False},
                    "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}}
    for line in sys.stdin:
        message = None
        try:
            message = json.loads(line)
            if "id" not in message:
                continue
            method, params = message.get("method"), message.get("params", {})
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                          "serverInfo": {"name": "md-review", "version": "1.0"}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": [tool, context_tool]}
            elif method == "tools/call":
                args = params.get("arguments", {})
                name = params.get("name")
                fields = {"view", "offset"} if name == "git_diff" else {"section", "offset"}
                if name not in ("git_diff", "review_context") or set(args) - fields:
                    raise ValueError("未許可の操作です")
                offset = args.get("offset", 0)
                if type(offset) is not int or offset < 0:
                    raise ValueError("offsetが不正です")
                if name == "review_context":
                    page = review_context(round_dir, args["section"], offset)
                    result = {"content": [{"type": "text", "text": json.dumps(page, ensure_ascii=False)}]}
                    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}, ensure_ascii=False), flush=True)
                    continue
                content = frozen_diff(round_dir, args["view"])
                mode_rows = info["paths"]
                comparison = round_dir / "comparison.json"
                if args["view"] == "delta" and comparison.exists():
                    changed = set(json.loads(comparison.read_text())["changed_paths"])
                    mode_rows = [row for row in mode_rows if row[0] in changed]
                page = {"snapshot_id": info["snapshot_id"], "view": args["view"], "text": content[offset:offset + 12000],
                        "next_offset": offset + 12000 if offset + 12000 < len(content) else None,
                        "path_modes_and_states": mode_rows if offset == 0 and args["view"] in ("branch", "delta") else "snapshot.json参照"}
                result = {"content": [{"type": "text", "text": json.dumps(page, ensure_ascii=False)}]}
            else:
                raise ValueError("未対応のmethodです")
            response = {"jsonrpc": "2.0", "id": message["id"], "result": result}
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
            response = {"jsonrpc": "2.0", "id": message.get("id") if isinstance(message, dict) else None,
                        "error": {"code": -32602, "message": str(exc)}}
        print(json.dumps(response, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", type=Path)
    parser.add_argument("--run-dir", type=Path)
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--note-file", type=Path, help="既存文書の取込専用です。通常はnote-stdinを使います")
    notes.add_argument("--note-stdin", action="store_true")
    parser.add_argument("--add-paths", nargs="+", default=[])
    parser.add_argument("--add-rules", nargs="+", type=Path, default=[])
    parser.add_argument("--exclude", nargs=2, action="append", default=[], metavar=("PATH", "REASON"))
    parser.add_argument("--project", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--direction", choices=("codex-claude-review", "claude-codex-review"))
    parser.add_argument("--layers", nargs="+", choices=("qa", "e2e", "cr", "adv"))
    parser.add_argument("--paths", nargs="+")
    parser.add_argument("--rules", nargs="+", type=Path)
    summaries = parser.add_mutually_exclusive_group()
    summaries.add_argument("--summary-file", type=Path, help="既存文書の取込専用です。通常はsummary-stdinを使います")
    summaries.add_argument("--summary-stdin", action="store_true")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    if args.serve:
        serve(args.serve.resolve(strict=True))
        return
    if args.run_dir:
        folder, config = load_run(args.run_dir)
        if any((args.project, args.base, args.direction, args.layers, args.paths, args.rules, args.summary_file, args.summary_stdin, args.out_dir)):
            parser.error("既存runには初期化用引数を使えません。add-paths/add-rulesを指定してください")
        if not (args.note_file or args.note_stdin):
            parser.error("実装側追記にはnote-stdinが必要です")
        note = (sys.stdin.read() if args.note_stdin else args.note_file.read_text()).strip()
        if not note:
            raise ValueError("追記が空です")
        lock = os.open(folder / ".lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(lock, "w") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            journal_index(folder, config)
            config["paths"] = sorted(set(config["paths"]) | set(map(safe_path, args.add_paths)))
            config["rules"] = sorted(set(config["rules"]) | {str(p.resolve(strict=True)) for p in args.add_rules})
            for path, reason in args.exclude:
                if not reason.strip():
                    raise ValueError("除外理由が必要です")
                config.setdefault("exclusions", {})[safe_path(path, allow_secret=True)] = reason
            scope = check_scope(config)
            info = capture(config)
            reference = append(folder, "Implementation update", json.dumps({"snapshot_id": info["snapshot_id"],
                   "added_paths": args.add_paths, "added_rules": list(map(str, args.add_rules))}, ensure_ascii=False) + "\n\n" + note)
            config["updates"].append(reference)
            atomic_text(folder / "run.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
            atomic_text(folder / "latest-fix.json", json.dumps({"reference": reference, "snapshot_id": info["snapshot_id"]}))
        print(folder / "review.md")
        return
    if args.note_file or args.note_stdin or args.add_paths or args.add_rules:
        parser.error("追記用引数にはrun-dirが必要です")
    if not all((args.project, args.base, args.direction, args.layers, args.rules, args.summary_file or args.summary_stdin)):
        parser.error("project/base/direction/layers/rules/summary-stdinが必要です")
    if os.environ.get("GIT_INDEX_FILE"):
        parser.error("別indexの伝播は未対応です。元の設定を変更せず保留してください")
    project = Path(git(args.project, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    base = git(project, "rev-parse", "--verify", args.base + "^{commit}").decode().strip()
    suggested = project / ".codex" / "review-runs" / str(uuid.uuid4())
    try:
        folder = safe_directory(args.out_dir or suggested, project)
    except ValueError:
        if args.out_dir:
            raise
        folder = safe_directory(Path.home() / ".codex" / "review-runs" / digest(str(project).encode())[:12] / str(uuid.uuid4()), project)
    config = {"project": str(project), "base": base, "direction": args.direction,
              "layers": list(dict.fromkeys(args.layers)), "paths": sorted(set(map(safe_path, args.paths or []))),
              "exclusions": {safe_path(path, allow_secret=True): reason for path, reason in args.exclude},
              "rules": [str(p.resolve(strict=True)) for p in args.rules]}
    if any(not reason.strip() for reason in config["exclusions"].values()):
        raise ValueError("除外理由が必要です")
    if not args.paths:
        config["paths"] = changed_paths(config)[0]
    scope = check_scope(config)
    summary = (sys.stdin.read() if args.summary_stdin else args.summary_file.read_text()).strip()
    if not summary:
        raise ValueError("実装担当のサマリーが空です")
    capture(config)  # 不正な対象では記録を作りません。
    folder.mkdir(parents=True, mode=0o700, exist_ok=False)
    private_write(folder / "run.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    private_write(folder / "review.md", "# Cross-model review\n\n" + json.dumps({**config, "scope_check": scope}, ensure_ascii=False, indent=2) +
                  "\n\n## Implementation summary\n\n" + summary + "\n")
    # 新規MDの範囲は生成した本文から確定します。見出しは解釈しません。
    body = journal_body(folder)
    config["summary_reference"] = journal_reference(body, 0, len(body))
    config["updates"] = []
    atomic_text(folder / "run.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    print(folder / "review.md")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
