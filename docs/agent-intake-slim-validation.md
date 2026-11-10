# Agent intake trial: source preservation and static size

## Scope and status

- Baseline: `exp/xml-agents` at `1bf4624cd4a5ed45262f98edcd53cc488bf1667b` (tree `1f618ab850688958e69f6bfd4c02d77e3f405b06`).
- Candidate: the role preloads and four workflow documents in this change. This is a draft trial, not a measured runtime optimization.
- Fixes: resolve actual applicable E2E project rules; recognize lenses and the new exact-source skills as eligible preload delivery; separate universal, principle, review-layer and UI excerpts; translate operational prose into English.
- Runtime usage: **NOT_MEASURED**. Actual Claude startup delivery, model quality, wall time and allowance consumption were not tested. Claude Code is unavailable in the execution environment.
- The target user's Codex client/configuration and the suspected 32,768-byte truncation remain unverified. This change does not alter `.codex/config.toml` or `.codex/AGENTS.md`.

## Measurement method

UTF-8 byte counts and reference token counts with `tiktoken 0.14.0`, encoding `o200k_base`. Each row sums the complete agent-definition file and each skill listed in its frontmatter. Tokenize each file separately, then sum. Counts include file headers/metadata. They exclude CLAUDE.md hierarchy, task/tool prompts, additional source reads, output, cache behavior and protocol overhead. They are not Claude token counts, billed tokens or five-hour usage percentages.

## Claude initial file totals

| Role | Before bytes | After bytes | Before reference tokens | After reference tokens | Token change |
| --- | ---: | ---: | ---: | ---: | ---: |
| `adviser` | 78,179 B | 72,258 B | 15,842 | 14,829 | -6.39% |
| `code-quality-reviewer` | 74,393 B | 68,472 B | 15,261 | 14,248 | -6.64% |
| `data-platform` | 38,646 B | 30,532 B | 7,540 | 6,010 | -20.29% |
| `e2e-qa` | 76,810 B | 71,056 B | 16,227 | 15,233 | -6.13% |
| `hq-coder` | 48,281 B | 40,167 B | 9,208 | 7,678 | -16.62% |
| `nestjs-backend` | 45,149 B | 36,680 B | 8,793 | 7,210 | -18.00% |
| `opus-escalation` | 36,510 B | 28,396 B | 7,050 | 5,520 | -21.70% |
| `react-ui-flow` | 48,533 B | 48,737 B | 9,447 | 9,548 | +1.07% |
| `req-pl` | 48,277 B | 40,163 B | 9,379 | 7,849 | -16.31% |
| `review-planner` | 41,977 B | 27,483 B | 8,389 | 5,606 | -33.17% |
| `reviewer` | 45,468 B | 39,902 B | 8,823 | 7,863 | -10.88% |
| `sec-arch` | 41,907 B | 33,793 B | 8,067 | 6,537 | -18.97% |
| `spring-boot` | 35,224 B | 27,110 B | 6,767 | 5,237 | -22.61% |
| `test-qa` | 73,351 B | 67,430 B | 14,990 | 13,977 | -6.76% |
| `ux-qa` | 50,830 B | 51,389 B | 10,111 | 10,265 | +1.52% |
| `vue-frontend` | 35,816 B | 36,375 B | 6,899 | 7,053 | +2.23% |

The universal core alone changes from 31,426 B / 6,017 reference tokens to 16,932 B / 3,234 reference tokens. Other required skill text still belongs in each role's total.

## Conditional UI reads and increases

The React, Vue and UX roles already require the complete UI section, so splitting metadata produces small increases. These rows are retained above; no blanket reduction is claimed.

For affected user-facing changes, other substantive owners must read the complete original UI section if it is not already verified in their context: 7,737 B / 1,465 reference tokens. This includes visible text/style/layout and API/error/state changes affecting the experience. A routing-only planner passes source references without reviewing code. Other existing source, consultation and permission duties still apply.

The following adds that one missing original excerpt to the new static total. It is an illustrative source-text comparison, not an actual run; tool wrappers and any other reads are excluded.

| Role for an affected UI task | Before static tokens | After + UI excerpt | Difference |
| --- | ---: | ---: | ---: |
| `adviser` | 15,842 | 16,294 | +452 (+2.85%) |
| `code-quality-reviewer` | 15,261 | 15,713 | +452 (+2.96%) |
| `e2e-qa` | 16,227 | 16,698 | +471 (+2.90%) |
| `hq-coder` | 9,208 | 9,143 | -65 (-0.71%) |
| `nestjs-backend` | 8,793 | 8,675 | -118 (-1.34%) |
| `test-qa` | 14,990 | 15,442 | +452 (+3.02%) |

For UI review work, this trial can increase total source text. Keep the split as an opt-in draft candidate until matched real traces establish its value. Smaller startup context is not proof of lower total usage.

## English workflow documents

All existing Markdown headings, machine identifiers, command examples, Japanese invocation templates and required Japanese user-facing results remain. Explanatory values changed; YAML keys/order, non-string values, fixed prompts and the eleven result keys did not.

| File | Before bytes | After bytes | Before reference tokens | After reference tokens | Token change |
| --- | ---: | ---: | ---: | ---: |
| `claude-review.yml` | 16,325 B | 14,776 B | 4,391 | 3,115 | -29.06% |
| `codex-review.yml` | 13,921 B | 12,692 B | 3,740 | 2,675 | -28.48% |
| `critical-review-request.md` | 8,783 B | 6,766 B | 2,394 | 1,523 | -36.38% |
| `md-review.md` | 37,762 B | 33,310 B | 10,329 | 7,094 | -31.32% |

## Preserved obligations and checks

- All original governance paragraphs remain, apart from extending the preload-eligibility list. New subheadings separate shared evidence rules from review-layer handoffs; original rule text stays intact.
- Human-review principles, complete section boundaries and exceptions are preserved. All roles retain truthful evidence reporting, missing-rule holds, Japanese output and execution limits.
- Both Claude profiles are synchronized. All 32 actual role definitions retain their models, tools and other frontmatter fields. Only skill lists and the two E2E rule-resolution paragraphs change; non-agent documentation is unchanged.
- Generated sources retain SHA-256 identity, missing/conflicting-source fallback and same-owner reuse. Tests cover missing sources/mirrors, stale output, source mismatch, output symlinks and setup links for new directories.
- Codex retains its three generated skills and selected source sections. No additional review layer or execution permission is introduced.

## Validation

The six affected unittest modules below ran **110 tests**, with **0 failures, 0 errors and 0 skips**, in 43.390 seconds. The observed run used `unittest.defaultTestLoader.loadTestsFromNames` and `TextTestRunner`. This command selects the same modules:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python -m unittest \
  test_engineering_preloads test_claude_review_execution_boundary \
  test_bias_dispatch_limits test_instruction_scope \
  test_parent_hq_contract test_md_review_flow
python3 -I -B tools/sync_engineering_preloads.py
git diff --check
```

The generator check and whitespace check also passed. Workflow tests use fake provider fixtures; their Claude/Codex IDs and approvals are not real model reviews. No full suite, external CI or live Claude invocation was run. A second author compared the MD translation with its baseline for permission boundaries, retry/resume limits and approval/handoff conditions; no translation loss was identified in those scopes.

## Reproduce the size comparison

Run at the candidate checkout with Python and the tokenizer version above. This reads the baseline from Git and the candidate from the working tree; it does not launch a model.

```python
from pathlib import Path
import re
import subprocess
import tiktoken

base = "1bf4624cd4a5ed45262f98edcd53cc488bf1667b"
encoding = tiktoken.get_encoding("o200k_base")

def read(path, before):
    if before:
        return subprocess.check_output(["git", "show", f"{base}:{path}"], text=True)
    return Path(path).read_text(encoding="utf-8")

def total(parts):
    return (sum(len(p.encode("utf-8")) for p in parts),
            sum(len(encoding.encode(p)) for p in parts))

for path in sorted(Path(".claude/agents").glob("*.md")):
    values = []
    for before in (True, False):
        definition = read(path, before)
        header = definition.split("---", 2)[1]
        match = re.search(r"(?m)^skills:\n((?:  - [^\n]+\n)+)", header)
        names = re.findall(r"(?m)^  - (.+)$", match[1])
        parts = [definition] + [read(f".claude/skills/{n}/SKILL.md", before) for n in names]
        values.append(total(parts))
    print(path.stem, values)

for path in sorted(Path(".codex/workflows").glob("*")):
    if path.suffix in {".md", ".yml"}:
        print(path.name, total([read(path, True)]), total([read(path, False)]))
```

## Deployment and remaining runtime trial

After choosing this candidate, rerun the existing setup for the selected profile to link new skill directories, then start a fresh Claude session. Existing real files remain protected by setup. Do not claim a retained session received the new skills.

A useful next live comparison pairs a non-UI task and a UI review on the same source/evidence and model settings. Record actual injected skill/source identities, original reads, all parent/child usage and outcomes. Retain both positive and negative cases and all required consultations. Missing logs stay NOT_MEASURED; source inspection and fixture tests never substitute for observed model behavior.
