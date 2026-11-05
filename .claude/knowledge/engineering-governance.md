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

Every implementing/reviewing owner independently reads the applicable contract and `human-review-patterns.md` sections on first entry, even when invoked directly. Exact section delivery may use `Preloaded rule delivery` below. Same-owner continuations follow `Rule loading across continuations` below.
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

Claude and Codex owners may satisfy first-entry reading for exact sections delivered by the generated `engineering-review-core`, `engineering-react-rules`, and `engineering-nest-rules` skills. This is a user-approved delivery rule, not a new quotation from Nishiguchi. Each owner must actually receive the skill text in its own context and retain its included section names and source SHA-256 as `Rules loaded` evidence. A frontmatter declaration alone is not delivery evidence or whole-document reading.

The coordinator checks source identity against the active project's current rules and supplies permitted digest/metadata evidence; SHA-256 here is not a Git blob hash. Missing, changed, unverified or conflicting sources require targeted original reading, including exceptions, or an exact evidence request. Claude reviewers do not run shell/hash commands for this check. Project-local configured sources take precedence; never replace a project-specific document with a shared summary without checking its identity. Existing read-at-entry instructions remain mandatory for applicable sections not actually injected. Codex source checks use only tools allowed by the active platform/workflow; a skill never grants shell access. Owners without verified delivered sections retain their normal original-reading requirements.

Reuse unchanged, verified injected sections on the same-owner continuation. Read only missing/changed relevant sections and project design rules; preloading does not expand routing/planning/consultation scope, permissions, or approval authority. Missing mandatory evidence stays pending. Regenerate both Claude profiles and Codex `.agents/skills` with `python3 -I -B tools/sync_engineering_preloads.py --write` after a source change and check without `--write` before publishing. Existing deployments need setup again to link new skill directories, followed by a fresh session. Keep Codex outputs in repository `.agents/skills`; verify actual delivery in a fresh owner rather than assuming discovery or injection. Do not infer runtime compliance or token savings from static configuration checks.

### Claude role-scoped intake

For Claude owners, record resolved original paths/versions, complete injected/read sections and missing obligations in the existing `Rules loaded` record. A complete active role definition already injected into your own system prompt needs no self-Read when its correspondence to the current original path/version is verified through invocation/source evidence. The same applies to exact rule sections actually delivered in your own context. A role name, skills declaration, parent's summary or another owner's reading is insufficient. If identity, delivery or retained text is missing, recover only the necessary original clauses, including exceptions; keep dependent approval pending. Do not reread a verified definition merely to confirm your role or format the result.

Use the Claude platform contract. Codex routing/model/implementation instructions in `.codex/AGENTS.md` are not a default Claude-child reading assignment. Resolve a workflow beside that file without loading its full text. Explicit project/common instructions and directly applicable cross-platform clauses still apply; read any such required originals and exceptions. In `codex-claude-review`, the coordinator reads the complete workflow once; reviewers independently read the complete original sections selected by `review_entry.role_sections`, plus any triggered cross-references. Keep the actual path/version and section keys, not a parent-written replacement contract. A narrower delivery never waives permissions, approval conditions, handoffs or the eleven-field result.

In a restricted Claude review, the coordinator uses the workflow's process-local auto-compaction setting to limit accumulated input rather than disabling prompt caching. After compaction, the same owner checks retained source identities, coverage/evidence references, all open findings/questions/handoffs, specialist IDs/adoption, rule versions/read sections and verification gaps against the existing records. A compaction summary alone is not proof of reading, closure or approval. Recover only necessary missing originals with permitted tools; preserve full native logs and pending obligations. Compaction is not a new reviewer or an output/turn limit, and savings require observed request usage.

On a rule-source change, the authorized coordinator compares retained old and current originals and supplies their identities, changed complete sections with exceptions, and added/removed obligations once. Each owner reads the applicable changed originals and required cross-references, reusing verified unchanged retained sections. A new whole-document hash alone is not a reason to reread every section. Missing old text or an uncertain change boundary requires permitted recovery and remains pending; never freeze outdated rules or substitute a parent summary. Report setup facts, including missing links, only from current inspection.

For Claude native Read, specify both `offset` and `limit` from the first call when the exposed schema supports them. Start with at most 100 lines or the smaller complete required section; use fewer lines for long-line prose. This is a delivery chunk, not a review-scope or whole-file waiver. Retain visible line ranges once and continue at the next unread line until every required section and exception is complete. If output is truncated, recover only missing or uncertain ranges with a smaller limit. If one required line cannot fit, request a permitted narrow original excerpt from the coordinator and keep the obligation pending. Read limits do not authorize Bash, Python helpers or repository scripts in restricted reviews. Batch independent Read/Glob/Grep requests only when their combined results are known to fit the tool and response limits; otherwise return one bounded source chunk at a time. Plan bounded reads of complete relevant sections; on truncation count only visible complete ranges and recover missing/uncertain ranges with context, not the whole previous document. Reuse your own verified readings throughout the pass and same-owner continuations. Do not create another manifest or duplicate report. All non-injected mandatory rules, design sections and exceptions remain required. Explicit project whole-file requirements still apply, including changed-file reading; reading a test does not transfer QA/E2E adequacy ownership to L2.


### First-pass rule intake and bounded reading

Before substantive implementation/review judgment, each owner records `Rules loaded` once: exact injected sections, personally read original sections, applicable project design/rule sections including exceptions, and missing obligations. Verify the supplied source identity. Parent reading, an agent-definition summary or another rule is not a substitute for required non-injected originals. Read known absolute paths directly; an empty Glob result does not prove absence. Request exact unavailable evidence and keep dependent conclusions `UNCONFIRMED`; independent work may continue.

Review every requested changed hunk and affected function/responsibility with the necessary immediate callers/callees. Do not require whole-file, whole-test or whole-design-document reading by default. Expand only when needed to establish impact or an exception, and record why. Explicit user/project whole-file requirements still apply. `COMPLETE` means the assigned obligations were checked, not that every source file was read in full; retain uninspected obligations. Same-owner continuations reuse unchanged verified readings and add only missing/changed evidence.

For `codex-claude-review`, disable the internal server-side `advisor` with `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` on initial launch and resume, and inspect actual parent/child tool metadata. This does not disable the registered `adviser` Agent or required consultation. Unknown runtime tools or missing evidence never become approval. The workflow defines the scoped environment, log check and stop behavior; do not edit managed/global settings to force a pass.

### Core rules for Claude preload

This is the user-approved operational core, not Nishiguchi's wording or proof of company-wide adoption. Preserve the pinned source and the separate human-review reference. Explicit project rules and platform/user controls retain their precedence. Do not invent quotations or export one project's conventions to another project.

- Responsibility: identify the actual owner/layer and a concrete mixed responsibility before requesting a boundary change. Reuse existing validated concepts, but do not merge contracts merely because their fields match.
- Exceptions: catch for recovery, error translation, cleanup or meaningful context. Preserve unexpected failures and their cause. Do not remove every catch or accept an empty catch.
- Types: validate untrusted boundaries and narrow types. An annotation/cast is not runtime validation; a justified framework assertion is not automatically a defect. Check the actual producer and nearest guard before asserting reachability.
- Intake: before substantive judgment, record injected/read/missing rule sections and applicable project design exceptions once. For Claude native Read, use explicit `offset` and `limit` from the first call when supported, starting with at most 100 lines (less for long lines); retain visible ranges and continue without gaps until required sections and exceptions are complete. This chunk size never waives whole-file rules or authorizes scripts; missing/truncated evidence stays pending. Read required missing originals; an empty Glob is not absence. Inspect changed responsibilities and necessary surrounding code, expanding with a reason rather than requiring full files by default. User/project whole-file requirements and all pending obligations remain.
- Scope/design: make the smallest design-correct change, including required boundary repair. Read applicable project rules and their exceptions. A sourced mandatory violation needs no invented crash; an optional preference is not a blocker.
- Evidence: within your layer, connect requirement/rule -> actor/input and operation -> success/failure path -> observable result. Derive expectations independently of the patch/mocks; check a normal control and counterevidence. QA/E2E also connect fixture identity, entry point and assertion, and identify what mocks bypass. Separate reachable defects, mandatory violations, verification gaps and optional observations. Keep source/revision and all open IDs until owner-confirmed closure; Info never closes a mandatory obligation.
- Ownership: implementation owns edits; CR checks local correctness; QA/E2E own test adequacy; ADV owns boundary consistency. HQ and first-pass L2 obtain triggered React/Nest evidence, even from unchanged dependencies when their behavior is needed to judge the change. File presence alone is not a trigger or exemption. Consultants answer their assigned boundary; implementation advice is not independent L2 evidence. Planners route metadata only. No automatic layer chain or extra delegate.
- Execution: the active workflow and actual tool restrictions decide execution permissions. In codex-claude-review, all Claude reviewers/consultants stay review-only and Codex owns commands, tests, fixes and CI. A normal Claude session may execute an explicit user request with available permissions. Never bypass restrictions through another agent.
- Review gates: normal source review judges code and test adequacy, not CI passage. Missing CI/test runs alone are NOT_RUN notes, not DEFER. Require execution only for an explicit user/project/active-workflow obligation or a concrete material question that cannot be resolved from source; name that dependency. Before escalating a question, cite the current obligation or reachable risk and how different answers change the verdict. Optional enhancements create no approval gate; do not seek user acceptance merely to close them. Only the original owner may withdraw an existing unsupported gate with reasons; retain its history and every genuine open obligation.
- Completeness: reconcile claims with checked paths, applicable rules/exceptions and actual consultation. A correct handler does not prove failures reach it; producer output does not prove consumer state. Scope claims to evidence. Severity and budgets waive no mandatory checks or closure. Read applicable source-index, supplement, phase and closure rules not already injected. Single-layer approval is not merge approval.

- Re-review delivery (codex-claude-review only): after full initial review and batch fixes, send the scoped fix delta and planned verification results together once to the same parent/child. Include command/cases/exit/source, limits, and a permitted test/script reference or necessary assertions plus import/load target. Reuse unchanged evidence. Failed, waived, unavailable, not-run or partial checks keep their reasons and pending obligations; they are not success or closure. Evidence-backed earlier questions/user-directed continuations are explicit exceptions. Never require full manifests/logs or weaken read-only and layer boundaries.

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

### OPS-1: Release, operability and data-lifecycle boundaries

This is a user-approved operating supplement, not a Nishiguchi quotation. Apply only a row whose trigger the change reaches, within the assigned role; without a trigger the row is NOT_APPLICABLE with a concrete reason. It is not a checklist for every PR.

| Area | Trigger | Question to answer from source or supplied evidence | Default owner |
| --- | --- | --- | --- |
| Rollout and compatibility | Change to a public/internal API contract, persisted schema/data, event/message/queue payload, or config/flag consumed by other versions, clients or workers | During a mixed-version deploy (old client/new server, old worker/new producer) and after rollback, can either side break? Are migration/flag ordering (expand/contract) and a rollback path stated? | Adviser; data-platform for migrations |
| Observability and operability | New/changed async work, retry, background job, external integration or error handling that could fail without a caller seeing it | Can an operator detect and diagnose the failure from existing logs/metrics/alerts and an existing meaningful identifier? Is the failure not swallowed, and is no sensitive data logged? Do not demand new metrics where an existing signal suffices | Adviser |
| Performance and capacity | New/changed list, query, loop, batch or endpoint whose input or data volume can grow | Is there a concrete bound (pagination/limit/index/batch size) for the reachable cardinality? No speculation without a concrete failure path | Adviser; data-platform for query/persistence |
| Dependencies and supply chain | Manifest, lockfile, CI, tooling or runtime image changes | Is a new dependency necessary versus an existing one? Do transitive/lockfile changes match the intent? Check version pinning, install scripts, and license/maintenance for a new package | Adviser; sec-arch for known-vulnerability or trust questions |
| Personal/sensitive data lifecycle | New or changed personal/sensitive field, log, export, analytics or third-party transfer | Are classification and minimization defined, who can read it, is there a retention/deletion path, and is it kept out of logs, errors and URLs? | sec-arch; Adviser for the boundary |

- Classification: a missing concrete project rule or an unverifiable fact is UNCONFIRMED, not a blocker. Findings default to Should; a Blocker needs a mandatory project rule or a concrete reachable failure path. Never invent cardinality, traffic or compliance requirements.

### XREV-1: Cross-model review calibration lenses

This is a user-approved operating supplement, not a Nishiguchi quotation or a claim about either model. The lenses in the table are triggered-only, but `HND-1` below is a standing reporting and approval rule that applies in every review of the affected layers, not a triggered lens. Evidence base: one PR comparison (n=1) recorded in `docs/cross-model-review-guildboard-pr1024.md`. Apply only a lens whose trigger the change reaches, within the assigned layer; otherwise it is NOT_APPLICABLE. These are inspection aids, not a per-PR checklist, and add no reviewer layer, approval gate, automatic chain, tool permission or execution right. An unobservable aspect stays UNCONFIRMED with an exact weighted handoff (HND-1), never an assumed pass or defect.

| Layer | Trigger | Lens |
| --- | --- | --- |
| ALL | A side effect (notification, cache update, event, audit) is verified only through a mock | A mock proves the call, not delivery. Trace whether a real destination/consumer exists in the reached flow; a missing destination with source evidence is an owned finding (HND-1 rule 1), otherwise UNCONFIRMED with an exact weighted handoff |
| ALL | Project rules (e.g. CLAUDE.md) may bear on the layer's judgment | Read the applicable rule sections at intake, including QA/E2E. A grep-only conclusion is reported as "not found by grep", never as proven absence |
| ALL | A claim rests on knowledge that was not executed | Cite an authoritative primary source (spec, official docs, source) or keep it UNCONFIRMED; neither inflate nor understate it |
| ALL | Severity and Blocker/Should class differ | Give a one-line reason |
| QA | Lock/serialization claim | Check lock target binding, transaction vs root client, and call order |
| QA | Newly added side effect | A failure-propagation test (rejects with the same error, no swallowed failure) |
| QA | A value must not change; a mutation can fail | Preservation/negative controls for the unchanged value; a failed mutation produces no success-side effect |
| E2E | Evidence mixes HTTP, UI and mocked controllers | Separate the three. An earlier-branch rejection (401/403/404/428) is not proof of a new rejection branch; do not infer authentication (401) from authorization cases |
| E2E | Operator and target differ | Distinguish operator vs target subject |
| E2E | Declaring a coverage gap | Read the affected E2E files fully first |
| CR | Raw SQL replaces an ORM call | Compare accepted input forms (e.g. ID notations the ORM/controller already accept) |
| CR | A new error status or audit vocabulary | The status must reach the user-visible message mapper; audit values must match their consumer's normalizer |
| CR | Changed behavior near comments or duplicated rules | Comments contradicting the change; the same invariant duplicated across services |
| CR | Missing render destination or spec/openapi update | With path:line evidence of the mismatch, report an owned finding (HND-1 rule 1) naming who confirms/fixes it; do not decide the other layer's design. Hand off only what the layer cannot establish, with a weight (HND-1 rule 2) |
| ADV | An invariant is claimed | Enumerate every writer of that value (APIs, admin paths, seeds, jobs) and compare with the authoritative permission/spec. "Pre-existing" does not exempt a path the PR's invariant relies on |
| ADV | A rule applies to data that already exists | Apply OPS-1 rollout to existing data (legacy rows, resubmission) |
| ADV | A new row lock is added | Consult data-platform on lock compatibility, including FK checks from audit inserts, and lock order against other flows |
| ADV | A state change has consumers | Check consumer-side effects (notification target, cache invalidation) |
| ADV | A product decision is involved (e.g. privacy widening, pre-notice) | Put it to the user as a separate question |
| ADV | Project documents conflict | Record both sources and the precedence evidence; keep NEEDS_CONFIRMATION unless source precedence resolves it |

**HND-1: Handoff weight and evidence-first reporting (part of XREV-1).** User-approved 2026-11-05. Findings, including `🟢 Low`, are what get fixed and re-reviewed; no one executes a handoff (there is no automatic layer chain), so a handoff must carry real weight. These rules are always on; they apply to the standalone layers and to `codex-claude-review` / `claude-codex-review`. They add no reviewer layer, tool permission or automatic chain, keep the eleven `Workflow Result` fields (`handoffs` stays one field; its items gain a `weight` key) and keep the Info rules (Info is not a finding).

1. **Evidence becomes a finding.** When a layer has concrete source evidence (path:line plus the inspected fact) of a defect or a contract/spec mismatch, it reports an owned finding (minimum `🟢 Low`; severity per the evidence) and names the confirming/fixing owner (review layers stay read-only; the implementation owner edits), even if the natural fix lies in another layer's area (for example a missing render destination, a missing spec/openapi update, a missing test). The finding is tracked, fixed and re-reviewed. The layer still does not decide other layers' judgments (product/API design, authorization matrices, test strategy): it reports the evidenced mismatch and names who confirms or fixes it.
2. **A handoff is reserved for what the layer cannot establish from its own evidence** (it needs execution, another layer's judgment or a product decision). Every handoff carries a weight `🔴` / `🟡` / `🟢` meaning the consequence if left unresolved, and a one-line reason. Show the weight in the Question cell (or a `weight` key in the workflow `handoffs` item). A weight is not lowered without evidence: the original owner may lower it only by closing or withdrawing the handoff with closure evidence.
3. **Low cap interaction.** The cap of 5 `🟢 Low` per pass stays. Evidenced mismatches beyond the cap remain as `🟢`-weighted handoffs (tracked), never as Info. Classification is made once from the evidence at first report: an evidenced defect or mismatch is never Info, so this overflow is not a promotion of Info; a `Low` that newly arises from fix changes is a fresh classification with `Origin: FIX_INDUCED` (existing Origin and re-review cap rules unchanged).
4. **Approval gating.** While any open handoff has weight `🟡` or `🔴`, the layer reports no clean result: no `L1.5_APPROVE` / `L1.5_APPROVE_WITH_NOTES`, no L2 `APPROVE` for that layer, and workflow `decision: APPROVE` is not allowed. Use the layer's existing non-approval label with Reason `NEEDS_CONFIRMATION` where the handoff is an evidence hold. Only `🟢`-weighted open handoffs, with no open finding (including `🟢 Low`, see `Minor findings: Low and Info`), allow `L1.5_APPROVE_WITH_NOTES` or a single-layer workflow `APPROVE`, as before. Final multi-layer approval still requires every handoff closed. Never lower a `🔴`/`🟡` handoff to `🟢` or Info to avoid this gate.

- Not adopted: these lenses do not claim that either model is generally better, and a single comparison does not establish a model trait. Do not turn the lenses (not HND-1) into mandatory per-PR items; revalidate against the source revision before reuse. HND-1 rests on one comparison only (n=1, PR #1024): Codex's CR put the missing Toaster and the not-updated openapi into handoffs only, while Claude's CR reported them as `🟡` findings. It is a user decision about weight, not proof of a model trait.

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

### Review objective and evidence

Judge requirements, changed behavior and mandatory rules. Reading volume, findings, tokens and approval speed alone do not prove quality. Use the existing coverage/finding record, without per-read reports.

- State one objective: actor/operation, acceptance/rule, actual before/after, layer and exclusions. Validate it independently. Distinguish the reported symptom from this patch's effect; an already-correct baseline scenario alone cannot prove ticket resolution. Missing/conflicting acceptance keeps dependent judgment unconfirmed. Routing-only planners do not trace code.
- Map required originals/exceptions, normal/fail paths, counterevidence and consultations to it. Count only actually delivered complete ranges as read; a request, heading, hash or command is not reading evidence. Reuse one retained copy after identity verification. Preserve independent first readings, explicit whole-file rules and applicable QA/E2E/React/Nest duties.
- Expand for a named acceptance, mandatory clause or evidenced contradiction whose answer can change judgment. Consultants own their question and dependencies, not the whole PR or another layer's adequacy audit. Request the precise missing fact. Optional new contracts are not required fixes/gates without an applicable obligation. Retain genuine dependent uncertainty; recover necessary evidence without routine approval requests.
- Ground findings in reachable conditions, filters/pagination, counterevidence and consequence. Rule violations need their clause/exception, not an invented crash. Separate introduced/pre-existing defects and explain impact on current acceptance/approval or separate ownership. Reconcile disposition with the native verdict. Reclassification needs an evidence/requirement/scope rationale, not an inherited label; preserve all open IDs and owner-confirmed closure.
- QA/E2E assess whether assertions distinguish defective/repaired behavior, retain normal controls, and state mock exclusions. A mocked child does not cover its real failure. Request a targeted before/after comparison only when diagnostically useful and authorized; unrun comparisons remain reasoning/UNCONFIRMED. Narrow handoffs to missing assertions or fixture/runtime facts and decision impact, each with an XREV-1 HND-1 weight; a gap evidenced by source is an owned finding, not a handoff. Keep own dependent gaps local, other-layer work pending, and all native fields/stricter workflow gates; do not repeat full audits or claim merge approval.
- Compare matched known-defect, normal and hold cases using pre-fixed hidden expectations, real runs and independent assessments. Supplied known findings test retention, not new discovery. Evaluate misses, unsupported findings, scope errors, mandatory completion and verdict reasoning; count every parent/reviewer/consultant and elapsed time. Missing/unmatched/unrun evidence is inconclusive. Static tests or savings cannot offset quality failure. This is separately authorized validation, not an automatic new PR gate.

### Mandatory UI consistency and task usability

These are user-approved quality obligations, separate from Nishiguchi's original principles. For a user-facing change, check **both UI consistency and task usability** within the changed operation and its directly affected shared consumers. This includes visible wording, styling, layout and API/error/state changes that alter the experience. A backend-only change with no user-facing effect may be NOT_APPLICABLE with a concrete reason. Existing framework, role and execution restrictions remain in force.

Before editing or judging the change, identify the user/role, goal, entry point, supported viewport/input mode, expected result and relevant failure/recovery path. Choose the project's approved components, tokens, terminology and interaction rules as the consistency baseline. Reuse a comparable sound pattern when no explicit rule exists and record why; do not spread a known usability defect merely to match nearby screens.

| Required axis | Checks within the affected operation |
| --- | --- |
| UI consistency | Shared components/tokens, color meaning, typography, spacing, alignment, action placement, terms/icons, form/error/status presentation, responsive layout and visible/accessible names agree with the applicable baseline. |
| Task usability | The user can discover the next action, predict its effect and understand loading/success/failure. Check meaningful labels and clickable areas, keyboard/focus operation, text legibility, input retention/correction, error recovery and permitted cancel/back/undo where relevant. Prevent duplicate or accidental consequential actions without adding needless steps or confirmation dialogs. |

Use the following heuristic questions where the change triggers them: visible status; familiar user language; control and escape; consistency; error prevention; recognition instead of memory; efficient operation; focused content; understandable recovery; useful contextual help. These are inspection aids, not a requirement to add every feature to every screen. Check the actual user/role, permissions, empty/loading/disabled/success/error states and directly affected viewport/input modes; do not expand into every product screen or a fixed scenario count.

Code-observable checks for those questions (inspection aids; apply only the rows the change triggers, and keep unobservable aspects UNCONFIRMED rather than guessing):

| Question | Observation point in source or supplied evidence |
| --- | --- |
| Is status visible? | Each async branch (pending/success/error) has a user-visible representation. |
| Can the user escape or undo? | Destructive or consequential actions have confirmation/undo as appropriate, and duplicate submission is prevented. |
| Can the user recover from an error? | On failure the user's input is retained, and the message states the cause and the next action. |
| Is it consistent? | Shared components/tokens are used, and terms/labels for the same operation match across screens. |
| Is it operable? | Interactive elements use appropriate element types (button/a/input), have accessible names, are keyboard-reachable with visible focus, and have usable target size. |
| Is it readable and localizable? | Text legibility follows the baseline tokens (size/contrast) where defined; user-visible strings go through the project's i18n/copy mechanism when one exists, without hard-coded concatenated sentences; unobservable rendering stays UNCONFIRMED. |

These rows translate the questions into checks; they do not prove human comfort, and unobserved rendering/interaction stays UNCONFIRMED under the evidence rules below. A reviewer (CR/ADV) treats HQ's reached-state list as supplied evidence, not as the review scope: independently derive the reachable states from the requirement and source, and report any state the list omits.

Evidence and judgment:
- Assess UI and UX separately in the existing coverage record: expected baseline/task -> inspected source or observed behavior -> result and precise missing evidence. Reuse COMPLIANT / NON_COMPLIANT / NOT_APPLICABLE / UNCONFIRMED; do not create parallel reports for each consultation.
- Source and comparable components can establish structural/contract facts. Static screenshots can establish only the visible state and viewport shown. For rendered appearance or interaction claims that source cannot resolve, inspect attributable candidate screenshots/browser or authorized interaction evidence for the named state, user and input mode. A screenshot cannot prove clicking, keyboard operation, recovery or task completion. Automated selectors passing does not prove discoverability or human comfort.
- Keep observed defects and sourced mandatory violations distinct from heuristic hypotheses and personal taste. AI role-play, personas or an AI's quick completion are not human-user research. Do not claim human ease, satisfaction or a universal optimum without relevant observations; uncertain preference or friction remains a bounded hypothesis. Human feedback is needed when choosing between designs whose usability is not established by the available evidence, not as a blanket new gate for every change.
- Missing material evidence for an owned UI/UX acceptance condition remains UNCONFIRMED; state the exact dependency and request only the needed authorized evidence. An unrun browser check alone is NOT_RUN, not a new unconditional approval gate. Never treat an unobserved axis as compliant or invent a defect to avoid uncertainty.

Ownership within existing roles:
- HQ defines both axes, implements the smallest coherent improvement, obtains triggered framework advice and owns authorized verification. Before editing, list the states the changed operation can actually reach (e.g. loading/empty/disabled/success/error/duplicate submit/back navigation; omit unreachable ones) and reconcile that list after implementation so reviewers verify the same set.
- CR checks local consistency, applicable UI rules and concrete local interaction defects. Cross-screen/task/producer questions retain exact evidence and go to ADV or QA/E2E; CR does not become a UX, architecture or E2E audit.
- ADV owns the affected user task and cross-boundary UI/UX acceptance. It obtains matched React/Vue evidence where triggered, reconciles applicable standards and retains dependent uncertainties. It does not certify usability from a code-only or screenshot-only pass.
- React/Vue consultation checks the supplied UI baseline, affordances, accessible interaction and reached state/render flow. It remains read-only and does not run browsers/tests or grant whole-PR approval.
- QA/E2E owns test adequacy and the evaluation of supplied browser/interaction evidence within its actual permissions. Verify named UI/UX criteria; do not substitute subjective redesign commentary or perform unrequested execution.

Visible UI/copy/styling changes cannot use the non-user-facing formatting exemption to skip these obligations or matched framework consultation. Unchanged verified evidence remains reusable; no automatic new reviewer, full review chain, product-wide UX inventory, tooling permission or test environment is introduced.

References: Jakob Nielsen, [10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), 1994 / reviewed 2024; W3C WAI, [Understandable controls and consistency](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o1-understandable/), 2021 (supplemental guidance, not a claim of WCAG conformance); Rosala and Moran, [Synthetic Users](https://www.nngroup.com/articles/synthetic-users/), 2024. The user adopts the above scoped operating rules; these sources do not prove this AI review workflow's effectiveness.

### Scope, budgets, and stop conditions

- Token/file targets bound each slice, not the definition of correctness. Preserve all triggered mandatory checks in the coverage record.
- On a budget limit, return inspected/pending paths, remaining obligations, and the next same-layer slice. The coordinator may continue that requested layer; do not start another review layer without authorization.
- Do not cap finding counts or stop after a fixed number. Report every evidence-backed 🔴/🟡 finding and every `🟢 Low` finding within the requested scope, ordered by severity (the `Low` limit and `Info` are defined in the next minor-findings bullet). Group the same root cause without dropping distinct impacts or obligations.
- Use `Severity: 🔴 Critical/重大 / 🟡 Important/重要 / 🟢 Minor/軽微` for concrete impact. Severity is separate from status, coverage, and native verdicts; the color does not decide approval or closure. Preserve existing mandatory checks and workflow closure conditions.
- Minor findings are `🟢 Low` or `🟢 Info`. `Low` is a finding: it has an ID, owner and status, is tracked, fixed and re-reviewed like any finding, and counts toward approval and closure. A layer reports at most 5 `Low` per review pass (initial or re-review), highest impact first. `Info` is not a finding: no ID, no ledger entry, no tracking, no fix, no re-review, and it never blocks approval; write each as one concise line or omit it. Minor observations beyond the 5 `Low` become `Info`, lowest impact first, except that an evidenced defect or contract/spec mismatch is never `Info`: it stays a tracked `🟢`-weighted handoff (XREV-1 HND-1 rule 3). An item classified `Info` stays `Info`: never raise or re-label it as `Low` (not on re-review, not to fill the 5-`Low` limit, not because fewer than 5 `Low` exist). A `Low` arises only from a fresh, evidence-backed classification as `Low`; a new `Low` found on a re-review is allowed as a new finding, counts within the 5 per pass, and stays subject to any re-review cap the workflow defines (for example `rereview_cap`/`NEW_UNRELATED` in `claude-review.yml`). A mandatory-rule violation is never `Info`. Never lower a 🔴/🟡 finding, question, handoff or missing mandatory evidence to `Low`/`Info` (or drop it) to avoid an approval condition; reclassification does not satisfy any approval or closure condition. Existing closure statuses such as `reviewer_confirmed_fixed` and `reviewer_withdrawn` are unchanged. **Approval-label boundary (CR and ADV, standalone and in workflows):** with only `Info` remaining (no open finding, no open handoff) the layer returns its clean label, `L1.5_APPROVE` / `APPROVE`; `Info` is one concise line (omitted in the MD workflows per `md-review.md`), never tracked, never blocking. `L1.5_APPROVE_WITH_NOTES` (CR only) means: local scope complete, no open finding (🔴/🟡/🟢 `Low`), and the only remaining items are open `🟢`-weighted handoffs that CR has explicitly assigned with evidence to another layer (HND-1); L2 has no notes label, and its `APPROVE` coexists with `🟢` handoffs only as its Merge Judgment rules allow. **Any open `🟢 Low` finding, including one whose action label is `DEFER`, allows no approval-class label** (`L1.5_APPROVE`, `L1.5_APPROVE_WITH_NOTES`, `APPROVE`): the layer uses its existing non-approval label (`L1.5_REQUEST_CHANGES` / `REQUEST_CHANGES`). The `DEFER` action label expresses only fix priority/timing within the repair cycle; the item stays open until reviewer-confirmed closure or evidenced withdrawal. Classification is made once from the evidence at first report; an evidenced defect or mismatch is never `Info`, and a `Low` that newly arises from fix changes is a fresh classification with `Origin: FIX_INDUCED`. The convergence `reviewer` tracks only supplied `Low` items (and 🔴/🟡) and does not carry `Info`.
- A proven blocker permits an early `REQUEST_CHANGES` with `Review Coverage: PARTIAL`; list remaining scope. Do not present this as an exhaustive review or silently discard supplied tickets.
- Zero findings is valid. Do not invent issues, require a quota, or increase severity to appear strict.
- `COMPLETE` means the declared scope and its required checks are covered; it does not guarantee defect-free code or overall PR approval.

### User-directed execution permissions

This is a user-approved operational rule, not a quotation from the human review guidelines.

Autonomous review without an explicit execution request does not start typecheck, lint, build, tests, Playwright, CI or other verification commands.

For `Workflow: codex-claude-review`, Claude and its review subagents inspect sources, fixed Git diffs and supplied evidence. Codex owns application/verification execution, test creation, CI operations and fixes. The MD review contract permits fixed read-only Git MCP and explicitly listed Backlog reads; it never permits arbitrary Bash or source edits. A message cannot expand an existing restricted session. Use a newly configured one-shot invocation for the MD transport.

When the user explicitly requests execution in a normal Claude Code session, the main Claude session or an authorized implementation/verification owner may perform those actions with its available permissions. If an existing restricted session cannot execute them, use a separate normal session. Do not treat this direct request as an autonomous review or an automatic Codex-to-Claude review.

### Autonomous Claude review

Standalone Claude review remains source/metadata inspection only; no application/test/build/CI execution without a separate execution request.

For explicitly active `codex-claude-review` and `claude-codex-review`, the 2026-11-03 user-approved `.codex/workflows/md-review.md` contract replaces the earlier prompt transport, automatic layer progression and final human-only commit procedure. Resolve it beside the selected workflow and apply its complete assigned originals/exceptions. User-selected layers only; no default chain. Source/test edits and all verification execution stay with the implementation platform. Receivers independently inspect Git diff and actual sources; Claude uses a fixed read-only Git MCP, not Bash. The host appends actual native responses to MD; Info is omitted entirely. Keep actual base/HEAD, index/worktree/untracked contents and modes, prior source, all Low IDs/questions/handoffs, complete phase coverage, required consultation and eleven Workflow Result fields. Missing data stays pending.

Each Claude print invocation ends after its current review. Resume its actual same-phase parent/child only after batch fixes and evidence are ready. Do not leave Claude AI running or use model calls/heartbeat/sleeping agents while waiting for implementation, Local-ci or Codex. Reverse Codex rounds remain fresh read-only execs. A name, launch acknowledgement, CLI success or MD word Approve is not actual owner approval. Check native logs/real delegation, full coverage and source correspondence.

Store the shared MD under an already ignored .codex/.claude path or an external home .codex folder, without adding .gitignore or .git/info/exclude entries. Retain previous findings and actual responses; the implementation owner only appends fix candidates/evidence. The selected reviewers alone close or withdraw their findings. Final selected approvals precede implementation-side Local-ci, then the actual Codex ci-reviewer, then a scoped draft PR. The user alone marks Ready for review. Applicable existing rules/managed permissions retain precedence; report concrete conflicts rather than bypassing controls.

### User-authorized staged review baseline

The explicitly active MD workflow in `.codex/workflows/md-review.md` preserves the initial index and supersedes this initial-stage default for that workflow only. Its final reviewed-content commit/draft-PR step is user-authorized; standalone review/fix cycles retain the following rules.

The user has already adopted this staged-baseline method as the default HQ rule for the applicable review/fix cycles. HQ stages only the exact initial review target before the first review, without asking for renewed approval on each run. A contrary explicit instruction takes precedence; an existing-index state that cannot be safely preserved remains pending. This narrow authorization overrides a blanket no-stage rule for that operation; do not ask again for permission already given. It does not authorize commit/push/merge, staging during repairs, staging unrelated/environment/secret files, or changing the separate reverse workflow. A request to update this configuration without staging it is not an instruction to stage these configuration edits.

Before staging, identify the authorized paths/hunks/base/exclusions, actual HEAD, existing index entries/content/modes and working/untracked states. Keep existing staged work and every unrelated index entry unchanged. Do not use `git add .`, unscoped `git add -A`, stash/reset/checkout or an index restore to hide or replace another person's work. Whole-file staging is allowed only if the complete selected content is authorized and cannot overwrite prior staged hunks. An already matching staged target needs no restaging. If a path contains different pre-existing staged and unstaged versions, do not blindly add the full working file: preserve the earlier staged contribution and the whole intended target, or stop with the exact incompatible hunks/paths. Do not silently choose one version or shrink the requested scope. Partial-hunk, binary, unmerged-index or other cases without a proven preservation path stay pending.

A non-destructive separate review index is an optional alternative only when permitted and all HQ/reviewer processes, including every initial and resumed Claude parent/child Git invocation, demonstrably use the same run-local `GIT_INDEX_FILE`. If that propagation cannot be confirmed, hold. The original index must remain byte/content-identical, unrelated entries must stay intact, and the actual alternative index/source identity must be explicit. Do not assume propagation to Claude's tools, change global settings, or present an alternate-index review as an update to the user's real index. If that consistency cannot be demonstrated, hold rather than attempting a destructive workaround.

After the initial target is safely staged, record its actual index identity and scope as the fixed review baseline once per run. Verify the staged paths/content correspond to the intended target; additions/deletions/rename endpoints and initial untracked contents must be represented. Do not restage for each later layer or fix. The first reviewer inspects the baseline with `git diff --cached` against the confirmed base and the actual source. Later layers also inspect current repairs. All reviewers retain their actual reviewed source revision and findings, not index identity alone.

Keep every review fix unstaged and preserve that fixed index. Ordinary `git diff` then shows tracked changes since the initial baseline; `git status` and direct inspection of untracked contents are also required, since plain diff omits newly created fix files. A deletion or rename must not lose either its prior staged state or its new path/content. Compare the fixed index with its recorded identity when returning from repairs; if it changed, do not auto-restore or silently redefine the baseline. Preserve current work, report the break and retain non-approval until a reliable basis is recovered. Same-owner continuation, full first-pass completion, 🔴/🟡/🟢 Low closure, required consultation and all final-snapshot gates remain unchanged.

At handoff, say that approval covers the current working source, while the index still contains the initial review baseline and fixes/new files remain unstaged/untracked. Do not present that index alone as the approved final commit. The human confirms and stages the final contents before committing; HQ does not automatically commit or push.

### Rule loading across continuations

A first-pass owner independently reads the applicable current rules and evidence once. The same parent/child on re-review reuses its retained complete reading of unchanged documents; continuation is not a fresh first pass. Check whether applicable rule/requirement sources changed using metadata or targeted diffs, then read only changed relevant sections and their necessary exceptions. Use source identity supplied by the authorized coordinator or already accessible metadata. Restricted Claude reviewers never run a hash/Git command; request missing identity evidence or inspect necessary originals with permitted tools. A supplied Git blob hash and a source SHA-256 are different kinds of evidence and must not be compared as if identical. Matching identity permits reuse only for complete sections actually read/injected and still retained by this owner; omitted sections remain unread. On a mismatch read only the changed sections, or the whole file if they cannot be identified (for example the earlier version was uncommitted). Never reread/resend unchanged source documents merely because a new turn starts. `🟢 Info` items are not part of the retained ledger and are not re-sent. Missing retained context, changed requirements or a concrete evidence gap requires only the necessary permitted recovery; prohibited/unavailable required evidence remains pending. Retained history may contain earlier document text; do not claim it was erased.

For Claude review, interrupted initial work, a next slice and specialist-result integration continue the same actual owner; they are not new first passes or post-fix reviews. Retain parent/child IDs, phase, effective tool restrictions and the existing coverage/finding record once. The same role name in a new Agent call does not resume that owner. Send only the continuation reason and new evidence, including changed source/rule identity and specialist originals/IDs; reuse retained readings and preserve every open obligation. If secure resumption or necessary retained context is unavailable, report the precise gap and recover only what is permitted; do not silently start replacement owners or loop retries. Preserve the active workflow's secure-restart exceptions and independent first owners for new phases. This continuation rule does not change the reverse `claude-codex-review` fresh-round contract.

Before re-review, Codex relays new test command/case/results with the source revision, exact user answers with their source, and changed constraints once if the owner cannot obtain them directly. A short `再レビューしてください` does not mean omitting these newly available facts. Keep initial-source and current-fix identities, original findings and unresolved questions accessible; do not regenerate unchanged ledgers, full diffs or optional evidence packets on every edit.

### Batched re-review evidence

For `codex-claude-review` only, the default sequence is complete initial review, batch all fixes, perform the necessary planned verification, then send the fix delta and verification results together once to the same parent/child. Do not split routine delivery into fix-only requests and later result-only followups, or restart review after each source/test edit. The readiness condition is that planned results are available, including failures, not that every test passed. This does not change the reverse `claude-codex-review` contract.

Include the scoped staged/unstaged/untracked fix delta and actual source identity, exact user answers with source and constraints, actual command/cases/exit code/verified source, and results with their limits. Make the test/script reference or the necessary assertions and import/load target available within Claude's permitted Read scope at the same time. Case names and PASS labels alone do not establish what was checked. If a verifier is outside the permitted scope, provide only a narrow permitted reference or the necessary excerpts and target correspondence; do not open an excluded reports directory or transmit unrelated logs. Claude evaluates Supplied execution evidence and never runs the verifier.

A short request with narrow references/excerpts is sufficient. Reuse known unchanged evidence and rules; do not require a giant manifest, full diff/test bodies, repeated unchanged documents, or per-call hash rituals. Keep exact source identity without repeating optional packaging.

When verification was explicitly waived, unavailable, failed, not run or partially interrupted, preserve `NOT_RUN / FAILED / PARTIAL` as applicable, the reason and every pending obligation. Never translate those states into execution success or finding closure. An earlier reviewer decision may be needed to answer a question, or an explicit user instruction may require an earlier continuation. Record such evidence-backed exceptions and remaining work separately from normal batched delivery. Same-owner resume, current-snapshot approval, independent QA/E2E obligations, and single-layer handoffs remain unchanged.

### Evidence reuse and concise reporting

Group specialist questions once by responsibility after the necessary boundary trace. For autonomous Claude review, use the registered Sonnet specialist and keep its own model/effort instead of inheriting Adviser’s Opus; the reverse Codex workflow retains its configured models. Reuse the same review-phase consultant for changed or unanswered questions; do not restart it or copy another specialist’s full investigation. React owns UI/state/render, Nest producer/validation/serialization, security trust, and data persistence/retries. Actual required React/Nest review consultation remains distinct from implementation advice; another owner's approval never replaces an independent first-pass check. Reuse neutral unchanged facts with source/revision/owner and Supplied attribution, and reopen only changed, contradicted or genuinely unresolved evidence. Keep real consultation IDs/results and all pending work without broad duplicate investigations.

For same-owner Claude fix re-review, keep one compact impact mapping in the existing request/ledger: finding or changed obligation -> changed hunk/responsibility -> affected callers/consumers, tests and rules -> verification and remaining gaps. The reviewer independently validates this mapping against the actual delta and prior checked scope, expanding when evidence requires it. This is not a new report or a replacement for independent first-pass coverage. Retain unchanged pending IDs with accessible original questions/evidence instead of re-investigating them; new evidence or changed dependencies reopens them. Preserve all mandatory test/specification/rule-change rechecks and every open item.

Reopen the same review-phase specialist with question IDs, prior checked scope, relevant changed hunks and new verification/rule evidence. Do not send the whole PR or another specialist's narrative by default. The specialist still inspects its owned boundary and counterevidence, and requests additional affected context when needed. Mandatory initial consultation and changed/unanswered obligations remain; an unresolved product decision without new evidence is retained, not researched repeatedly.

For `codex-claude-review`, before returning a re-review finding, its owner checks Origin against the earlier ID or before/after evidence. Under the existing role definitions, distinguish a defect introduced by a fix from a pre-existing defect related to its scope/consumers; scope overlap alone does not prove causation. A newly classified Low needs its obligation/evidence without relabeling an existing Info. Keep uncertain classification explicit and every required finding pending. The coordinator may request correction of a concrete inconsistency, but does not add a routine classification-only round or overwrite the owner's judgment. Existing Origin categories, caps and closure rules remain unchanged.

For Claude L2, request the triggered consultation as soon as the minimal actual boundary, relevant rules, phase/snapshot and responsibility-specific questions are known. Do not finish a second framework investigation or prove a defect before asking. Prefer foreground Agent calls and await their actual replies in the same run; when the exposed Agent schema supports `run_in_background`, use `false`. Keep role model/effort and tool restrictions unchanged. If direct consultation is unavailable, return all known `SPECIALIST_REQUEST` items together; the coordinator obtains the replies and returns their accessible originals/IDs together once to the same Adviser. An available permitted completion notification/wait is preferable to status polling. Do not add a tool, global setting, sleeping agent or heartbeat loop just to wait. If completion cannot be obtained, preserve IDs, partial evidence, the exact missing capability and pending obligations; do not claim integration or approval.

The coordinator and Adviser treat a launch acknowledgement or “waiting for replies” as unfinished work. Receive actual results, inspect their evidence, then integrate once. Do not repeatedly request launch confirmation, reinsert already accessible replies or prompt for integration while the same consultation is still running. Recover an inaccessible original once when necessary; retain original prompts/replies, actual IDs and accepted/rejected advice with reasons. The coordinator relays the owner's verdict, changed conclusions and remaining items without narrating the complete report again. Required output sections and Workflow Result fields may refer to the one retained ledger; none of its open obligations is dropped.

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
| React component/prop/state responsibility, Context/Provider, hooks/effects, async UI, forms/dialogs, query/cache, selector/filter/URL sync, API-to-view mapping, React user-facing UI consistency, styling/copy and task usability | `react-ui-flow` |
| NestJS controller/module/service/DI responsibility, DTO validation/transformation, guard/pipe/interceptor/filter, exception behavior, serialization/producer contract | `nestjs-backend` |

- A UI/API change may need both consultants, with separate questions and scopes.
- Non-user-facing formatting/generated output or unrelated-framework changes may be `NOT_APPLICABLE` only when behavior, accessibility, responsibility and user-facing UI/UX are unaffected. Visible copy/styling still follows `Mandatory UI consistency and task usability` and matching framework consultation. Check the actual effect rather than the filename.
- Preserve existing Spring/Vue/security/data/QA routes for their own domains. Do not send unrelated frameworks to React/Nest.
- Consult once per applicable framework, phase, and unchanged evidence set. Batch related questions; reopen only changed or unresolved evidence.
- Consultation is mandatory when triggered; agreement with the advice is not. The owner accepts/rejects advice using source-backed evidence and retains unresolved mandatory obligations.

### Phase ownership

- Implementation: HQ performs bounded intake, then obtains the matched consultant's result before committing to the affected design/edit. HQ owns application edits.
- First-pass L2: Adviser traces the boundary, obtains the matched framework evidence, then makes its scoped judgment. An already proven blocker may be returned early, with consultation and remaining coverage explicitly pending.
- L1.5: `code-quality-reviewer` remains self-contained. It owns local framework/rule checks; an evidenced cross-layer mismatch is an owned finding naming the confirming/fixing owner (XREV-1 HND-1), and only what CR cannot establish becomes a weighted handoff, never a hidden specialist/L2 run.
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
Keep framework consultants within inspection/advice ownership. In `codex-claude-review`, consultants inherit the review-only CLI restrictions and request command evidence from Codex. A standalone session retains its actually authorized tools without transferring implementation ownership to a consultant. The reverse Codex direction retains strict read-only/no-execution. Do not widen OS/Codex/managed permissions, bypass those controls, or pretend a call succeeded.
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

For `codex-claude-review` single-layer results, apply the workflow's `review_gates.handoffs`, `response_contract.acceptance` and `md-review.md` approval/result-consistency rules. With complete current-snapshot local coverage, required evidence/consultation, no local findings (including Low), questions or unchecked obligations, and an accepted native verdict, the owner reports `decision: APPROVE` even when independent other-layer handoffs remain open, provided every open handoff is weighted `🟢` (XREV-1 HND-1); an open `🟡`/`🔴` handoff prevents a clean result and the owner uses its existing non-approval label with Reason `NEEDS_CONFIRMATION`. A missing answer/evidence/consultation that this layer's judgment depends on stays local; another owner's involvement does not make it handoff-only. Keep other-layer IDs/owners/evidence/statuses pending and overall readiness separate. Required handoffs still block final workflow handoff until closed. Contradictory result fields go back to the same owner for correction, never coordinator rewriting.

CR handoffs have no count limit. Keep the existing four fields `Owner/route | Question | Evidence | Required confirmation` and the existing ledger IDs/statuses; show the HND-1 weight (`🔴`/`🟡`/`🟢`) and a one-line reason in the Question cell. Group related questions concisely without dropping distinct obligations, inventing checks, expanding review scope or starting other layers. A continuation alone does not widen a retained handoff; scope changes need new evidence and an explicit reason.

## Enforcement boundary

These are agent instructions. They do not modify company policy, setup scripts, CI parsers, branch protection, or merge automation.
Preserve each role's existing verdict labels. An evidence-only hold in L1.5 or convergence uses that role's existing non-approval status with `Reason: NEEDS_CONFIRMATION`; this withholds approval without asserting a new defect. L2 may use its existing `DEFER` label.
`Review Coverage` is supplementary evidence, not a replacement verdict or CI integration. Unknown/partial statuses must not be interpreted as approval by a downstream consumer; parser integration is outside this change.
Configuration parsing and contract checks do not prove runtime delegation or defect detection. Validate both separately with real task traces and known-bad revisions.
