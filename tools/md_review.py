#!/usr/bin/env python3
"""レビューMDと固定したGit読取用snapshotを管理します。"""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
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


def safe_path(value):
    path = Path(value)
    if path.is_absolute() or not path.parts or any(p in ("..", ".git") for p in path.parts):
        raise ValueError("対象はリポジトリ内の相対パスで指定してください")
    if any(p == ".env" or p.startswith(".env.") and p not in (".env.example", ".env.sample") for p in path.parts):
        raise ValueError("秘密を含む環境ファイルはレビューsnapshotへ保存できません")
    return path.as_posix()


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


def append(folder, title, body):
    """呼出し側がrunのlockを保持して追記します。"""
    target = folder / "review.md"
    fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    with os.fdopen(fd, "a", encoding="utf-8") as stream:
        stream.write(f"\n\n## {title}\n\n{body.rstrip()}\n")


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
    record = {"base": config["base"], "head": head, "paths": rows, "rules": rules}
    record["snapshot_id"] = digest(json.dumps(record, sort_keys=True).encode())
    return record


def frozen_diff(round_dir, view):
    pairs = {"branch": ("base", "head"), "staged": ("head", "index"), "unstaged": ("index", "worktree")}
    if view not in pairs:
        raise ValueError("未対応のviewです")
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
            "inputSchema": {"type": "object", "properties": {"view": {"enum": ["branch", "staged", "unstaged"]},
                "offset": {"type": "integer", "minimum": 0}}, "required": ["view"], "additionalProperties": False},
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
                result = {"tools": [tool]}
            elif method == "tools/call":
                args = params.get("arguments", {})
                if params.get("name") != "git_diff" or set(args) - {"view", "offset"}:
                    raise ValueError("未許可の操作です")
                offset = args.get("offset", 0)
                if type(offset) is not int or offset < 0:
                    raise ValueError("offsetが不正です")
                content = frozen_diff(round_dir, args["view"])
                page = {"snapshot_id": info["snapshot_id"], "view": args["view"], "text": content[offset:offset + 12000],
                        "next_offset": offset + 12000 if offset + 12000 < len(content) else None,
                        "path_modes_and_states": info["paths"] if offset == 0 else "snapshot.json参照"}
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
    parser.add_argument("--note-file", type=Path)
    parser.add_argument("--add-paths", nargs="+", default=[])
    parser.add_argument("--add-rules", nargs="+", type=Path, default=[])
    parser.add_argument("--project", type=Path)
    parser.add_argument("--base")
    parser.add_argument("--direction", choices=("codex-claude-review", "claude-codex-review"))
    parser.add_argument("--layers", nargs="+", choices=("qa", "e2e", "cr", "adv"))
    parser.add_argument("--paths", nargs="+")
    parser.add_argument("--rules", nargs="+", type=Path)
    parser.add_argument("--summary-file", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    if args.serve:
        serve(args.serve.resolve(strict=True))
        return
    if args.run_dir:
        folder, config = load_run(args.run_dir)
        if any((args.project, args.base, args.direction, args.layers, args.paths, args.rules, args.summary_file, args.out_dir)):
            parser.error("既存runには初期化用引数を使えません。add-paths/add-rulesを指定してください")
        if not args.note_file:
            parser.error("実装側追記にはnote-fileが必要です")
        note = args.note_file.read_text().strip()
        if not note:
            raise ValueError("追記が空です")
        lock = os.open(folder / ".lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(lock, "w") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            config["paths"] = sorted(set(config["paths"]) | set(map(safe_path, args.add_paths)))
            config["rules"] = sorted(set(config["rules"]) | {str(p.resolve(strict=True)) for p in args.add_rules})
            info = capture(config)
            temporary = folder / (str(uuid.uuid4()) + ".json")
            private_write(temporary, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
            os.replace(temporary, folder / "run.json")
            append(folder, "Implementation update", json.dumps({"snapshot_id": info["snapshot_id"],
                   "added_paths": args.add_paths, "added_rules": list(map(str, args.add_rules))}, ensure_ascii=False) + "\n\n" + note)
        print(folder / "review.md")
        return
    if not all((args.project, args.base, args.direction, args.layers, args.paths, args.rules, args.summary_file)):
        parser.error("project/base/direction/layers/paths/rules/summary-fileが必要です")
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
              "layers": list(dict.fromkeys(args.layers)), "paths": sorted(set(map(safe_path, args.paths))),
              "rules": [str(p.resolve(strict=True)) for p in args.rules]}
    summary = args.summary_file.read_text().strip()
    if not summary:
        raise ValueError("実装担当のサマリーが空です")
    capture(config)  # 不正な対象では記録を作りません。
    folder.mkdir(parents=True, mode=0o700, exist_ok=False)
    private_write(folder / "run.json", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    private_write(folder / "review.md", "# Cross-model review\n\n" + json.dumps(config, ensure_ascii=False, indent=2) +
                  "\n\n## Implementation summary\n\n" + summary + "\n")
    print(folder / "review.md")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
