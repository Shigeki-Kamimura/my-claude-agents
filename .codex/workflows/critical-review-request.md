# 批判的レビュー依頼のひな形

Purpose: The parent expands an unprefixed 「レビューして」 into the request below for an existing review agent.
First-pass only; no new review layer, automatic chain or override of any agent's output contract.
Expansion conditions and procedure are defined by `.codex/AGENTS.md` `Bare review requests`.
The wording is shareable; operation is Codex-only (`.claude/CLAUDE.md` has no corresponding expansion rule).

Do not use for:
- Requests with a role prefix (`p:` `rp:` `cr:` `ci:` `rev:` `adv:` `qa:` `e2e:` `hq:` `sol:` and aliases); route to that role normally.
- Explicit workflow requests in either direction, including layer names such as `crからadvまで`, or an active `Workflow` marker; follow that workflow.
- Re-review, continuation or fix-confirmation requests; resume the original owner. If unavailable, follow `.codex/AGENTS.md` `Bare review requests`.

## プレースホルダー

The expander fills these. Try Git or other available evidence first; ask the user one question only for an unresolved item.

- `{layer}`: `cr` / `adv` / `qa` / `e2e`. Use the layer named in the request; see `.codex/AGENTS.md` for vocabulary/matching (`qa` / `e2e` require a phrase expressing review intent). Otherwise use `cr`. `rev` requires an explicit prefix.
- `{base}`: Actual comparison base (name and SHA), in precedence order of user selection, PR metadata, project rules.
  Upstream/merge-base are confirmation aids; if adopted, state the assumption in the request. Never assume `main` or `HEAD~1`.
- `{head}`: Actual comparison target (name and SHA).
  With no uncommitted changes, use only the normal base/head diff. For uncommitted-only review, use base `HEAD <sha>` and head 「作業ツリー」.
  For mixed committed/uncommitted changes, include both under the default `{scope}` and use head 「ブランチ先端 + 作業ツリー」.
- `{scope}`: Default is 「`{base}` と `{head}` の差分、およびステージ済み・未ステージ・未追跡の変更」.
  Preserve exclusions, secret and ignore policies. For working-tree review, identify scope by uncommitted contents as well as HEAD.
- `{focus}`: Use only when user-specified; otherwise cover the entire `{layer}` responsibility.
  Split perspectives into separate requests only when the user asks.

## 依頼文

```text
Request a {layer} review. Use a fresh task/context where possible; inspect independently of the implementer's explanation.

対象
- base: {base}
- head: {head}
- 範囲: {scope}
- 観点: {focus}

前提
- First record the operation/responsibility, acceptance/rule sources and expected before/after briefly as `Review objective` in the existing coverage ledger. Map checks/consultations to that objective, mandatory rules or open IDs. An unconfirmed objective never waives mandatory checks; hold dependent judgments.
- Seek failure conditions without assuming approval.
- For each part judged to pass within your layer, consider a failing input/state once to challenge it.
  Do not report the contemplated inputs themselves. Only if you can neither refute it nor establish a rationale, record one line in 「未確認」.

指摘の条件
- Defect: show reachable conditions, causal path and consequence.
- Rule violation: cite the applicable mandatory rule and concrete mismatch. No invented runtime crash is needed.
- Verification gap: identify the missing obligation and why judgment depends on it.
- Without any of these, record the reason in 「未確認」, not as a finding.
- Preferences/alternatives are mandatory only with an applicable rule or concrete risk.
- Check implementer claims (「到達しない」「テストで保証されている」, etc.) against code; do not accept them at face value.
- Zero findings is valid; never manufacture findings.

独立性
- Do not base conclusions on implementer self-reports, notes or prior review ledgers, except those explicitly supplied in this request.
- Use requirements, design and project rules as evidence.
- Obtain the actual diff and surrounding source independently.

報告
- State inspected and uninspected scope.
  Zero findings is valid only with complete coverage. Unchecked scope never supports approval.
- Report every 🔴🟡 finding in severity order, without a count limit.
  Split minor observations into 🟢Low and 🟢Info. 🟢Low findings are capped at 5, highest impact first. Overflow is 🟢Info, not findings; one concise line each or omit. Evidenced defects/spec mismatches instead stay tracked as 🟢-weighted handoffs (HND-1), never Info. Never promote/relabel existing 🟢Info as 🟢Low. Classify once from first-report evidence; a fix-induced new 🟢Low is a fresh classification with `Origin: FIX_INDUCED` (existing Origin/re-review caps unchanged). Any open 🟢Low, even `DEFER`, requires `L1.5_REQUEST_CHANGES` / `REQUEST_CHANGES`, never an approval label. New evidence-backed 🟢Low found on re-review may be reported as new findings.
  On budget exhaustion, report unchecked scope and the next slice.
- For working-tree review, report checked base/HEAD and identify the uncommitted contents.
- Record rule compliance as `source/section -> responsibility or invariant -> inspected evidence -> result`.
  result is `COMPLIANT / NON_COMPLIANT / NOT_APPLICABLE / UNCONFIRMED`.
  Follow governance `Evidence reuse and concise reporting` and the assigned agent's output contract for concise reporting.
- This request never overrides the assigned agent's output contract.

制約
- Do not edit source/tests or stage, commit, push or merge.
- Inspect only with Git, reads and search. Do not run apps, builds or tests.
  (qa / e2e may choose and run necessary verification under their agent definitions.)
- Start no other review layers, except the assigned agent's required framework consultation.
  Report handoffs in the assigned agent's output-contract format.
```

## 参照する規則

Use these `.claude/knowledge/engineering-governance.md` sections:
- `Pinned source and reconciliation`, `Principle application`, `Source coverage and role scope`, `User-approved technical supplements`
- `Review objective and evidence`, `Scope, budgets, and stop conditions`, `Independent review and reconciliation`
- `Evidence reuse and concise reporting`, `Rule loading across continuations`
- `Autonomous Claude review` (a Claude section; Codex borrows only the default `{scope}` of staged/unstaged/untracked changes, never Claude-specific full access or staged-baseline procedures)

The corresponding agent definition (`.codex/agents/*.toml`) governs each layer's scope and output contract.
`code-quality-reviewer.toml` supplies the no-app/build/test-execution policy and separate working-tree content identification.
