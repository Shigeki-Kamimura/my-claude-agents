#!/usr/bin/env python3
"""共有原文からClaude/Codex用の事前読込スキルを生成・検証します。"""

import argparse
import hashlib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILES = (".claude", ".claude-company")
SOURCES = {
    "governance": "knowledge/engineering-governance.md",
    "human": "knowledge/human-review-patterns.md",
}
LENSES = "engineering-review-lenses"
PRINCIPLES = "engineering-principles"
REVIEW_EVIDENCE = "engineering-review-evidence"
UI_RULES = "engineering-ui-rules"
HUMAN_PRINCIPLES = (
    "Responsibility Separation", "Exception Handling", "Type Safety",
    "Refactoring Scope", "Design Document Alignment",
)
SECTIONS = {
    "engineering-review-core": {
        "governance": (
            "Core rules for Claude preload", "Claude role-scoped intake", "Pinned source and reconciliation",
            "User-directed execution permissions", "Shared evidence and reporting", "Conditional UI rule intake",
        ),
    },
    PRINCIPLES: {
        "governance": ("Review objective and evidence",),
        "human": HUMAN_PRINCIPLES,
    },
    REVIEW_EVIDENCE: {
        "governance": ("Review-layer approval and handoffs",),
    },
    UI_RULES: {
        "governance": ("Mandatory UI consistency and task usability",),
    },
    "engineering-react-rules": {
        "governance": ("ASYNC-1: Promise aggregation does not cancel work",
                       "HTTP-1: Distinguish authentication and forbidden access"),
        "human": ("Frontend Suspense Query Pattern", "API-to-UI Semantics",
                  "Reachable Failure Evidence", "Cross-Layer Regression Cases"),
    },
    "engineering-nest-rules": {
        "governance": ("ASYNC-1: Promise aggregation does not cancel work",
                       "HTTP-1: Distinguish authentication and forbidden access"),
        "human": ("API-to-UI Semantics", "Reachable Failure Evidence"),
    },
    # Claudeのレビュー4層だけに渡す。XREV-1(HND-1を含む)を読む選択に依存させないため
    LENSES: {"governance": ("XREV-1: Cross-model review calibration lenses",
                            "BIAS-1: Provenance and self-preference controls")},
}
CODEX_SECTIONS = {
    "engineering-review-core": {
        "governance": (
            "Pinned source and reconciliation", "Source coverage and role scope",
            "OPS-1: Release, operability and data-lifecycle boundaries",
            "XREV-1: Cross-model review calibration lenses",
            "BIAS-1: Provenance and self-preference controls",
            "User-directed execution permissions", "Review objective and evidence", "Mandatory UI consistency and task usability",
            "Independent review and reconciliation", "Evidence and reporting",
        ),
        "human": HUMAN_PRINCIPLES,
    },
    "engineering-react-rules": SECTIONS["engineering-react-rules"],
    "engineering-nest-rules": SECTIONS["engineering-nest-rules"],
}


def section(text: str, title: str) -> str:
    """指定した節を、次の見出しまで例外ごと取得します。"""
    headings = list(re.finditer(r"(?m)^(#{2,3}) (.+)$", text))
    matches = [i for i, match in enumerate(headings) if match[2] == title]
    if len(matches) != 1:
        raise ValueError(f"見出しが一意ではありません: {title}")
    index = matches[0]
    level = len(headings[index][1])
    following = [match for match in headings[index + 1:] if len(match[1]) <= level]
    end = following[0].start() if following else len(text)
    return text[headings[index].start():end].strip().removesuffix("---").rstrip()


DESCRIPTIONS = {
    "engineering-review-core": "Universal engineering principles, source intake, execution boundaries and evidence rules preloaded for every Claude role.",
    PRINCIPLES: "Human-review principles and evidence objectives for substantive Claude owners.",
    REVIEW_EVIDENCE: "Approval and handoff clauses for QA/E2E/CR/ADV and convergence reviewers.",
    UI_RULES: "Complete UI consistency and task-usability rules for user-facing changes.",
    "engineering-react-rules": "React consultation rules for async state, GET Suspense exceptions and API-to-render evidence; preloaded for react-ui-flow.",
    LENSES: "Cross-model review calibration lenses and handoff weights (XREV-1 incl. HND-1) and provenance/self-preference controls (BIAS-1); preloaded only for test-qa, e2e-qa, code-quality-reviewer and adviser.",
    "engineering-nest-rules": "NestJS consultation rules for async failures, authentication/authorization and API producer reachability; preloaded for nestjs-backend.",
}


def agent_files(root: Path, profile: str) -> list[Path]:
    """先頭frontmatterにnameを持つ定義だけを対象にします。"""
    found = []
    for path in sorted((root / profile / "agents").glob("*.md")):
        header = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
        if header and re.search(r"(?m)^name: \S+\s*$", header[1]):
            found.append(path)
    return found


def render(root: Path, name: str, platform: str = "claude") -> str:
    """出典と原文を両profileで同じ内容にします。"""
    if platform not in ("claude", "codex"):
        raise ValueError(f"未対応のplatformです: {platform}")
    description = DESCRIPTIONS[name]
    if platform == "codex" and name == "engineering-review-core":
        description = "Shared engineering principles, execution boundaries and evidence rules for Codex implementation/review roles."
    identity_tools = (
        "Never run Bash/git merely to validate these rules."
        if platform == "claude" else
        "Use source identity supplied by the coordinator or permitted read-only metadata tools once at intake; "
        "do not repeat hash checks for each read."
    )
    chunks = [f"---\nname: {name}\ndescription: {description}\n---\n",
              "<!-- Generated by tools/sync_engineering_preloads.py; edit the source documents. -->\n",
              f"# {name}\n\n"
              "Exact excerpts for your assigned role/workflow; no whole-document credit or added tools, "
              "execution, layers, delegation, approval authority or file scope.\n\n"
              "Retain actual injected sections, skill names, source SHA-256 and missing/changed rules once "
              "in `Rules loaded`. A declaration is not delivery. Compare current project-source identity "
              "supplied by the coordinator. " + identity_tools + "\n\n"
              "Missing, changed, uncertain or conflicting delivery/identity requires complete affected "
              "originals and exceptions through permitted tools, or an exact evidence request. Report setup "
              "gaps; dependent judgment stays pending. Project rules override only explicit fields.\n\n"
              "Complete delivered sections satisfy first-entry reading. Reuse only complete, retained, "
              "verified unchanged sections on same-owner continuation. Omitted applicable originals/design "
              "rules and exceptions remain unread and required; preserve source-index, workflow/phase, "
              "consultation, closure and retained-blocker duties.\n"]
    if name in (PRINCIPLES, REVIEW_EVIDENCE, UI_RULES):
        # 共通coreを重ねて配らず、この抜粋自体の出典・不足時の扱いを残します。
        chunks[-1] = (
            f"# {name}\n\n"
            "Exact excerpts: follow the verified `engineering-review-core` delivery contract and "
            "retain these sections/SHA-256 in the same `Rules loaded` record. If that contract is "
            "missing or unverified, read the complete `Preloaded rule delivery` section in the "
            "current project-local governance source below with permitted tools; dependent judgment "
            "stays pending. This excerpt adds no permission, scope or approval authority.\n"
        )
    sections = CODEX_SECTIONS if platform == "codex" else SECTIONS
    for source, titles in sections[name].items():
        relative = SOURCES[source]
        data = (root / ".claude" / relative).read_bytes()
        for profile in PROFILES:
            if (root / profile / relative).read_bytes() != data:
                raise ValueError(f"共有原文が不一致です: {relative}")
        digest = hashlib.sha256(data).hexdigest()
        chunks.append(f"\nSource: `.claude/{relative}` (company: `.claude-company/{relative}`)\n"
                      f"SHA-256: `{digest}`\nIncluded sections: {', '.join(titles)}\n\n")
        for title in titles:
            chunks.append(section(data.decode("utf-8"), title) + "\n\n")
    return "\n".join(chunks).rstrip() + "\n"


def sync(root: Path, write: bool = False) -> list[str]:
    """既定では差分を検出し、明示指定時だけ生成します。"""
    outputs = {root / profile / "skills" / name / "SKILL.md": render(root, name)
               for name in SECTIONS for profile in PROFILES}
    outputs.update({root / ".agents" / "skills" / name / "SKILL.md": render(root, name, "codex")
                    for name in CODEX_SECTIONS})
    if write:
        for path in outputs:
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"生成先がroot外を参照しています: {path}")
    stale = []
    for path, expected in outputs.items():
        if path.is_file() and path.read_text(encoding="utf-8") == expected:
            continue
        stale.append(str(path.relative_to(root)))
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="検証・生成する設定コピーのルートです。省略時はこのリポジトリです")
    parser.add_argument("--write", action="store_true", help="生成物を更新します")
    args = parser.parse_args()
    try:
        stale = sync(args.root.resolve(), args.write)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if stale:
        print(("UPDATED: " if args.write else "STALE: ") + ", ".join(stale))
    else:
        print("OK: Claude/Codex事前読込スキルと両profileの原文が一致しています")
    return int(bool(stale) and not args.write)


if __name__ == "__main__":
    raise SystemExit(main())
