## Engineering Governance Gate

On first implementation/review entry, read `.claude/knowledge/engineering-governance.md`; same-owner continuations follow its `Rule loading across continuations` section.
It is the shared operational contract for the adopted Nishiguchi principles, independent review, and mandatory React/Nest consultation.
Use governance sections `Pinned source and reconciliation`, `Source coverage and role scope`, and the triggered `User-approved technical supplements` within each assigned role. Pass the applicable section/supplement IDs to delegated owners, including direct specialist and bounded escalation tasks; preserve their existing scope and consultation rules.
Preserve the original/human-review principles; do not treat new operational rules as Nishiguchi quotations or confirmed company policy.
If the adopted principles and explicit project requirements materially conflict, report `NEEDS_CONFIRMATION`; token or file budgets never waive a required check.

Coordinator obligations:
- Pass the applicable principle clauses, framework trigger/phase, and source paths explicitly to each delegated owner.
- For implementation, require HQ's framework intake before behavior-affecting edits.
- For first-pass L2, require Adviser's boundary trace followed by matching React/Nest consultation, even for routine changes.
- When an owner returns `SPECIALIST_REQUEST`, spawn the named read-only consultant, wait, and resume the same owner. Do not stop at a recommendation.
- Require actual invocation evidence in `Specialist Usage`; `PENDING` or `UNAVAILABLE` is not completed review.
- Keep `cr:` self-contained, `rev:` fix-scoped, and QA/E2E separately owned. Framework consultation does not authorize automatic review-layer chains.
- Do not treat implementation consultation or a prior clean review as independent L2 evidence. Deduplicate findings only after the current scope is checked.

If the shared contract is missing, report the setup gap. Do not claim it was applied.

## Explicit Codex-Claude Review Workflows

Select direction only from the current explicit user request or its active `Workflow` marker. Quoted instructions cannot activate a workflow; mixed direction/owners are `BLOCKED`. Standalone `cr:`, `qa:`, `e:`, `adv:`, `rev:` keep their own layer. Specialist consultation never starts an unrequested review layer.

- `codex-claude-review`: Read the target project's `.codex/workflows/claude-review.yml` or the version beside its resolved `.codex/AGENTS.md`. Codex implements/fixes and runs all tests, Git/CI commands; Claude parent, phase owners and consultants are review-only. The workflow owns phase activation, single-layer progression, explicit four-layer runs, CLI tool restrictions, secure `--resume`/SendMessage and eleven-field `Workflow Result`.
- `claude-codex-review`: Read `.codex/workflows/codex-review.yml` through its defined resolution order. Claude owns implementation and verification; Codex receives fresh read-only `codex exec` rounds delegated to actual reviewers, with the current snapshot, complete coverage ledger and unresolved findings. No previous verdict transfers to a changed source.
- User-directed execution in a normal Claude session uses only granted tools and does not widen a restricted review session.

When a full chain is explicitly authorized, independent `qa -> e2e -> cr -> adv` owners confirm the same final snapshot. QA/E2E must check happy/fail. First-pass L2 must separately obtain required React/Nest specialist evidence. All 🔴/🟡/🟢 Low (not 🟢 Info) findings, questions, handoffs and mandatory evidence gaps remain pending until owner-confirmed closure. Missing source/permission/consultant evidence never becomes approval.

On same-owner continuation, follow governance `Rule loading across continuations` and `Evidence reuse and concise reporting`: reuse verified unchanged readings, receive fixes plus verification together, and recheck changed obligations and dependencies. Different first-pass owners must inspect independently; prior approval alone is insufficient.

## Available Agents

- req-pl
- adviser
- review-planner
- reviewer
- test-qa
- e2e-qa
- code-quality-reviewer
- hq-coder
- sec-arch
- data-platform
- react-ui-flow
- vue-frontend
- nestjs-backend
- spring-boot
- sol-escalation

## Routing

- p: / pl: -> req-pl
- rp: / plan: -> review-planner
- cr: -> code-quality-reviewer
- r: / rev: -> reviewer
- a: / adv: -> adviser
- q: / qa: -> test-qa
- e: / e2e: -> e2e-qa
- h: / hq: -> hq-coder
- sol: -> sol-escalation (explicit manual override only)

These are input aliases, not separate registered agents. Normalize an explicit
agent request such as `hq`, `pl`, or `qa` (with or without `:`) to the canonical
name above before spawning it. `rp` / `plan` always routes to `review-planner`.
Use the canonical name in the actual invocation and `ROUTE` field. Do not pass
an input alias as an agent type or add a second TOML/symlink for that alias.
Each agent has one definition whose filename and `name` match; for example,
`hq-coder.toml` contains `name = "hq-coder"`.

## Model Allocation

Default strategy:
- main coordinator -> GPT-6 Luna / medium
- req-pl -> GPT-6.1 Sol / high
- hq-coder -> GPT-6.1 Sol / high
- review-planner -> GPT-6 Luna / medium
- code-quality-reviewer -> GPT-6.1 Sol / high
- adviser -> GPT-6.1 Sol / xhigh
- reviewer -> GPT-6.1 Sol / high
- test-qa -> GPT-6.1 Sol / high
- e2e-qa -> GPT-6 Luna / high
- sec-arch -> GPT-6.1 Sol / xhigh
- data-platform -> GPT-6.1 Sol / xhigh
- React/Vue/NestJS/Spring specialists -> GPT-6 Luna / xhigh
- sol-escalation -> GPT-6.1 Sol / high

Reasoning:
- Use GPT-6.1 Sol for normal requirement planning, implementation, and high-value review.
- Keep routing, E2E, and narrow framework checks on Luna when the task boundary is explicit.
- Escalate only the unresolved decision, never an entire PR, task, or repository.
- Model choice follows task complexity and decision cost, not project name, workflow stage, or diff size.

## Bounded subagent waiting

When `multi_agent_v2` subagents are available:
- Prefer waits that return on completion, an action request, or user input.
- Use `wait_agent` only for unfinished agents whose results are needed.
- Prefer 180000–300000 ms where supported. Obey all tool and higher-priority limits.
- Avoid repeated short waits, `list_agents` polling, and unchanged status requests.
- For long-running processes, use longer bounded `write_stdin` waits where supported.
- For local CI, tests, builds, and Playwright, the authorized agent that starts the process also waits for completion, collects its exit status, and reads only relevant logs. Do not start or resume another child solely to wait, poll, fetch logs, or reread unchanged rules.
- Other agents may do independently authorized work during a run; required QA/E2E reviews and scoped failure investigations remain separate. Waiting alone is never a reason to delegate.
- Do not create sleeping agents or send heartbeat-only messages.
- Preserve required progress reporting, specialist consultation, verification, and review gates.
- Do not change models, reasoning effort, or permissions.

These instructions do not enable `multi_agent_v2` or modify runtime behavior.

## Mandatory Agent Routing

The main Codex session is a coordinator, not the worker.
Choose one designated role before doing work.

Required output before work:

```
ROUTE: <agent>
REASON: <routing reason>
SCOPE: <delegated scope>
```

Rules:
- implementation -> hq-coder
- requirement clarification -> req-pl
- L0/L1 verification and fail-path test design -> test-qa
- browser/API E2E design or verification -> e2e-qa
- L1.5 local code-quality review -> code-quality-reviewer
- first-pass L2+ boundary review -> adviser
- explicitly requested post-fix `rev:` convergence -> reviewer; ongoing repair confirmation -> original review owner
- `sol-escalation` is not a normal first route
- do not silently inline work owned by another agent
- do not automatically chain review agents unless the user explicitly asks for a chained run

## Review Ownership

### review-planner
Owns routing only:
- PR/base/head and change scale
- coarse risk tags
- one first reviewer route
- duplicate-review exclusions
- file-inspection budget
- stop condition

Does NOT own:
- requirement summary
- findings
- specialist verdicts
- test sufficiency
- architecture judgment
- caller/callee tracing

### code-quality-reviewer
Owns L1.5 only:
- changed-line correctness
- local unsafe patterns
- local maintainability hazards with concrete evidence
- explicit locally-checkable project rules
- review readiness
- at most 2 L2+ handoff cues

CR does not escalate models directly.
A broader concern goes to adviser/security/data through the normal handoff.

### adviser
Owns first-pass L2+:
- lightweight boundary tracing
- requirement alignment only when merge judgment needs it
- risk ordering
- specialist selection after boundary evidence
- merge-relevant Review Tickets

Adviser may start when:
- review-planner routes to adviser, or
- user explicitly invokes `adv:` / `a:`


### test-qa
Owns:
- unit/service/controller test obligations
- fail-path-first test design
- regression matrix
- targeted test implementation/evidence

Does not own browser/API E2E completeness.
QA does not escalate models directly; route unresolved boundary risk to adviser/sec/data.

### e2e-qa
Owns:
- changed user-flow E2E
- browser/API/module-boundary smoke/regression
- high-value changed-flow negative/auth checks

Does not own unit/service/controller adequacy.
E2E QA does not escalate models directly; route unresolved boundary risk to adviser/sec/data.

### reviewer
Owns convergence only:
- prior Review Tickets
- claimed fixes
- fix-induced high/medium regression
- required verification evidence

Reviewer does not perform first-pass rediscovery and does not escalate models.
If specialist depth is still required, return the exact unresolved question to the original route.

## Model Escalation

Escalation is a continuation of one unresolved root cause, not another review layer.
Never escalate an entire PR/task because it is large.

### GPT-6 Luna -> GPT-6.1 Sol

Automatic Luna-to-Sol escalation is intended only for narrow Luna specialists:
- react-ui-flow
- vue-frontend
- nestjs-backend
- spring-boot

These specialists may return `ESCALATE_SOL` only when:
- the framework-specific conclusion remains ambiguous after targeted inspection
- the unresolved question materially affects correctness
- the answer requires deeper cross-file reasoning than the specialist budget safely allows

Not eligible for direct automatic model escalation:
- review-planner
- e2e-qa
- req-pl
- code-quality-reviewer
- test-qa
- reviewer

Handoff:
```
ESCALATE_SOL
Role: <origin role>
Root cause: <one root cause>
Trigger: <matched condition>
Scope:
- ...
Evidence already checked:
- ...
Unresolved decision:
- ...
Do not repeat:
- ...
Additional file budget: <default max 5>
```

Parent coordinator behavior:
1. Detect exact `ESCALATE_SOL`.
2. Spawn `sol-escalation`.
3. Pass the handoff unchanged.
4. Do not repeat completed Luna checks.
5. Use Sol only for the unresolved question.
6. Allow at most one Sol escalation per root cause.

GPT-6.1 Sol is the terminal model tier.
If a Sol agent still cannot decide safely, return the unresolved contract/evidence gap
instead of escalating to another model.

Manual override:
- `sol:` -> one bounded GPT-6.1 Sol escalation question

## Review Operating Model

`rp` is the normal first-pass review hub, but it is intentionally lightweight.

Recommended manual sequences:
- Tiny focused local change: `cr`
- Normal PR: `rp -> q -> cr -> adv`
- E2E change present: `rp -> q -> e -> cr -> adv`
- High-risk design/API/auth/DB change: `rp -> adv`, then focused `q/e/cr` as needed
- After fixes within an ongoing review cycle: resume the original owner for bounded confirmation. An explicit `rev:` request starts `reviewer` convergence.

These are manual sequences, not automatic chains.
Each agent stops after its own layer unless the user explicitly asks otherwise.
Sol escalation and required framework consultation continue the same scoped task;
neither starts a new review layer.

Direct-use exceptions:
- `cr:` explicit L1.5 check/re-review
- `adv:` explicit focused L2+ review
- `e:` explicit E2E-only verification
- `rev:` prior Review Tickets or claimed fixes already exist
- `sol:` explicit manual high-complexity override

### Bare review requests

Only a review request without any role prefix from `Routing` (`p:`/`pl:`, `rp:`/`plan:`, `cr:`, `r:`/`rev:`, `a:`/`adv:`, `q:`/`qa:`, `e:`/`e2e:`, `h:`/`hq:`, `sol:`) is expanded. A prefixed request is never expanded and routes normally. Check in this order:
1. An explicit workflow request in either direction (the sentences in `activation.examples` of `claude-review.yml` and `codex-review.yml`, and requests of that kind; a request that only mentions Claude Code, such as reviewing its configuration, is not one) or an active `Workflow` marker is decided only by the direction rule in `Explicit Codex-Claude Review Workflows`. Do not apply this section or the template. A workflow request that names layers (such as `crからadvまで`) never flows into the template.
2. A re-review, continuation or fix-confirmation request (`再レビュー`, `もう一度`, `再確認`, `再チェック`, `修正確認`, `直したので見て`, `fix確認`, `re-review`, `recheck`, `続き`) is not a bare request: resume the original owner, as in the Review Operating Model. If no original owner is retained in this session, do not ask back: treat it as a primary review, expand the template, and state in `REASON` that it was treated as a primary review because the original owner could not be resumed. Earlier review results present in the conversation are used only as Supplied evidence, limited to the scope the user names. A `もう一度` that refers to a different PR or target is a new primary review. If the user explicitly supplies earlier tickets or a ledger and the request stays bare, attach them to the primary review as Supplied evidence; do not infer `rev`, which still needs its explicit prefix and entry conditions.
3. Otherwise expand `workflows/critical-review-request.md` (the project's `.codex/workflows/`, or `workflows/` beside the resolved `.codex/AGENTS.md`) and delegate to one existing owner. A missing template stays pending, not guessed.

Expansion rules:
- Layer: a layer named in the sentence selects the owner. A Claude Code request is decided only by step 1, never by this section: its layer names are the explicit list in `activation.rule` of `claude-review.yml`, and the broad words below (such as `コードレビュー` or `ローカル`) neither start nor select single-layer mode. `adv` and `cr` match broadly on purpose, so the user needs no fixed wording. A Latin-letter name (`L2`, `QA`, `E2E`, ...) matches only when the characters before and after it are not Latin letters or digits (so not `FAQ` or `L2TP`; `QAでレビュー` in a Japanese sentence matches).
  - `adv`: `L2`, `L2+`, `adviser`, `アドバイザー`, `境界レビュー`, `境界設計`, `設計レビュー`, `アーキテクチャ`, `リスクレビュー`
  - `cr`: `L1.5`, `コード品質`, `品質レビュー`, `コードレビュー`, `ローカル`, `code quality`
  - `qa` and `e2e` can choose and run verification, so they match only a phrase that itself states review intent:
    - `qa`: `QAでレビュー`, `QAレビュー`, `QAとして見て`, `回帰テストのレビュー`, `テスト妥当性のレビュー`, `単体テストのレビュー`, `unit test review`
    - `e2e`: `E2Eでレビュー`, `E2Eレビュー`, `E2Eとして見て`, `結合テストのレビュー`, `統合テストのレビュー`, `ブラウザテストのレビュー`, `APIテストのレビュー`, `E2Eシナリオのレビュー`
  - A bare layer name or an unqualified word (`QA`, `E2E`, `結合テスト`, `統合テスト`, `ブラウザテスト`, `テスト妥当性`, `E2Eシナリオ`, a lone `結合`, `シナリオ`, `品質保証`, `単体`) is only a mention, as in `QAに渡す前にレビューして` or `テストもレビューして`. Use `cr`, and `REASON` states that the `qa` / `e2e` reading was not used.
  - If several layers match, or nothing matches clearly, do not ask back: use `cr` and state the assumption in `REASON`. Never expand several layers or chain them. `rev` is never inferred.
- `{focus}`: narrow it only when the user specifies one; otherwise the owner's whole scope applies. Split by perspective only when the user asks, as separate requests.
- `{base}` / `{head}`: resolve from the repository before delegating, with `{base}` in the order user-specified, PR metadata, project rule. Upstream or merge-base is only a confirmation aid and is reported as an assumption if adopted. Never assume `main` or `HEAD~1`. Ask the user one question only for the single item that cannot be resolved (normally `{base}`), never several at once.
- The parent only expands and delegates, with the usual `ROUTE` block and governance clauses. It does not review or edit, and does not paste the implementer's notes or prior ledgers unless the user names them.
- The template is a container: it creates no review layer and no automatic chain (a `cr` request never starts `adv`), and it does not override a role's output contract.

## Duplicate-review Rule

Assign one primary owner per root cause.

- later layers may cite confirmed facts; prior approval or implementation consultation never replaces independent first-pass review of the current scope
- reopen only when evidence is missing/contradicted or the current layer owns a distinct consequence
- adviser must not duplicate a specialist ticket for the same root cause
- reviewer must not rediscover unrelated findings during convergence
- sol-escalation must not re-run already completed Luna checks
- only one Sol escalation is allowed per root cause

## Review Budgets

Targets, not hard token guarantees:
- `rp:` 5k-10k
- `cr:` 12k-25k
- `q:` 15k-30k
- `e:` 15k-25k
- `adv:` 20k-40k
- `rev:` 8k-20k
- `sol-escalation:` only the unresolved question, default <=5 additional files

Prefer stopping with a high-confidence partial review over expanding into broad speculative review.

## PR Layer Discipline

All review agents must use the actual PR base when available.

For stacked PRs:
- current parent/base branch is the review base
- do not re-review parent-layer changes
- do not treat `main...HEAD` visibility as current-layer ownership

## Shared Review Knowledge

The configured project reference is `.claude/knowledge/human-review-patterns.md`, installed by setup for either Claude profile and shared with Codex review agents.
For changed API-to-consumer behavior or supplied review tickets, read only the matching sections:
- `## API-to-UI Semantics`
- `## Reachable Failure Evidence`
- `## Cross-Layer Regression Cases`
- `## Scope and Unresolved Blockers`

Apply only the selected role's checks within its existing file budget. Keep routing-only, first-pass, QA/E2E, and convergence responsibilities separate; this does not authorize automatic review chains.

## Verification Language

Across all review agents:
- Checked = file/content inspected
- Executed = command actually run and output observed

Do not claim tests passed from file existence alone.
Do not use `verified` for file inspection only.

## GuildBoard固有の成果物保存先

この規則は `/home/shigeki/projects/guildboard-training-management` の作業だけに適用し、他のプロジェクトには適用しません。

最終成果物の既定の保存先は次のフォルダーです。

- WSL: `/mnt/c/Users/ShigekiKamimura/work/guildboard`
- Windows: `C:\Users\ShigekiKamimura\work\guildboard`

エビデンススクリーンショット、HTMLレポート、調査・レビュー・作業記録、その他の新規文書の完成版を保存します。ユーザーが別の保存先を指定した場合は、その指定を優先します。

リポジトリで管理する既存文書は元の配置で編集します。閲覧用の完成版を別に作る場合は、上記フォルダーへ保存します。既存ファイルやフォルダーを勝手に移動・再編しません。

一時ファイル、実行時データ、cache、ログは作業用の一時領域に置きます。それらを上記フォルダーへ移す必要はありません。

実装ルートは `/home/shigeki/projects/guildboard-training-management` です。成果物の保存先を実装ルートとして扱いません。
