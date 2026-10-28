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

## Principle application

Every implementing/reviewing owner independently reads this contract and the applicable sections of `human-review-patterns.md` on first entry, even when invoked directly. Same-owner continuations follow `Rule loading across continuations` below.
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
- Do not cap finding counts or stop after a fixed number. Report every evidence-backed finding within the requested scope, including 🟢 items, ordered by severity. Group the same root cause without dropping distinct impacts or obligations.
- Use `Severity: 🔴 Critical/重大 / 🟡 Important/重要 / 🟢 Minor/軽微` for concrete impact. Severity is separate from status, coverage, and native verdicts; the color does not decide approval or closure. Preserve existing mandatory checks and workflow closure conditions.
- A proven blocker permits an early `REQUEST_CHANGES` with `Review Coverage: PARTIAL`; list remaining scope. Do not present this as an exhaustive review or silently discard supplied tickets.
- Zero findings is valid. Do not invent issues, require a quota, or increase severity to appear strict.
- `COMPLETE` means the declared scope and its required checks are covered; it does not guarantee defect-free code or overall PR approval.

### Autonomous Claude review

These rules apply to standalone Claude review and `codex-claude-review`, not the reverse read-only Codex transport. The user authorized native Claude full access: use the installed CLI's supported `--permission-mode bypassPermissions`, inherit its normal tools, and do not impose plan/fixed-tool restrictions. OS/Codex/managed controls and explicit user limits still take precedence; a denied operation is not permission to bypass another control. Inability to access the real diff, environment/authentication or required source is `確認不能`/non-approval.

Claude reads the applicable project/shared rules, finds the actual review base from the user's request, real PR metadata or project rule, and gets its own Git diff/status/related source. Never assume `main` or a prior verdict. Absent a narrower selection, include staged, unstaged and untracked paths; keep index/worktree changes distinct even when they cancel, and preserve exclusions/secret/ignore policy. Inspect branch changes against the confirmed base when assigned. Continue obtainable work if the base is missing, but do not approve an unknown branch scope. New/deleted/renamed files and actual untracked contents must not disappear from the review.

Native full access and review ownership are separate. Review requests do not ask Claude to implement or edit source/tests; Codex/HQ owns fixes. CR and ADV may run Git/read/search and metadata utilities to inspect evidence, but not application/server/test/lint/typecheck/build/migration programs or repository scripts, including execution by proxy. QA/E2E may choose and run necessary verification within their assigned responsibility and actual environment; record the command, result and source revision. Do not extend CR/ADV's execution prohibition to QA/E2E. Existing normal implementation-side QA tasks retain their authoring ownership.

Keep a recoverable comparison basis during your own inspection: immutable base/HEAD and index blob IDs/modes, plus the reviewed working-tree/untracked contents and path states, including additions, deletions and rename endpoints. Complete retained context or a minimal private temporary source snapshot may preserve mutable bytes. In the user-authorized staged-baseline process below, HQ first stages the precise initial target and then freezes that index; the reviewer performs no stage operation. Outside that exception, a Codex-prepared package or Git writes are not required. If prior content cannot be recovered, report that gap instead of claiming a fix comparison. Do not mistake a patch-text comparison for an actual before/after source comparison.

Finish the whole initial scope and necessary specialist consultation before Codex repairs the complete 🔴–🟢 batch. Partial/interrupted work retains all unchecked obligations and continues with the same owner; no approval from missing evidence. Codex does not interrupt normal investigation with unsolicited inspection requests or force each test edit through another review. On `再レビュー`, resume the same actual parent/child and compare current fixes/affected paths with that owner's previous observed source, findings and requirements. Record HEAD/base and meaningful working-tree/source identity; HEAD alone does not identify mutable uncommitted changes. A changed scope/revision invalidates affected old conclusions. If the prior source is unavailable, recover only what is needed or retain the precise gap; do not invent a prior comparison.

Codex sends short requests and actual user answers/constraints. Claude gathers available facts itself. Mandatory Codex-made diff artifacts, manifests, packet/contract dumps and multiple per-call hash/access handshakes are removed. Optional temporary diffs or narrow supplied evidence remain useful only when normal access fails; honor existing user transmission/access limits and do not shrink scope to hide missing evidence. A supplied helper's success is not actual Claude execution. Standalone requests never start a new layer; an explicitly authorized four-layer run still needs independent `cr -> qa -> e -> adv` approvals on its final source snapshot and every required item closed.

### User-authorized staged review baseline

The user has already adopted this staged-baseline method as the default HQ rule for the applicable review/fix cycles. HQ stages only the exact initial review target before the first review, without asking for renewed approval on each run. A contrary explicit instruction takes precedence; an existing-index state that cannot be safely preserved remains pending. This narrow authorization overrides a blanket no-stage rule for that operation; do not ask again for permission already given. It does not authorize commit/push/merge, staging during repairs, staging unrelated/environment/secret files, or changing the separate reverse workflow. A request to update this configuration without staging it is not an instruction to stage these configuration edits.

Before staging, identify the authorized paths/hunks/base/exclusions, actual HEAD, existing index entries/content/modes and working/untracked states. Keep existing staged work and every unrelated index entry unchanged. Do not use `git add .`, unscoped `git add -A`, stash/reset/checkout or an index restore to hide or replace another person's work. Whole-file staging is allowed only if the complete selected content is authorized and cannot overwrite prior staged hunks. An already matching staged target needs no restaging. If a path contains different pre-existing staged and unstaged versions, do not blindly add the full working file: preserve the earlier staged contribution and the whole intended target, or stop with the exact incompatible hunks/paths. Do not silently choose one version or shrink the requested scope. Partial-hunk, binary, unmerged-index or other cases without a proven preservation path stay pending.

A non-destructive separate review index is an optional alternative only when permitted and all HQ/reviewer processes, including every initial and resumed Claude parent/child Git invocation, demonstrably use the same run-local `GIT_INDEX_FILE`. If that propagation cannot be confirmed, hold. The original index must remain byte/content-identical, unrelated entries must stay intact, and the actual alternative index/source identity must be explicit. Do not assume propagation to Claude's tools, change global settings, or present an alternate-index review as an update to the user's real index. If that consistency cannot be demonstrated, hold rather than attempting a destructive workaround.

After the initial target is safely staged, record its actual index identity and scope as the fixed review baseline once per run. Verify the staged paths/content correspond to the intended target; additions/deletions/rename endpoints and initial untracked contents must be represented. Do not restage for each later layer or fix. The first reviewer inspects the baseline with `git diff --cached` against the confirmed base and the actual source. Later layers also inspect current repairs. All reviewers retain their actual reviewed source revision and findings, not index identity alone.

Keep every review fix unstaged and preserve that fixed index. Ordinary `git diff` then shows tracked changes since the initial baseline; `git status` and direct inspection of untracked contents are also required, since plain diff omits newly created fix files. A deletion or rename must not lose either its prior staged state or its new path/content. Compare the fixed index with its recorded identity when returning from repairs; if it changed, do not auto-restore or silently redefine the baseline. Preserve current work, report the break and retain non-approval until a reliable basis is recovered. Same-owner continuation, full first-pass completion, 🔴–🟢 closure, required consultation and all final-snapshot gates remain unchanged.

At handoff, say that approval covers the current working source, while the index still contains the initial review baseline and fixes/new files remain unstaged/untracked. Do not present that index alone as the approved final commit. The human confirms and stages the final contents before committing; HQ does not automatically commit or push.

### Rule loading across continuations

A first-pass owner independently reads the applicable current rules and evidence once. The same parent/child on re-review reuses its retained complete reading of unchanged documents; continuation is not a fresh first pass. Check whether applicable rule/requirement sources changed using metadata or targeted diffs, then read only changed relevant sections and their necessary exceptions. Never reread/resend unchanged source documents merely because a new turn starts. Missing retained context, changed requirements or a concrete evidence gap requires only the necessary permitted recovery; prohibited/unavailable required evidence remains pending. Retained history may contain earlier document text; do not claim it was erased.

Before re-review, Codex relays new test command/case/results with the source revision, exact user answers with their source, and changed constraints once if the owner cannot obtain them directly. A short `再レビューしてください` does not mean omitting these newly available facts. Keep initial-source and current-fix identities, original findings and unresolved questions accessible; do not regenerate unchanged ledgers, full diffs or optional evidence packets on every edit.

### Evidence reuse and concise reporting

Group specialist questions once by responsibility after the necessary boundary trace. For autonomous Claude review, use the registered Sonnet specialist and keep its own model/effort instead of inheriting Adviser’s Opus; the reverse Codex workflow retains its configured models. Reuse the same review-phase consultant for changed or unanswered questions; do not restart it or copy another specialist’s full investigation. React owns UI/state/render, Nest producer/validation/serialization, security trust, and data persistence/retries. Actual required React/Nest review consultation remains distinct from implementation advice; another owner's approval never replaces an independent first-pass check. Reuse neutral unchanged facts with source/revision/owner and Supplied attribution, and reopen only changed, contradicted or genuinely unresolved evidence. Keep real consultation IDs/results and all pending work without broad duplicate investigations.

Show the verdict and changed conclusion first, with one compact complete finding/coverage ledger. On re-review, report newly resolved/open findings and changed coverage, referring to the retained unchanged ledger by ID; preserve every pending item and include required workflow fields. When clean, the native verdict, reviewed-source identity, scope/coverage and required workflow metadata suffice; do not add a no-issue narrative for every checked file. Preserve every 🔴–🟢 finding, owner, status, cause/rule evidence and action, happy/fail obligations and required metadata; brevity is not a top-N limit. Do not repeat full diffs, logs, unchanged rules, specialist narratives or the same ledger across output sections. Same-owner continuation can refer to already held unchanged evidence and rules without rereading/resending full sources. Keep native verdicts and important uncertainty; a short request/output never licenses an unverified approval. Claim runtime or usage improvements only from actual execution evidence.

### Adviser consolidation and retained records

For ADV/L2, and the final review response of an already authorized four-layer workflow, show the Adviser-owned consolidated result only. Adviser asks Nest/React about unresolved framework decisions and still obtains every triggered mandatory consultation, even without a pre-existing question. Specialists return scoped evidence to Adviser/the coordinator, not parallel user-facing review reports. Adviser evaluates their answers against current sources, records accepted/rejected advice and reasons, and reports one integrated verdict/finding ledger; do not paste specialist narratives beside it. Preserve every evidenced finding, 🟢 item, material uncertainty, and required ownership/evidence datum in that integration.

The coordinator retains original specialist prompts/responses, actual agent IDs, phase/snapshot, source references, important pending items and Adviser reconciliation as audit evidence outside the implementation diff. Consultation does not request implementation edits; preserve available originals and IDs without inventing traces or creating duplicate audit copies. When the user explicitly requests full conversation or HTML records, save the authorized complete record as a separate artifact; distinguish that artifact from the concise final response and never delete originals merely to shorten the reply. Missing records stay marked missing. This does not authorize a new Adviser layer for a standalone CR/QA/E2E request.

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
- QA/E2E: retain test ownership. Framework code inspection is not executed verification.

Required consultation continues the already requested task. It is not permission to chain `cr -> qa -> adv -> rev` automatically.
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
A scoped clean result is not full PR approval. Confirmed open blockers keep overall merge readiness at `REQUEST_CHANGES`; missing blocking evidence keeps it deferred.

## Enforcement boundary

These are agent instructions. They do not modify company policy, setup scripts, CI parsers, branch protection, or merge automation.
Preserve each role's existing verdict labels. An evidence-only hold in L1.5 or convergence uses that role's existing non-approval status with `Reason: NEEDS_CONFIRMATION`; this withholds approval without asserting a new defect. L2 may use its existing `DEFER` label.
`Review Coverage` is supplementary evidence, not a replacement verdict or CI integration. Unknown/partial statuses must not be interpreted as approval by a downstream consumer; parser integration is outside this change.
Configuration parsing and contract checks do not prove runtime delegation or defect detection. Validate both separately with real task traces and known-bad revisions.
