#!/usr/bin/env python3
"""Build one read-only review context packet (Markdown on stdout) for a reviewer agent.

Never writes files, never checks out, never uses a shell.
"""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

CONTEXT = 30
REQ_DOC_MAX_LINES = 800
MAX_SYMBOLS = 40
MANIFEST_RESERVE = 3000
KEYWORDS = {
    "if", "for", "while", "switch", "catch", "function", "return", "else", "new", "try", "do", "with", "super",
    "this", "constructor", "require", "import", "export", "print", "len", "str", "int", "get", "set", "main",
    "init", "self", "def", "class", "async", "await", "from", "assert", "raise", "yield", "lambda", "elif",
}
SYMBOL_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+(\w+)"),
    re.compile(r"^\s*class\s+(\w+)"),
    re.compile(r"\bfunction\s*\*?\s*(\w+)\s*[(<]"),
    re.compile(r"\b(?:class|interface|enum|type)\s+(\w+)"),
    re.compile(r"\b(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\(|function\b|\w+\s*=>)"),
    re.compile(r"^\s*(?:(?:public|private|protected|static|async|readonly|abstract|override|get|set)\s+)*(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?::\s*[^={;]+)?\{\s*$"),
    re.compile(r"^\s*(?:(?:public|private|protected|static|final|abstract|synchronized|default)\s+)+[\w<>\[\],.? ]+?\s+(\w+)\s*\([^;]*$"),
]


class PacketError(Exception):
    pass


def git(repo, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "--no-pager", "--literal-pathspecs", "-c", "core.fsmonitor=false", "-c", "core.quotepath=false",
         "-C", str(repo), *args],
        env=env, capture_output=True, timeout=60)
    if check and result.returncode != 0:
        raise PacketError("git %s failed: %s" % (args[0], result.stderr.decode("utf-8", "replace").strip()))
    return result


def text(data):
    return data.decode("utf-8", "replace")


def resolve(repo, rev, label):
    if not rev or rev.startswith("-"):
        raise PacketError("invalid %s ref %r (must not be empty or start with '-')" % (label, rev))
    result = git(repo, "rev-parse", "--verify", "--quiet", "--end-of-options", rev + "^{commit}", check=False)
    if result.returncode != 0:
        raise PacketError("cannot resolve %s ref %r to a commit" % (label, rev))
    return text(result.stdout).strip()


def numbered(lines, start=1):
    return "\n".join("%5d| %s" % (start + i, line) for i, line in enumerate(lines))


def parse_name_status(data):
    parts = data.decode("utf-8", "replace").split("\0")
    entries, i = [], 0
    while i < len(parts) and parts[i]:
        status = parts[i]
        if status[0] in "RC":
            entries.append((status, parts[i + 1], parts[i + 2]))
            i += 3
        else:
            entries.append((status, parts[i + 1], parts[i + 1]))
            i += 2
    return entries


def parse_diff(patch):
    """Return {new_path: info} where info has binary, deleted, ranges (new-side), symbols source lines."""
    files = {}
    for block in re.split(r"(?m)^diff --git ", patch)[1:]:
        lines = block.split("\n")
        rename = next((l[len("rename to "):] for l in lines if l.startswith("rename to ")), None)
        plus = next((l[6:] for l in lines if l.startswith("+++ b/")), None)
        minus = next((l[6:] for l in lines if l.startswith("--- a/")), None)
        deleted = any(l.startswith("deleted file mode") for l in lines)
        path = rename or plus or minus
        if path is None:
            m = re.match(r"a/(.+) b/(.+)", lines[0])
            path = m.group(2) if m else lines[0]
        info = {"binary": any(l.startswith("Binary files") or l.startswith("GIT binary patch") for l in lines),
                "deleted": deleted, "ranges": [], "src": []}
        for l in lines:
            h = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@ ?(.*)", l)
            if h:
                start, count = int(h.group(1)), int(h.group(2) if h.group(2) is not None else 1)
                info["ranges"].append((start, start + max(count, 1) - 1))
                info["src"].append(h.group(3))
            elif (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---")):
                info["src"].append(l[1:])
        files[path] = info
    return files


def extract_symbols(files):
    symbols = {}
    for path, info in files.items():
        for line in info["src"]:
            for pattern in SYMBOL_PATTERNS:
                m = pattern.search(line)
                if m:
                    name = m.group(1)
                    if len(name) >= 3 and name not in KEYWORDS:
                        symbols.setdefault(name, set()).add(path)
                    break
    return symbols


def merge_ranges(ranges, total):
    spans = sorted((max(1, a - CONTEXT), min(total, b + CONTEXT)) for a, b in ranges)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def read_req(repo, spec):
    if os.path.isfile(spec):
        return spec, Path(spec).read_bytes()
    candidate = Path(repo) / spec
    if candidate.is_file():
        return spec, candidate.read_bytes()
    if ":" in spec:
        rev, path = spec.split(":", 1)
        sha = resolve(repo, rev, "--req")
        result = git(repo, "cat-file", "blob", sha + ":" + path, check=False)
        if result.returncode == 0:
            return spec, result.stdout
        raise PacketError("--req %r: path not found at %s" % (spec, rev))
    raise PacketError("--req %r not found as a file or REV:path" % spec)


def build(args):
    repo = Path(args.repo)
    if not repo.is_dir():
        raise PacketError("--repo %r is not a directory" % args.repo)
    top = text(git(repo, "rev-parse", "--show-toplevel").stdout).strip()
    base = resolve(repo, args.base, "base")
    head = resolve(repo, args.head, "head")
    mb_run = git(repo, "merge-base", base, head, check=False)
    if mb_run.returncode != 0:
        raise PacketError("no merge-base between %s and %s" % (args.base, args.head))
    mb = text(mb_run.stdout).strip()

    truncs, included = [], []
    sections = []  # [title, body, truncatable_rank or None]

    sections.append(["1. Identity (what was resolved: actual SHAs, never assumed refs)", "\n".join([
        "- repo: %s" % top,
        "- base: %s (given as `%s`)" % (base, args.base),
        "- head: %s (given as `%s`)" % (head, args.head),
        "- merge-base: %s" % mb,
        "- worktree: %s" % ("yes (uncommitted changes in a separate section)" if args.worktree else "no"),
        "- generated-by: tools/review_packet.py (read-only; no checkout, no writes)",
    ]), None])

    diff_flags = ["--no-color", "--no-ext-diff", "--no-textconv", "-M"]
    stat = text(git(repo, "diff", *diff_flags, "--stat=120", mb, head, "--").stdout).rstrip()
    entries = parse_name_status(git(repo, "diff", *diff_flags, "--name-status", "-z", mb, head, "--").stdout)
    ns = []
    for status, old, new in entries:
        ns.append("%s\t%s" % (status, old if old == new else "%s -> %s" % (old, new)))
    sections.append(["2. Diffstat and name-status (R = rename, D = delete; renames show old -> new)",
                     "```\n%s\n```\n\n```\n%s\n```" % (stat or "(no changes)", "\n".join(ns) or "(none)"), None])

    patch = text(git(repo, "diff", *diff_flags, "-U3", mb, head, "--").stdout)
    note = ""
    if mb != base:
        note = "NOTE: base %s != merge-base %s; diff is merge-base...head (equivalent to `git diff base...head`).\n\n" % (base[:12], mb[:12])
    sections.append(["3. Full unified diff (-U3, merge-base vs head)", note + "```diff\n%s\n```" % patch.rstrip("\n"), None])
    files = parse_diff(patch)

    # 4. Changed files at head
    parts, partial = [], []
    for status, old, new in entries:
        info = files.get(new, {"binary": False, "deleted": status.startswith("D"), "ranges": []})
        if status.startswith("D"):
            parts.append("### %s (deleted at head)\nbase version: %s:%s (not printed)" % (new, base[:12], new))
            continue
        if info["binary"]:
            parts.append("### %s\nbinary file skipped" % new)
            continue
        blob = git(repo, "cat-file", "blob", head + ":" + new, check=False)
        if blob.returncode != 0:
            parts.append("### %s\n(not readable at head)" % new)
            continue
        if b"\0" in blob.stdout[:8000]:
            parts.append("### %s\nbinary file skipped" % new)
            continue
        lines = text(blob.stdout).split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        label = new if old == new else "%s (renamed from %s)" % (new, old)
        if len(lines) <= args.max_file_lines or not info["ranges"]:
            if len(lines) > args.max_file_lines:
                lines_shown = lines[:args.max_file_lines]
                omitted = len("\n".join(lines[args.max_file_lines:]))
                truncs.append("TRUNCATED: file %s beyond line %d (no hunks to select), %d chars omitted" % (new, args.max_file_lines, omitted))
                parts.append("### %s (%d lines)\nPARTIAL: lines 1-%d\n```\n%s\n```" % (label, len(lines), args.max_file_lines, numbered(lines_shown)))
            else:
                parts.append("### %s (%d lines, whole file)\n```\n%s\n```" % (label, len(lines), numbered(lines)))
            continue
        shown = []
        for a, b in merge_ranges(info["ranges"], len(lines)):
            shown.append("PARTIAL: lines %d-%d\n```\n%s\n```" % (a, b, numbered(lines[a - 1:b], a)))
        partial.append(new)
        parts.append("### %s (%d lines, changed hunks +-%d lines only)\n%s" % (label, len(lines), CONTEXT, "\n".join(shown)))
    sections.append(["4. Changed files at head (line numbered; large files show only changed hunks)",
                     "\n\n".join(parts) or "(none)", 2])

    # 5. Symbol references
    symbols = extract_symbols(files)
    names = list(symbols)[:MAX_SYMBOLS]
    if len(symbols) > MAX_SYMBOLS:
        truncs.append("TRUNCATED: symbol list capped at %d of %d, %d symbols omitted" % (MAX_SYMBOLS, len(symbols), len(symbols) - MAX_SYMBOLS))
    ref_parts = []
    prefix = head + ":"
    for name in names:
        result = git(repo, "grep", "-n", "-w", "-F", "-I", "-e", name, head, "--", check=False)
        seen, hits, extra = set(), [], 0
        for line in text(result.stdout).split("\n"):
            if not line.startswith(prefix):
                continue
            rest = line[len(prefix):]
            path = rest.split(":", 1)[0]
            if path in symbols[name] or rest in seen:
                continue
            seen.add(rest)
            if len(hits) < args.max_refs:
                hits.append(rest[:200])
            else:
                extra += 1
        if hits:
            more = "\n  ... %d more references omitted (--max-refs %d)" % (extra, args.max_refs) if extra else ""
            ref_parts.append("`%s` (defined/changed in %s)\n%s%s" % (name, ", ".join(sorted(symbols[name])), "\n".join("  " + h for h in hits), more))
            if extra:
                truncs.append("TRUNCATED: references for `%s` capped at %d, %d lines omitted" % (name, args.max_refs, extra))
    sections.append(["5. Changed-symbol references (heuristic: `git grep -n -w` in head tree, excluding the defining file; approximates callers/callees)",
                     "\n\n".join(ref_parts) or "(no references found)", 1])

    # worktree section
    if args.worktree:
        wd = text(git(repo, "diff", *diff_flags, "-U3", head, "--").stdout).rstrip("\n")
        wparts = ["Tracked changes (staged + unstaged) relative to head %s:\n```diff\n%s\n```" % (head[:12], wd or "(none)")]
        untracked = [p for p in git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout.decode("utf-8", "replace").split("\0") if p]
        for p in untracked:
            full = Path(top) / p
            name = Path(p).name
            if full.is_symlink() or not full.is_file():
                wparts.append("### untracked %s\nskipped (not a regular file)" % p)
            elif name == ".env" or name.startswith(".env."):
                wparts.append("### untracked %s\nskipped (environment/secret file)" % p)
            else:
                data = full.read_bytes()
                if b"\0" in data[:8000]:
                    wparts.append("### untracked %s\nbinary file skipped" % p)
                    continue
                lines = text(data).split("\n")
                if lines and lines[-1] == "":
                    lines.pop()
                shown = lines[:args.max_file_lines]
                tail = ""
                if len(lines) > len(shown):
                    omitted = len("\n".join(lines[len(shown):]))
                    truncs.append("TRUNCATED: untracked file %s beyond line %d, %d chars omitted" % (p, len(shown), omitted))
                    tail = "\nPARTIAL: lines 1-%d of %d" % (len(shown), len(lines))
                wparts.append("### untracked %s (%d lines)\n```\n%s\n```%s" % (p, len(lines), numbered(shown), tail))
        sections.append(["W. Working-tree changes (UNCOMMITTED; head = working tree for this section only)", "\n\n".join(wparts), 3])

    # 6. Requirements
    rparts = []
    for spec in args.req or []:
        name, data = read_req(repo, spec)
        lines = text(data).split("\n")
        shown = lines[:REQ_DOC_MAX_LINES]
        if len(lines) > len(shown):
            truncs.append("TRUNCATED: requirement doc %s beyond line %d, %d chars omitted" % (name, len(shown), len("\n".join(lines[len(shown):]))))
        rparts.append("### %s (%d lines)\n```\n%s\n```" % (name, len(lines), numbered(shown)))
    sections.append(["6. Requirement documents", "\n\n".join(rparts) or "(none given)", None])
    return sections, truncs, {"base": base, "head": head, "mb": mb}


def render(sections, truncs, max_chars):
    def body_of(secs):
        return "\n\n".join("## %s\n\n%s" % (t, b) for t, b, _ in secs)

    def manifest(secs, tr, total, over):
        lines = ["## 7. Packet manifest (everything included; every truncation listed)", ""]
        lines += ["- included: %s (%d chars)" % (t.split(" (")[0], len(b)) for t, b, _ in secs]
        lines += ["- %s" % t for t in tr] or ["- no truncation"]
        if over:
            lines.append("- !!! OVER BUDGET: %s !!!" % over)
        lines.append("- total chars: %8d (limit %d)" % (total, max_chars))
        lines.append("- estimated tokens: ~%d (chars/3.5)" % round(total / 3.5))
        return "\n".join(lines)

    secs = [list(s) for s in sections]
    tr = list(truncs)
    over = ""
    budget = max_chars - MANIFEST_RESERVE - len(tr) * 150
    excess = len(body_of(secs)) - budget
    for rank in (1, 2, 3):
        if excess <= 0:
            break
        for s in secs:
            if s[2] == rank and excess > 0:
                cut = min(len(s[1]), excess + 200)
                keep = max(0, len(s[1]) - cut)
                note = "\n[TRUNCATED: section tail removed to fit --max-chars]"
                tr.append("TRUNCATED: section '%s' tail (budget), %d chars omitted" % (s[0].split(" (")[0], len(s[1]) - keep))
                s[1] = s[1][:keep] + note
                excess = len(body_of(secs)) - budget
    if excess > 0:
        over = "packet exceeds --max-chars by ~%d chars; diff/requirements/identity are never truncated" % excess
    out = body_of(secs)
    m = manifest(secs, tr, 0, over)
    total = len(out) + 2 + len(m)
    m = manifest(secs, tr, total, over)
    if tr and any("(budget)" in t for t in tr):
        m = "!!! PACKET TRUNCATED TO FIT --max-chars; parts are missing, see list below !!!\n\n" + m
    return "# Review context packet\n\n" + out + "\n\n" + m + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description="Build a read-only review context packet (Markdown on stdout).")
    p.add_argument("--repo", required=True)
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--worktree", action="store_true")
    p.add_argument("--req", action="append", default=[], help="requirement file path or REV:path (repeatable)")
    p.add_argument("--max-file-lines", type=int, default=400)
    p.add_argument("--max-refs", type=int, default=8)
    p.add_argument("--max-chars", type=int, default=120000)
    args = p.parse_args(argv)
    try:
        sections, truncs, _ = build(args)
        sys.stdout.write(render(sections, truncs, args.max_chars))
    except (PacketError, subprocess.TimeoutExpired, OSError) as error:
        sys.stderr.write("error: %s\n" % error)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
