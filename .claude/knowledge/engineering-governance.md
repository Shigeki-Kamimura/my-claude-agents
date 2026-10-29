# Engineering Governance

## Authority and provenance

The user adopts Nishiguchi's review policy as the constitutional engineering baseline for implementation and review in this configuration.
Company-wide adoption is not confirmed. This document is an operational interpretation, not Nishiguchi's original wording.

- Preserve `human-review-patterns.md` in this knowledge directory as the existing human-review reference.
- Do not invent quotations, attribute new preferences to Nishiguchi, or silently rewrite an authoritative source.
- Separate the source principle, an explicit project rule, and a user-approved AI operational improvement.
- If the original guideline becomes available, record its source/revision and reconcile this interpretation. Do not claim original-source compliance without reading it.
- Platform instructions, security controls, and explicit project requirements retain their actual precedence. Report a material conflict with the adopted principles as `NEEDS_CONFIRMATION`; do not silently weaken either side.
- Within these engineering instructions, source-backed principles and contracts take priority over convenience, token targets, sample/file budgets, and duplicate-output reduction.
- Project conventions are scoped. Suspense, ORM exception helpers, audit formats, and API conventions require an applicable project source; do not export one project's choices to every repository.

### Pinned source and reconciliation

- Source: Nishiguchi, [Coding Guidelines](https://github.com/Shigeki-Kamimura/coding-guidelines), README.md.
- Reference revision: [`4f2f34ea149a52869a551acbcf17580da357e96f`](https://github.com/Shigeki-Kamimura/coding-guidelines/blob/4f2f34ea149a52869a551acbcf17580da357e96f/README.md). Checked: 2026-10-29 (Asia/Tokyo).
- Reconciliation covers the chapter inventory and related sections, especially §§1, 5.2–5.3, 6.4–6.5, 9–10 and 16. This is not a complete review of all sixteen chapters or proof of every agent's compliance.
- The five-principle table below is an operational summary, not the complete source. Responsibility separation maps to §§2, 4 and 5.2; meaningful exceptions to §§6.5, 9 and 10; type safety to §§6.4–6.5; focused changes to §§1, 5.2–5.3. Project design-document checks are an adopted operating rule, not a separate chapter attributed to the author.
- Preserve the source unchanged. Keep the user-approved technical supplements below separate from the source and from project-specific contracts. A later source revision requires targeted reconciliation before changing the adopted interpretation; do not silently track a moving branch.

## Principle application

Every implementing/reviewing owner independently reads the applicable contract and `human-review-patterns.md` sections on first entry, even when invoked directly. Claude section delivery may use `Preloaded rule delivery` below. Same-owner continuations follow `Rule loading across continuations` below.
Planning, routing and consulting roles apply the source index and triggered supplements within their assigned responsibility. Bounded escalation roles reuse unchanged supplied rule evidence and read only missing or changed relevant sections; this does not restart a complete rule/review pass.
Read the minimum complete relevant project rule, including exceptions. Use the explicit task/project source first, then discover actual local rule paths; an example path is not a universal source.

| Adopted principle | Implementation obligation | Review obligation |
| --- | --- | --- |
| Responsibility separation | Identify the owner/layer before placing logic; use the smallest design-correct boundary. | Identify the concrete mixed responsibility and its consequence or sourced rule violation. |
| Meaningful exception handling | Catch for recovery, translation, cleanup, or meaningful context; preserve unexpected failures. | Trace failure meaning and propagation; reject empty, pointless, or misleading handling. |
| Type safety | Validate untrusted input and narrow types; do not silence mismatches with casts. | Check runtime evidence, not just type annotations; distinguish justified boundary assertions from unsafe casts. |
| Focused refactoring | Include required boundary repairs, not unrelated cleanup or speculative abstractions. | Check both unnecessary scope expansion and a small patch that preserves a known violation. |
| Design alignment | Read the applicable rule before editing. | Cite the exact rule and changed code; distinguish mandatory rules from examples/preferences. |

Use `source/section -> responsibility or invariant -> inspected evidence -> result` for triggered principles.
Results are `COMPLIANT / NON_COMPLIANT / NOT_APPLICABLE / UNCONFIRMED`, scoped to inspected evidence.
An explicitly mandatory rule violation does not need an invented runtime crash to be blocking. An optional preference does not become mandatory because an AI repeats it.

### Preloaded rule delivery

Claude subagents may satisfy first-entry reading for exact sections delivered by the generated `engineering-review-core`, `engineering-react-rules`, and `engineering-nest-rules` skills. This is a user-approved delivery rule, not a new quotation from Nishiguchi. Each owner must actually receive the skill text in its own context and retain its included section names and source SHA-256 as `Rules loaded` evidence. A frontmatter declaration alone is not delivery evidence or whole-document reading.

The coordinator checks source identity against the active project's current rules and supplies permitted digest/metadata evidence; SHA-256 here is not a Git blob hash. Missing, changed, unverified or conflicting sources require targeted original reading, including exceptions, or an exact evidence request. Claude reviewers do not run shell/hash commands for this check. Project-local configured sources take precedence; never replace a project-specific document with a shared summary without checking its identity. Existing read-at-entry instructions remain mandatory for applicable sections not actually injected. Codex agents without these Claude preloads retain their normal reading requirements.

Reuse unchanged, verified injected sections on the same-owner continuation. Read only missing/changed relevant sections and project design rules; preloading does not expand routing/planning/consultation scope, permissions, or approval authority. Missing mandatory evidence stays pending. Regenerate both profiles with `python3 -I -B tools/sync_engineering_preloads.py --write` after a source change and check without `--write` before publishing. Existing deployments need setup again to link new skill directories, followed by a fresh Claude session. Do not infer runtime compliance or token savings from static configuration checks.

### Core rules for Claude preload

This is the user-approved operational core, not Nishiguchi's wording or proof of company-wide adoption. Preserve the pinned source and the separate human-review reference. Explicit project rules and platform/user controls retain their precedence. Do not invent quotations or export one project's conventions to another project.

- Responsibility: identify the actual owner/layer and a concrete mixed responsibility before requesting a boundary change. Reuse existing validated concepts, but do not merge contracts merely because their fields match.
- Exceptions: catch for recovery, error translation, cleanup or meaningful context. Preserve unexpected failures and their cause. Do not remove every catch or accept an empty catch.
- Types: validate untrusted boundaries and narrow types. An annotation/cast is not runtime validation; a justified framework assertion is not automatically a defect. Check the actual producer and nearest guard before asserting reachability.
- Scope/design: make the smallest design-correct change, including required boundary repair. Read applicable project rules and their exceptions. A sourced mandatory violation needs no invented crash; an optional preference is not a blocker.
- Evidence: separate reachable defects, mandatory-rule violations, verification gaps and optional observations. Record inspected revision/source and the obligation behind the expected behavior. Missing evidence never becomes approval; retain supplied unresolved findings and handoffs until the owning reviewer confirms closure or withdraws with evidence. Never use Info classification to close an unresolved mandatory obligation.
- Ownership: implementation owns edits; each requested review layer retains its own scope. L1.5 stays self-contained. HQ and first-pass L2 must obtain applicable React/Nest consultation after tracing the boundary; implementation advice does not replace independent L2 evidence. Consultants advise only on their assigned boundary, and review-planner routes metadata only. This does not authorize an additional layer or delegate.
- Execution: the active workflow and actual tool restrictions decide execution permissions. In codex-claude-review, all Claude reviewers/consultants stay review-only and Codex owns commands, tests, fixes and CI. A normal Claude session may execute an explicit user request with available permissions. Never bypass restrictions through another agent.
- Completeness: budgets do not waive mandatory rules, consultation, blocker closure or current-snapshot evidence. A clean single-layer result does not grant four-layer/final/merge approval. Read the detailed source index, triggered ASYNC-1/HTTP-1, phase ownership, minor-finding/closure rules and retained-blocker obligations when relevant and not already injected. Preserve their conditions and exceptions.

## Source coverage and role scope

Use this index when the assigned change triggers a topic. Read the complete relevant source section, including exceptions, with the applicable project rules. Chapter names and line starts refer to the pinned README above; this index is not a claim that each chapter has been fully audited.
The listed roles identify responsibility, not a new review chain or permission to invoke every role. Keep existing consultation triggers and the selected layer's scope. `review-planner` uses metadata to route only; escalation roles resolve only their supplied question. Reuse unchanged readings under `Rule loading across continuations`.

| Source chapter (README line start) | Trigger in the assigned change | Responsible owner within existing scope |
| --- | --- | --- |
| §1 コードの量と本質 (L48) | Added concepts, deletion, or scope growth | `req-pl`, `hq-coder`, selected CR/ADV owner |
| §2 概念を実装する (L144) | Domain concepts, states, or model boundaries | `req-pl`, `hq-coder`, selected CR/ADV owner |
| §3 命名（名前警察） (L424) | A name misrepresents the responsibility or contract | `hq-coder`, selected CR/ADV owner; no naming-only blocker without an applicable rule |
| §4 責務と疎結合 (L514) | Controller, service, component, or dependency ownership | `hq-coder`, matching framework consultant, selected CR/ADV owner |
| §5 再利用と資産化（装備を充実させる） (L1096) | Reuse, abstraction, or refactoring | `hq-coder`, selected CR/ADV owner |
| §6 ロジックの書き方 (L1237) | Branches, invariants, types, or input validation | `hq-coder`, matching framework consultant, assigned QA/CR owner |
| §7 副作用と不変性 (L1505) | Mutation, shared state, or external effects | `hq-coder`, matching framework/data consultant, selected reviewer |
| §8 パフォーマンス（計算量） (L1699) | Changed work size, queries, batches, or concurrency limits | `hq-coder`, matching framework/data consultant, selected reviewer |
| §9 非同期・並行処理 (L1816) | Promises, cancellation, partial failure, or concurrent effects | `hq-coder`, matching framework/data consultant, assigned reviewer/QA/E2E owner; apply supplement ASYNC-1 |
| §10 エラーハンドリング (L1912) | Catch, error translation, HTTP errors, or user recovery | `hq-coder`, matching framework consultant, assigned reviewer/QA/E2E owner; apply supplement HTTP-1 when authentication/authorization is involved |
| §11 セキュリティ (L2013) | Untrusted input, identity, authorization, secrets, or PII | `hq-coder`, `sec-arch`, matching framework consultant, assigned reviewer/QA/E2E owner |
| §12 ログと可観測性 (L2102) | Logs, causes, correlation, or sensitive diagnostic data | `hq-coder`, `sec-arch`/`data-platform` when their boundary is affected, selected reviewer |
| §13 スケールアウトを前提に書く (L2122) | Process-local state, multiple instances, or distributed work | `hq-coder`, `data-platform`, matching backend consultant, selected reviewer |
| §14 トランザクションと整合性 (L2147) | Dependent writes, commit timing, or partial persistence | `hq-coder`, `data-platform`, matching backend consultant, assigned reviewer/QA/E2E owner |
| §15 冪等性（リトライ・重複に耐える） (L2182) | Retry, duplicate requests, jobs, or external delivery | `hq-coder`, `data-platform`, matching framework consultant, assigned reviewer/QA/E2E owner |
| §16 チェックリスト (L2218) | Final check of the topics actually changed | Current assigned owner only; retain unchecked obligations without claiming complete source compliance |

## User-approved technical supplements

These supplements were adopted by the user on 2026-10-29. They clarify application of the pinned examples; they are not quotations from Nishiguchi or edits to the original guideline. Apply only the supplement triggered by the assigned boundary, including direct agent invocation. Preserve explicit project contracts and report material conflicts.

### ASYNC-1: Promise aggregation does not cancel work

- Trigger: interpreting or changing `Promise.all` failure behavior, especially when started operations can write data or cause external effects.
- `Promise.all` rejects its result when an input rejects; it does not itself cancel the other started operations or roll back their effects. Do not infer that work stopped or that no write succeeded from the aggregate rejection.
- Follow the actual contract for continued work, partial success, cancellation, cleanup and retry/idempotency. `Promise.allSettled` waits for outcomes; it does not provide cancellation, rollback or atomicity. Require a cancellation/transaction design only when the affected contract needs it, not for every parallel read.
- Source context: [guideline §9.3](https://github.com/Shigeki-Kamimura/coding-guidelines/blob/4f2f34ea149a52869a551acbcf17580da357e96f/README.md#L1854-L1865). Technical basis: [MDN, Promise.all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all), [ECMAScript, PerformPromiseAll](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-performpromiseall).

### HTTP-1: Distinguish authentication and forbidden access

- Trigger: interpreting or changing HTTP 401/403 handling, error translation, login recovery, or permission guidance.
- A 403 alone does not prove an expired session or that logging in again will resolve the failure. Normally give the applicable permission guidance; determine reauthentication from the actual API/authentication contract and verified error details. Do not create an automatic login/retry loop with unchanged credentials.
- Distinguish 401 (missing valid authentication credentials for the target resource) from 403 (the server understands the request but refuses it). Some APIs document different mappings. Inspect that producer contract before changing its consumer; do not relabel every 403 or prohibit documented recovery using new credentials.
- Preserve unexpected failures and their cause. A status or catch boundary does not establish an unobserved cause.
- Source context: [guideline §10.1](https://github.com/Shigeki-Kamimura/coding-guidelines/blob/4f2f34ea149a52869a551acbcf17580da357e96f/README.md#L1968-L2009). Technical basis: Fielding, Nottingham and Reschke, [RFC 9110 §15.5.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2) and [§15.5.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.4), 2022.

### Calibration examples

Use these examples when evaluating whether agents apply the adopted rules correctly, not as a new test/review gate for each task. Compare the agent's judgment and evidence with the expected decision; record the agent, rule revision and actual result when run. Static configuration checks do not count as agent execution. Include both missed defects and unsupported findings; more findings is not a success metric.

| Case | Expected decision and evidence | Unsupported judgment to avoid |
| --- | --- | --- |
| Two types have the same fields but different contracts and reasons to change | Keep the contracts separate unless actual shared responsibility is established (§5.2) | Demand a shared type based only on matching shape |
| Existing types/helpers represent the same validated contract | Reuse the nearby definition or give a contract-based reason not to (§5) | Create a duplicate concept without checking existing ownership |
| A catch recovers, maps a verified error, adds useful context, or cleanup is required | Preserve that responsibility and unexpected-error propagation (§10) | Remove every catch or lose cleanup because catch is considered undesirable |
| External JSON is assigned a TypeScript type without runtime validation | Identify the unvalidated boundary; check the actual validator and reachable input (§6.4–6.5) | Treat an annotation/cast as validation, or demand repeated validation of an already validated internal value |
| One parallel write fails while another started operation can still succeed | Check continued effects and the real partial-success/retry contract (ASYNC-1) | Claim aggregate rejection cancelled or rolled back the writes |
| Independent parallel reads may continue after one failure, and the contract permits this | Accept the documented outcome (ASYNC-1) | Demand cancellation, transactions, or `allSettled` solely because `Promise.all` appears |
| An API returns 403 for an authenticated user without permission | Preserve permission guidance and check the API contract (HTTP-1) | Force logout/login or retry indefinitely with unchanged credentials |
| An API explicitly maps a recoverable invalid session to 403 | Follow the documented, bounded reauthentication flow after verifying that contract (HTTP-1) | Ban all reauthentication for 403 or assume the same mapping for other APIs |

## User-approved AI operational improvements

These checks strengthen application of the baseline; they are not additional quotations from Nishiguchi.
Apply them only within the selected role's ownership.
Before introducing a new concept, check nearby reusable types, literals, helpers and existing responsibilities. Do not force reuse across different contracts.

1. Establish the obligation before trusting the implementation. From current requirements/rules, name the changed responsibility, invariant, and acceptance condition. Do not derive expected behavior solely from the new code or its mocks.
2. Trace the relevant path. For a local review, stay within the function and immediate context. For L2, follow affected producer/consumer boundaries, failure handling, and side effects as required by the change.
3. Challenge each candidate finding. Check the nearest guard, filter, validation, transaction, existing consumer, documented exception, or bounded-data assumption that could disprove it. Report the resulting evidence, not private deliberation.
4. Separate finding kinds. A defect needs reachable preconditions, a causal code path, and a consequence. A rule violation needs the applicable mandatory rule and concrete mismatch. A verification gap needs the missing obligation and why judgment depends on it. Optional improvements are non-blocking.
5. Match evidence to the revision. Record base/head and relevant working-tree changes. A new commit, renamed symbol, passed unrelated suite, or source-file existence is not proof of a fix.
6. Close coverage explicitly. Use `Review Coverage: COMPLETE / PARTIAL / BLOCKED` for the requested scope, list uninspected obligations and their owners, and never turn missing evidence into approval.

### Scope, budgets, and stop conditions

- Token/file targets bound each slice, not the definition of correctness. Preserve all triggered mandatory checks in the coverage record.
- On a budget limit, return inspected/pending paths, remaining obligations, and the next same-layer slice. The coordinator may continue that requested layer; do not start another review layer without authorization.
- Do not cap finding counts or stop after a fixed number. Report every evidence-backed 🔴/🟡 finding and every `🟢 Low` finding within the requested scope, ordered by severity (the `Low` limit and `Info` are defined in the next minor-findings bullet). Group the same root cause without dropping distinct impacts or obligations.
- Use `Severity: 🔴 Critical/重大 / 🟡 Important/重要 / 🟢 Minor/軽微` for concrete impact. Severity is separate from status, coverage, and native verdicts; the color does not decide approval or closure. Preserve existing mandatory checks and workflow closure conditions.
- Minor findings are `🟢 Low` or `🟢 Info`. `Low` is a finding: it has an ID, owner and status, is tracked, fixed and re-reviewed like any finding, and counts toward approval and closure. A layer reports at most 5 `Low` per review pass (initial or re-review), highest impact first. `Info` is not a finding: no ID, no ledger entry, no tracking, no fix, no re-review, and it never blocks approval; write each as one concise line or omit it. Minor observations beyond the 5 `Low` become `Info`, lowest impact first. An item classified `Info` stays `Info`: never raise or re-label it as `Low` (not on re-review, not to fill the 5-`Low` limit, not because fewer than 5 `Low` exist). A `Low` arises only from a fresh, evidence-backed classification as `Low`; a new `Low` found on a re-review is allowed as a new finding, counts within the 5 per pass, and stays subject to any re-review cap the workflow defines (for example `rereview_cap`/`NEW_UNRELATED` in `claude-review.yml`). A mandatory-rule violation is never `Info`. Never lower a 🔴/🟡 finding, question, handoff or missing mandatory evidence to `Low`/`Info` (or drop it) to avoid an approval condition; reclassification does not satisfy any approval or closure condition. Existing closure statuses such as `reviewer_confirmed_fixed` and `reviewer_withdrawn` are unchanged. The convergence `reviewer` tracks only supplied `Low` items (and 🔴/🟡) and does not carry `Info`.
- A proven blocker permits an early `REQUEST_CHANGES` with `Review Coverage: PARTIAL`; list remaining scope. Do not present this as an exhaustive review or silently discard supplied tickets.
- Zero findings is valid. Do not invent issues, require a quota, or increase severity to appear strict.
- `COMPLETE` means the declared scope and its required checks are covered; it does not guarantee defect-free code or overall PR approval.

### User-directed execution permissions

This is a user-approved operational rule, not a quotation from the human review guidelines.

Autonomous review without an explicit execution request does not start typecheck, lint, build, tests, Playwright, CI or other verification commands.

For `Workflow: codex-claude-review`, Claude and its review subagents only inspect sources and supplied evidence. Codex owns command execution, test creation, CI operations and fixes. A message cannot expand the restricted CLI toolset of an existing review session.

When the user explicitly requests execution in a normal Claude Code session, the main Claude session or an authorized implementation/verification owner may perform those actions with its available permissions. If an existing restricted session cannot execute them, use a separate normal session. Do not treat this direct request as an autonomous review or an automatic Codex-to-Claude review.

### Autonomous Claude review

These rules apply to standalone Claude review and `codex-claude-review`, not the reverse read-only Codex transport. For `Workflow: codex-claude-review`, the user's latest instruction requires review-only Claude (parent, CR, QA, E2E, ADV and review consultants). Invoke initial and resumed sessions with `--permission-mode dontAsk`, `--tools "Read,Glob,Grep,Agent,SendMessage"`, and `--allowedTools Read Glob Grep Agent SendMessage` and `--disallowedTools Bash Edit Write NotebookEdit "mcp__*"`. Do not run Git/shell, typecheck, lint, build, format, tests, Playwright, CI/CD jobs, app/server commands, package/migrations, or scripts, and do not delegate execution or edits to specialists. The CLI denial is a mandatory safeguard, not a substitute for role instructions; if it cannot be applied, return BLOCKED. This scoped restriction does not change separately authorized Claude implementation or reverse-direction workflows. Other platform/managed/user limits retain precedence.

Claude reads the applicable project/shared rules, finds the actual review base from the user's request, real PR metadata or project rule, and gets its own Git diff/status/related source. Never assume `main` or a prior verdict. Absent a narrower selection, include staged, unstaged and untracked paths; keep index/worktree changes distinct even when they cancel, and preserve exclusions/secret/ignore policy. Inspect branch changes against the confirmed base when assigned. Continue obtainable work if the base is missing, but do not approve an unknown branch scope. New/deleted/renamed files and actual untracked contents must not disappear from the review.

For `codex-claude-review`, Claude only inspects applicable sources with Read/Glob/Grep, reviews existing evidence, identifies defects/test gaps, requests precise missing checks and returns verdicts. QA and E2E still independently review happy/fail adequacy, but do not implement or execute tests. Codex/HQ alone gathers Git base/index/worktree/untracked snapshots, creates/edits source/tests/fixtures, runs checks and Playwright, starts/reruns CI, collects command/status/run IDs and produces logs. Claude treats Codex results as Supplied and verifies their source revision; a claimed pass without traceable evidence is NOT_RUN/unconfirmed. A missing needed run is sent to Codex as an evidence request, not executed by Claude. This scope does not override ordinary implementation-side QA ownership outside this workflow.

Keep a recoverable comparison basis during your own inspection: immutable base/HEAD and index blob IDs/modes, plus the reviewed working-tree/untracked contents and path states, including additions, deletions and rename endpoints. Complete retained context or a minimal private temporary source snapshot may preserve mutable bytes. In the user-authorized staged-baseline process below, HQ first stages the precise initial target and then freezes that index; the reviewer performs no stage operation. Outside that exception, a Codex-prepared package or Git writes are not required. If prior content cannot be recovered, report that gap instead of claiming a fix comparison. Do not mistake a patch-text comparison for an actual before/after source comparison.

Finish the whole initial scope and necessary specialist consultation before Codex repairs the complete 🔴/🟡/🟢 Low batch. Partial/interrupted work retains all unchecked obligations and continues with the same owner; no approval from missing evidence. Codex does not interrupt normal investigation with unsolicited inspection requests or force each test edit through another review. On `再レビュー`, resume the same actual parent/child and compare current fixes/affected paths with that owner's previous observed source, findings and requirements. Record HEAD/base and meaningful working-tree/source identity; HEAD alone does not identify mutable uncommitted changes. A changed scope/revision invalidates affected old conclusions. If the prior source is unavailable, recover only what is needed or retain the precise gap; do not invent a prior comparison.

Codex sends short requests and actual user answers/constraints. Claude gathers available facts itself. Mandatory Codex-made diff artifacts, manifests, packet/contract dumps and multiple per-call hash/access handshakes are removed. Optional temporary diffs or narrow supplied evidence remain useful only when normal access fails; honor existing user transmission/access limits and do not shrink scope to hide missing evidence. A supplied helper's success is not actual Claude execution. Standalone requests never start a new layer; an explicitly authorized four-layer run still needs independent `qa -> e2e -> cr -> adv` approvals on its final source snapshot and every required item closed.

### User-authorized staged review baseline

The user has already adopted this staged-baseline method as the default HQ rule for the applicable review/fix cycles. HQ stages only the exact initial review target before the first review, without asking for renewed approval on each run. A contrary explicit instruction takes precedence; an existing-index state that cannot be safely preserved remains pending. This narrow authorization overrides a blanket no-stage rule for that operation; do not ask again for permission already given. It does not authorize commit/push/merge, staging during repairs, staging unrelated/environment/secret files, or changing the separate reverse workflow. A request to update this configuration without staging it is not an instruction to stage these configuration edits.

Before staging, identify the authorized paths/hunks/base/exclusions, actual HEAD, existing index entries/content/modes and working/untracked states. Keep existing staged work and every unrelated index entry unchanged. Do not use `git add .`, unscoped `git add -A`, stash/reset/checkout or an index restore to hide or replace another person's work. Whole-file staging is allowed only if the complete selected content is authorized and cannot overwrite prior staged hunks. An already matching staged target needs no restaging. If a path contains different pre-existing staged and unstaged versions, do not blindly add the full working file: preserve the earlier staged contribution and the whole intended target, or stop with the exact incompatible hunks/paths. Do not silently choose one version or shrink the requested scope. Partial-hunk, binary, unmerged-index or other cases without a proven preservation path stay pending.

A non-destructive separate review index is an optional alternative only when permitted and all HQ/reviewer processes, including every initial and resumed Claude parent/child Git invocation, demonstrably use the same run-local `GIT_INDEX_FILE`. If that propagation cannot be confirmed, hold. The original index must remain byte/content-identical, unrelated entries must stay intact, and the actual alternative index/source identity must be explicit. Do not assume propagation to Claude's tools, change global settings, or present an alternate-index review as an update to the user's real index. If that consistency cannot be demonstrated, hold rather than attempting a destructive workaround.

After the initial target is safely staged, record its actual index identity and scope as the fixed review baseline once per run. Verify the staged paths/content correspond to the intended target; additions/deletions/rename endpoints and initial untracked contents must be represented. Do not restage for each later layer or fix. The first reviewer inspects the baseline with `git diff --cached` against the confirmed base and the actual source. Later layers also inspect current repairs. All reviewers retain their actual reviewed source revision and findings, not index identity alone.

Keep every review fix unstaged and preserve that fixed index. Ordinary `git diff` then shows tracked changes since the initial baseline; `git status` and direct inspection of untracked contents are also required, since plain diff omits newly created fix files. A deletion or rename must not lose either its prior staged state or its new path/content. Compare the fixed index with its recorded identity when returning from repairs; if it changed, do not auto-restore or silently redefine the baseline. Preserve current work, report the break and retain non-approval until a reliable basis is recovered. Same-owner continuation, full first-pass completion, 🔴/🟡/🟢 Low closure, required consultation and all final-snapshot gates remain unchanged.

At handoff, say that approval covers the current working source, while the index still contains the initial review baseline and fixes/new files remain unstaged/untracked. Do not present that index alone as the approved final commit. The human confirms and stages the final contents before committing; HQ does not automatically commit or push.

### Rule loading across continuations

A first-pass owner independently reads the applicable current rules and evidence once. The same parent/child on re-review reuses its retained complete reading of unchanged documents; continuation is not a fresh first pass. Check whether applicable rule/requirement sources changed using metadata or targeted diffs, then read only changed relevant sections and their necessary exceptions. For the governance file, the re-review request may carry the `git hash-object .claude/knowledge/engineering-governance.md` hash that was read (optional; at least 12 hex digits when given), recorded alongside Checked at the first reading; the receiver runs the same command once. If the request carries no hash, the receiver computes it itself and compares it with the hash in its own retained record. A match allows skipping the reread only if the receiver's own retained record holds a complete Checked reading of that hash; otherwise treat it as a first reading. On a mismatch read only the changed sections, or the whole file if they cannot be identified (for example the earlier version was uncommitted). Never reread/resend unchanged source documents merely because a new turn starts. `🟢 Info` items are not part of the retained ledger and are not re-sent. Missing retained context, changed requirements or a concrete evidence gap requires only the necessary permitted recovery; prohibited/unavailable required evidence remains pending. Retained history may contain earlier document text; do not claim it was erased.

Before re-review, Codex relays new test command/case/results with the source revision, exact user answers with their source, and changed constraints once if the owner cannot obtain them directly. A short `再レビューしてください` does not mean omitting these newly available facts. Keep initial-source and current-fix identities, original findings and unresolved questions accessible; do not regenerate unchanged ledgers, full diffs or optional evidence packets on every edit.

### Evidence reuse and concise reporting

Group specialist questions once by responsibility after the necessary boundary trace. For autonomous Claude review, use the registered Sonnet specialist and keep its own model/effort instead of inheriting Adviser’s Opus; the reverse Codex workflow retains its configured models. Reuse the same review-phase consultant for changed or unanswered questions; do not restart it or copy another specialist’s full investigation. React owns UI/state/render, Nest producer/validation/serialization, security trust, and data persistence/retries. Actual required React/Nest review consultation remains distinct from implementation advice; another owner's approval never replaces an independent first-pass check. Reuse neutral unchanged facts with source/revision/owner and Supplied attribution, and reopen only changed, contradicted or genuinely unresolved evidence. Keep real consultation IDs/results and all pending work without broad duplicate investigations.

Show the verdict and changed conclusion first, with one compact complete finding/coverage ledger. On re-review, report newly resolved/open findings and changed coverage, referring to the retained unchanged ledger by ID; preserve every pending item and include required workflow fields. When clean, the native verdict, reviewed-source identity, scope/coverage and required workflow metadata suffice; do not add a no-issue narrative for every checked file. Preserve every 🔴, 🟡 and 🟢 Low finding (`Info` needs no ledger entry), owner, status, cause/rule evidence and action, happy/fail obligations and required metadata; brevity is not a top-N limit. After a snapshot change each layer still renews its approval for the final snapshot. The layer owner re-checks the obligations the fix touched, including callers, shared helpers and tested code it reaches directly or through call paths, and reuses an unaffected obligation only after confirming its earlier evidence is still valid, recording one line `証拠再利用：<ID>, <previous Checked/Executed snapshot_id>, <basis: the changed paths/symbols and how they map to the obligation>`. A test change requires `qa` and `e2e` to re-check all their obligations; a requirement, specification or rule change requires every layer whose obligations cite that source, with the layers decided and the basis recorded. This waives no required check. Do not repeat full diffs, logs, unchanged rules, specialist narratives or the same ledger across output sections. Same-owner continuation can refer to already held unchanged evidence and rules without rereading/resending full sources. Keep native verdicts and important uncertainty; a short request/output never licenses an unverified approval. Claim runtime or usage improvements only from actual execution evidence.

### Adviser consolidation and retained records

For ADV/L2, and the final review response of an already authorized four-layer workflow, show the Adviser-owned consolidated result only. Adviser asks Nest/React about unresolved framework decisions and still obtains every triggered mandatory consultation, even without a pre-existing question. Specialists return scoped evidence to Adviser/the coordinator, not parallel user-facing review reports. Adviser evaluates their answers against current sources, records accepted/rejected advice and reasons, and reports one integrated verdict/finding ledger; do not paste specialist narratives beside it. Preserve every evidenced finding, 🟢 Low item, material uncertainty, and required ownership/evidence datum in that integration.

The coordinator retains original specialist prompts/responses, actual agent IDs, phase/snapshot, source references, important pending items and Adviser reconciliation as audit evidence outside the implementation diff. Consultation does not request implementation edits; preserve available originals and IDs without inventing traces or creating duplicate audit copies. When the user explicitly requests full conversation or HTML records, save the authorized complete record as a separate artifact, rendered deterministically from the retained Codex and Claude logs by script rather than by an LLM (secret redaction is best-effort; the user checks before sharing); distinguish that artifact from the concise final response and never delete originals merely to shorten the reply. Missing records stay marked missing. This does not authorize a new Adviser layer for a standalone CR/QA/E2E request.

### Independent review and reconciliation

First-pass reviewers receive requirements, rules, the actual revision/diff, and relevant code/evidence.
Do not use implementation confidence, conversation summaries, a saved conclusion, or an earlier clean verdict to exclude a check or decide the answer.
Use a fresh review task/context where supported. This instruction does not disable saved memory or guarantee isolation; retain formal project rules.

Implementation-phase consultation and L2 consultation are distinct. The coordinator starts a fresh review-phase specialist task rather than resuming the implementation consultant's conversation as independent review.
Pass neutral facts and source paths. Do not lead with the implementer's preferred conclusion.
After independent inspection, reconcile supplied findings. Retain validated unresolved blockers, confirm disputed imports, and deduplicate tickets rather than mandatory checks.
Convergence intentionally receives original tickets and fix evidence; it does not restart first-pass discovery.
No majority vote overrides a reproducible blocker or a sourced mandatory violation.

## Mandatory framework consultation

Evaluate the following behavior triggers in implementation and first-pass L2 without waiting for the user to name an agent.
Routine or small work still matches. Difficulty, confidence, and file extensions alone are not the gate.

| Changed behavior | Required consultant |
| --- | --- |
| React component/prop/state responsibility, Context/Provider, hooks/effects, async UI, forms/dialogs, query/cache, selector/filter/URL sync, API-to-view mapping | `react-ui-flow` |
| NestJS controller/module/service/DI responsibility, DTO validation/transformation, guard/pipe/interceptor/filter, exception behavior, serialization/producer contract | `nestjs-backend` |

- A UI/API change may need both consultants, with separate questions and scopes.
- Pure text, formatting, styling, generated output, or unrelated-framework changes may be `NOT_APPLICABLE` only when behavior, accessibility and responsibility are unaffected. Check this rather than assuming it from a filename.
- Preserve existing Spring/Vue/security/data/QA routes for their own domains. Do not send unrelated frameworks to React/Nest.
- Consult once per applicable framework, phase, and unchanged evidence set. Batch related questions; reopen only changed or unresolved evidence.
- Consultation is mandatory when triggered; agreement with the advice is not. The owner accepts/rejects advice using source-backed evidence and retains unresolved mandatory obligations.

### Phase ownership

- Implementation: HQ performs bounded intake, then obtains the matched consultant's result before committing to the affected design/edit. HQ owns application edits.
- First-pass L2: Adviser traces the boundary, obtains the matched framework evidence, then makes its scoped judgment. An already proven blocker may be returned early, with consultation and remaining coverage explicitly pending.
- L1.5: `code-quality-reviewer` remains self-contained. It owns local framework/rule checks; cross-layer issues become handoffs, not hidden specialist/L2 runs.
- Convergence: consult only when a supplied ticket or a fix-induced risk needs framework evidence. Return to the same ticket, not a full framework review.
- QA/E2E: retain test-adequacy review ownership. For Codex-implementation/Claude-review workflow, all test execution belongs to Codex. Framework code inspection is not executed verification.

Required consultation continues the already requested task. It is not permission to chain `qa -> cr -> adv -> rev` automatically.
High-risk-only specialist defaults do not suppress the React/Nest behavior triggers above.

### Coordinator handshake

Each delegation contains the applicable principle clauses, phase, revision, trigger, question, scope, and source paths. Do not assume inheritance of the parent's developer prompt, prior file reads, or memory.
An owner may directly call an allowed consultant only if that tool is exposed at runtime. Otherwise return:

```text
SPECIALIST_REQUEST
Owner: <hq-coder | adviser | reviewer>
Phase: <implementation | L2 | convergence>
Specialist: <registered agent name>
Revision: <base/head; relevant uncommitted scope>
Trigger: <behavior and file/symbol>
Question: <bounded decision>
Rules: <source/sections>
Scope: <allowed paths/boundaries>
Evidence checked: <facts, not approval>
Return to: <same owner and unfinished decision>
```

The coordinator must actually invoke the specialist, obtain its result, and resume the same owner. A routing recommendation is not consultation completion.
Keep framework consultants within inspection/advice ownership. For autonomous Claude review this is not a Read/Grep/Glob-only or plan restriction; inherit the user-authorized native mode. The reverse Codex direction retains strict read-only/no-execution. Do not widen OS/Codex/managed permissions, bypass those controls, or pretend a call succeeded.
If the owner lacks a tool to obtain metadata/diffs, return `INPUT_REQUEST` with the exact missing artifact; the coordinator supplies it through an allowed tool. Do not invent a base, diff, or command result.
If spawning is unavailable, record `UNAVAILABLE` and the unchecked obligation. Dependent edits/approval stay pending.

Record `Specialist Usage` for candidate specialists:
- `USED`: actual invocation/reference, assigned scope, returned evidence, and accepted/rejected advice.
- `NOT_APPLICABLE`: checked trigger and concrete exemption.
- `PENDING / UNAVAILABLE`: remaining obligation and cause.
Reading an agent definition, imitating its role, or printing its name is not `USED`.
A completed invocation with insufficient evidence still leaves its review obligation pending; `USED` alone is not approval.

## Evidence and reporting

Write user-facing results in polite, plain Japanese. State the decision first and keep sentences short.
`Checked` means inspected file/content. `Executed` means an observed command run; imported CI evidence must identify its source, revision, command/test, and result.
Never invent a test command, execution, line number, requirement, or original quotation. Suggested verification is labeled not executed.
When a rule source is missing, mark the affected judgment unconfirmed, not the rule violated. Do not block unrelated work solely because an optional document is absent.

Final approval requires complete evidence for the requested layer, completed required consultation, and no unresolved blocker affecting that judgment.
A scoped clean result is not full PR approval. A single-layer approval is valid only for that layer and snapshot, is not four-layer or final approval, and joins a later four-layer run only as Supplied evidence. Confirmed open blockers keep overall merge readiness at `REQUEST_CHANGES`; missing blocking evidence keeps it deferred.

## Enforcement boundary

These are agent instructions. They do not modify company policy, setup scripts, CI parsers, branch protection, or merge automation.
Preserve each role's existing verdict labels. An evidence-only hold in L1.5 or convergence uses that role's existing non-approval status with `Reason: NEEDS_CONFIRMATION`; this withholds approval without asserting a new defect. L2 may use its existing `DEFER` label.
`Review Coverage` is supplementary evidence, not a replacement verdict or CI integration. Unknown/partial statuses must not be interpreted as approval by a downstream consumer; parser integration is outside this change.
Configuration parsing and contract checks do not prove runtime delegation or defect detection. Validate both separately with real task traces and known-bad revisions.
