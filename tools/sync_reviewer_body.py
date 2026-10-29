#!/usr/bin/env python3
"""reviewerエージェントの共通本文を3ファイル間で検証・同期します。

対象:
  .claude/agents/reviewer.md          基準(正本)
  .claude-company/agents/reviewer.md  基準とバイト単位で同一
  .codex/agents/reviewer.toml         共通本文のみ一致、ツール固有ブロックは別

ツール固有の部分は次のマーカーで囲みます。マーカーは本文の一部として残ります。
  <!-- tool-specific:begin -->
  <!-- tool-specific:end -->
beginとendは交互に現れる必要があり、1組以上が必要です。
ヘッダー(md の frontmatter、toml のキー定義)は本文の外にあるため、比較しません。

使い方:
  python3 tools/sync_reviewer_body.py             検証のみ。不一致なら終了コード1
  python3 tools/sync_reviewer_body.py --dry-run   書き込み対象と変更行数を表示(書き込まない)
  python3 tools/sync_reviewer_body.py --write     基準から他の2ファイルへ共通本文を同期
"""

import argparse
import difflib
import os
import re
import stat
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / ".claude/agents/reviewer.md"
MIRROR = ROOT / ".claude-company/agents/reviewer.md"
CODEX = ROOT / ".codex/agents/reviewer.toml"

BEGIN = "<!-- tool-specific:begin -->\n"
END = "<!-- tool-specific:end -->\n"
MARKER = re.compile(r"<!-- tool-specific:(begin|end) -->\n")
TOML_OPEN = 'developer_instructions = """\n'
TOML_CLOSE = '"""'
PLACEHOLDER = "<TOOL_BLOCK>\n"


class SyncError(Exception):
    """検証または同期の失敗を表します。"""


def read_bytes(path: Path) -> bytes:
    """読めない場合は、どのファイルかを示す SyncError にします。"""
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SyncError(f"読めません: {path.relative_to(ROOT)}: {exc}") from exc


def read_text(path: Path) -> str:
    """改行を変換せずに読みます。"""
    try:
        return read_bytes(path).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SyncError(f"UTF-8として読めません: {path.relative_to(ROOT)}: {exc}") from exc


def split_md(text: str):
    """frontmatterと本文に分けます。"""
    match = re.match(r"(---\n.*?\n---\n\n?)(.*)\Z", text, re.DOTALL)
    if not match:
        raise SyncError("frontmatterが見つかりません")
    return match.group(1), match.group(2)


def split_toml(text: str):
    """ヘッダー、本文、末尾に分けます。"""
    if TOML_OPEN not in text or TOML_CLOSE not in text:
        raise SyncError("tomlのdeveloper_instructionsが見つかりません")
    start = text.index(TOML_OPEN) + len(TOML_OPEN)
    end = text.rindex(TOML_CLOSE)
    if end < start:
        raise SyncError("tomlのdeveloper_instructionsの範囲が不正です")
    return text[:start], text[start:end], text[end:]


def common_and_blocks(body: str, label: str):
    """本文を共通部分とツール固有ブロックに分けます。

    begin/endを別々に数え、交互であることと1組以上あることを要求します。
    """
    markers = [m.group(1) for m in MARKER.finditer(body)]
    begins, ends = markers.count("begin"), markers.count("end")
    if begins != ends:
        raise SyncError(f"{label}: マーカー数が不一致です(begin {begins}, end {ends})")
    if begins == 0:
        raise SyncError(f"{label}: ツール固有ブロックが1件もありません")
    if markers != ["begin", "end"] * begins:
        raise SyncError(f"{label}: begin/endの順序が不正です(重複・入れ子・逆順)")
    blocks = []
    common = []
    pos = 0
    for begin in MARKER.finditer(body):
        if begin.group(1) != "begin":
            continue
        end = MARKER.search(body, begin.end())
        common.append(body[pos : begin.start()])
        blocks.append(body[begin.start() : end.end()])
        pos = end.end()
    common.append(body[pos:])
    return PLACEHOLDER.join(common), blocks


def eol_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def normalized(text: str) -> str:
    return text.replace("\r\n", "\n")


def analyze():
    """3ファイルを読み、検証結果と同期後の内容を返します(書き込まない)。"""
    canon_text = read_text(CANONICAL)
    _, canon_body = split_md(canon_text)
    toml_text = read_text(CODEX)
    toml_head, toml_body, toml_tail = split_toml(toml_text)
    canon_common, canon_blocks = common_and_blocks(normalized(canon_body), "reviewer.md")
    toml_common, toml_blocks = common_and_blocks(normalized(toml_body), "reviewer.toml")
    if len(canon_blocks) != len(toml_blocks):
        raise SyncError(
            f"ツール固有ブロック数が不一致です(基準 {len(canon_blocks)}, toml {len(toml_blocks)})"
        )
    return {
        "canon_text": canon_text,
        "toml_text": toml_text,
        "toml_head": toml_head,
        "toml_tail": toml_tail,
        "canon_common": canon_common,
        "toml_common": toml_common,
        "canon_blocks": canon_blocks,
        "toml_blocks": toml_blocks,
    }


def build_synced(info) -> str:
    """基準の共通本文とtomlのツール固有ブロックからtoml全文を作ります。"""
    blocks = iter(info["toml_blocks"])
    body = info["canon_common"].replace(PLACEHOLDER, "\0")
    body = re.sub("\0", lambda _: next(blocks), body)
    # TOMLの複数行基本文字列では、バックスラッシュと三連引用符が解釈されます
    if "\\" in body or '"""' in body:
        raise SyncError("本文にバックスラッシュまたは三連引用符があるため、tomlへ書けません")
    eol = eol_of(info["toml_text"])
    if eol != "\n":
        body = body.replace("\n", eol)
    new_text = info["toml_head"] + body + info["toml_tail"]
    try:
        parsed = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError as exc:
        raise SyncError(f"同期後のtomlが解析できません: {exc}") from exc
    if parsed.get("name") != "reviewer":
        raise SyncError("同期後のtomlのnameがreviewerではありません")
    return new_text


def check() -> int:
    problems = []
    try:
        if read_bytes(MIRROR) != read_bytes(CANONICAL):
            problems.append(f"{MIRROR.relative_to(ROOT)} が基準とバイト単位で一致しません")
    except SyncError as exc:
        problems.append(str(exc))
    try:
        info = analyze()
    except SyncError as exc:
        problems.append(str(exc))
        info = None
    if info and info["canon_common"] != info["toml_common"]:
        diff = difflib.unified_diff(
            info["canon_common"].splitlines(),
            info["toml_common"].splitlines(),
            "reviewer.md(共通本文)",
            "reviewer.toml(共通本文)",
            lineterm="",
        )
        problems.append("共通本文が不一致です:\n" + "\n".join(diff))
    if problems:
        print("\n".join(problems))
        return 1
    same = info["canon_blocks"] == info["toml_blocks"]
    print(
        f"OK: 共通本文は一致。ツール固有ブロック {len(info['canon_blocks'])} 件のみ別内容"
        f"({'同一' if same else '差分あり、想定どおり'})"
    )
    return 0


def plan():
    """書き込み計画を作ります。(path, 元のバイト列, 新しいバイト列)の一覧を返します。"""
    info = analyze()
    new_toml = build_synced(info).encode("utf-8")
    targets = [
        (MIRROR, read_bytes(MIRROR), read_bytes(CANONICAL)),
        (CODEX, read_bytes(CODEX), new_toml),
    ]
    return targets


def changed_lines(old: bytes, new: bytes) -> int:
    old_lines = old.decode("utf-8").splitlines()
    new_lines = new.decode("utf-8").splitlines()
    return sum(
        1
        for line in difflib.ndiff(old_lines, new_lines)
        if line.startswith(("+ ", "- "))
    )


def dry_run() -> int:
    try:
        targets = plan()
    except SyncError as exc:
        print(exc)
        return 1
    for path, old, new in targets:
        status = "変更なし" if old == new else f"変更あり({changed_lines(old, new)}行)"
        print(f"{path.relative_to(ROOT)}: {status}")
    print("dry-run: 書き込みは行っていません")
    return 0


def atomic_write(path: Path, data: bytes) -> None:
    """同一ディレクトリの一時ファイル経由で置き換えます。権限は元ファイルを保ちます。"""
    # mkstempは0600で作るため、置き換え先の権限(新規なら0644)を明示的に適用します
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write() -> int:
    # すべて検証してから書き込みます。ここまでに失敗した場合、何も変更しません
    try:
        targets = plan()
    except SyncError as exc:
        print(exc)
        return 1
    done = []
    try:
        for path, old, new in targets:
            if old != new:
                atomic_write(path, new)
                done.append((path, old))
        parsed = tomllib.loads(read_text(CODEX))
        if parsed.get("name") != "reviewer":
            raise SyncError("書き込み後のtomlのnameがreviewerではありません")
    except (OSError, SyncError, tomllib.TOMLDecodeError) as exc:
        print(f"書き込みに失敗したため元の内容に復元します: {exc}")
        not_restored = []
        for path, old in reversed(done):
            try:
                atomic_write(path, old)
            except OSError as restore_exc:
                not_restored.append(f"{path.relative_to(ROOT)}({restore_exc})")
        if not_restored:
            print("復元に失敗しました。元に戻っていないファイル: " + ", ".join(not_restored))
        return 1
    for path, old in done:
        print(f"更新: {path.relative_to(ROOT)}")
    return check()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="基準から同期する")
    group.add_argument("--dry-run", action="store_true", help="書き込み対象と変更行数を表示する")
    args = parser.parse_args()
    if args.write:
        return write()
    if args.dry_run:
        return dry_run()
    return check()


if __name__ == "__main__":
    sys.exit(main())
