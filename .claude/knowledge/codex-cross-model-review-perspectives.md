# Codex cross-model review perspectives (evidence-led)

Purpose: improve the **existing Codex L1.5 (`code-quality-reviewer`) and L2+ (`adviser`)** reviews across projects by combining complementary inspection perspectives observed in Codex/Claude review practice. This is not the GuildBoard Actions preflight, not a new review layer, not an automatic cross-model invocation, and not a replacement for the human-adopted Nishiguchi guidelines or project rules.

## Provenance and confidence

- **Project evidence (examples, not universal rules):** GuildBoard `CLAUDE.md` §5-A–I and §6 emphasize design/specification alignment, whole changed-file context, caller/callee impact, affected roles, normal and failure paths. GuildBoard `docs/review/review-prompt.md` emphasizes newly introduced defects, machine-check exclusion, atomicity/side effects, N+1, and rechecking prior findings. Resolve those files from the project when relevant; do **not** require GuildBoard paths or import its architecture/severity into another repository.
- **Published controlled experiment (limited setting):** Xiang et al. (2026), *Cross-Model LLM Code Review: Should you use Claude to review Codex or vice versa?*, 116 LiveCodeBench-style tasks and six model/review pairings; review direction changed measured outcomes. This is not a general benchmark of real-world PR review, and it does not prove exclusive model capabilities. https://arxiv.org/abs/2607.21656
- **Developer experiment (small/confounded):** kunitomo926 (2026), *15個の仕込みバグで比較*, compared four review modes on 15 planted bugs with two runs each; explicit prompting and review scope affected detection. Models, prompts and objectives differ, so do not assign intrinsic advantages to Claude or Codex. https://qiita.com/kunitomo926/items/7dfc85770cf5132f3d1c
- **General empirical caution:** Aðalsteinsson et al. (2025), *Rethinking Code Review Workflows with LLM Assistance*, reports contextual-information, trust and false-positive concerns in a field study. https://arxiv.org/abs/2505.16339
- **Community reports (hypotheses only):** users variously report missed obvious bugs, attention to improbable edge cases, and false-positive claims. These anecdotes conflict; none alone warrants a mandatory rule or severity change. Example discussions: https://www.reddit.com/r/codex/comments/1xfe8kh/ ; https://www.reddit.com/r/claude/comments/1ti1mc3/

**Interpretation:** Review dimensions, not model stereotypes, are portable. Strengthen explicit questions and counterexample checks while preserving narrow ownership, actual source evidence, and existing consultation rules. A finding is never justified by "Claude/Codex usually misses this."

## Two complementary lenses for the same changed contract

| Lens | Main question | Expected concrete evidence |
| --- | --- | --- |
| User/requirement lens (drawn from Claude Actions checklist) | Does this change preserve the intended real user/actor operation across relevant screens, API, state, roles and failure paths? | Actual acceptance/spec clause where available; changed entry point, real caller/consumer, affected role/state, observable outcome |
| Code/invariant lens (drawn from Codex Actions checklist) | Does the implementation introduce a reachable logic error, rule violation, unsafe boundary, duplicate effect, transaction gap, or unbounded work? | Exact diff/code path, guard/filter/DB constraints, action ordering, retry/concurrency behavior, rule source and counterevidence |

Apply both lenses **only within the assigned role's scope**. The implementer's claim and prior verdict are starting context, never proof. Consider a plausible counterexample, then inspect the actual validation/filter/guard or producer that could refute it. Do not turn hypothetical examples into blocker findings.

## Scope-preserving incidental signals and handoffs

A reviewer may **notice** a problem owned by another layer during authorized inspection. Noticing it does not authorize conducting that layer's review, changing the finding's owner, starting a new agent, or asserting that layer's coverage is complete.

- **Owned finding:** The current layer has concrete evidence within its responsibility; report and classify it under that layer's existing verdict rules. Never relabel a local defect as a handoff to force local approval.
- **Incidental cross-layer signal:** When the changed symbol, user-facing copy, event type, or adjacent code directly reveals a possible downstream mismatch, record the observed source and exact question for the proper owner. At most a **bounded exact-reference lookup within existing file/search budgets** may confirm the direct relationship; do not search all tests, reproduce the entire flow, or judge QA/E2E adequacy. No new mandatory cross-layer search is created.
- **Handoff contract:** Keep the existing CR format `Owner/route | Question | Evidence | Required confirmation`. Put the possible impact in `Question`; put actual source revision, path:line, inspected fact and limitations in `Evidence`. Clearly mark `HANDOFF / PENDING` or `UNCONFIRMED` instead of counting it as an owned finding. Preserve specialist-specific handoff formats where required. A confirmed prior/other-layer blocker remains in the shared ledger with its owner and status; do not quietly discard or downgrade it.
- **Verdicts:** A locally complete CR may use its existing `L1.5_APPROVE_WITH_NOTES` when **only explicit other-owner handoffs** remain. This does not close those handoffs or certify overall PR/merge readiness. A missing required **local** check or confirmed local defect keeps CR non-approved; missing required cross-layer evidence remains pending for the coordinator and designated owner.
- **No implicit execution:** Handoff is a record for an already authorized review/verification workflow, not permission to launch ADV, QA, E2E, tests, CI, or a Claude session. The next owner performs its own evidence check and maintains actual invocation records.

### Calibration example: GuildBoard growth-history PR #1006

This is an **example of ownership**, not a universal project rule or proof of any model's inherent ability. Revalidate the relevant source revision before using it as a regression test.

| Observed condition | Owner | Correct layer behavior |
| --- | --- | --- |
| Negative status display copy changed while a directly related Playwright expectation retained the old phrase | `e2e-qa` | CR can relay the exact code/expectation pair if encountered incidentally; **does not** run E2E, perform test-sufficiency review, or create a local CR blocker solely from that pair |
| Two changed files unexpectedly showed executable-bit metadata `100755 -> 100644` | `code-quality-reviewer` | CR checks the diff metadata for paths already under review; flag only an unintended change with a reason, not every permission change as a bug |
| Old status-correction event type also gained "decrease" wording, but documentation coverage was questioned | `adviser` | CR relays the changed event-kind/condition; ADV checks whether the authoritative spec already covers it and whether any update is genuinely required, without inventing a missing rule |

## L1.5 owner: code-quality-reviewer (`cr:`)

Use this focused matrix for **changed functions/components and immediate context**:

| Trigger | Combined check | Boundary / handoff |
| --- | --- | --- |
| Changed local branch, handler, form, hook or mapper | Follow one ordinary use and the highest-risk local fail path: null/empty/unknown, disabled state, stale callback, duplicate interaction, wrong branch or dropped output field | Cross-screen selector/URL/API semantics and true producer reachability -> `adviser` |
| Changed DTO parsing, type narrowing, error handling or Promise chain | Check whether an invalid value crosses the boundary; whether `as`, fallback, catch, Promise aggregation or fire-and-forget hides a meaningful failure | API-wide status/serialization and durability -> `adviser` |
| Changed local loop, query, reuse or component responsibility | Check actual input cardinality, repeated lookup or I/O (including N+1), local responsibility, missing shared predicate/mapper, incorrect helper reuse | Transaction design, multi-instance state, schema and cross-domain ownership -> `adviser` / matching specialist |
| A local project rule or CI result is referenced | Read its applicable clause and exceptions; distinguish confirmed source violation from formatting, linter or typecheck already owned by CI | Do not re-report machine checks; do not pronounce test/E2E adequacy |

Ask "What is the simplest realistic failing input/state here?" as well as "Could this rare edge case actually reach this code?" If the latter lacks evidence, record uncertainty or handoff rather than an invented bug. Preserve existing CR output labels and file/inspection budgets.

## L2+ owner: adviser (`adv:`)

Use this matrix only where **the diff crosses an affected contract/boundary**:

| Trigger | Combined check | Evidence and limits |
| --- | --- | --- |
| API, route, DTO, screen, permission, or requirement change | Compare current acceptance/authoritative design and permission rules with actual method/path/actor/role/request/response and affected producer/consumer | No blanket document scan; locate relevant current files/sections, exceptions, explicit non-goals. Missing authoritative spec = UNCONFIRMED, not invented inconsistency |
| Shared parser, normalizer, resolver, formatter, or fallback changes | Identify directly affected producer/input and consumer contracts, including legitimate uses outside the motivating example. Group uses by distinct contract; compare their before/after behavior with the applicable requirement and specification | Follow affected references within the assigned boundary/budget, not every repository use. Field presence or name resolution can switch a consumer branch while numeric values stay unchanged. A missing producer name in a spec is not itself a violation if its general rule covers that use |
| User-visible wording, state, completion, or recovery changes | Check what the affected operation communicates as a whole: the actual data/state and its affected visible, accessible and notification representations. Check that each representation preserves the intended outcome, permitted next action and relevant uncertainty | Inspect only representations reached by the changed flow. A category label, outcome, API value and accessible description may legitimately differ; compare each with its own contract, not literal string equality. Keep unclear scope as a question, not a required rewrite |
| Changed UI selector, URL, data source, mapper, or shared API consumer | Trace real user input -> selection/filter -> request -> producer response -> mapper -> screen, including affected independent/combined/cleared/URL-restored states and applicable legacy/unknown values | Establish actual reachable producer data. Do not claim a crash based only on a TypeScript type or a mock fixture |
| Authn/authz or data ownership changes | Trace authenticated actor/tenant, resource scope, server guard/service enforcement, forbidden/foreign-resource path and visible response | Handoff precise trust-boundary questions to `sec-arch`; no UI-only authorization claims |
| Write, queue, notification, external side effect or retry change | Trace dependent writes/transaction, uniqueness/conditional update, commit -> dispatch -> handler -> retry/crash recovery; evaluate N+1/scale where affected | For partial writes, pre/post-commit effect gap, idempotency or data growth, consult `data-platform` as evidence requires; do not assume Promise.all cancels work |
| New cross-module or browser flow, changed validation or failure response | Check real-world happy/fail route and which tests/fixtures would expose the changed contract, including a realistic normal path and meaningful failure | Specify required QA/E2E evidence and owner, not run tests or certify their coverage |
| Historical finding or claimed remedy | Compare current source against original failure and disconfirming guards/requirements; explicitly retain, resolve or withdraw with a reason | Keep all existing tickets/owners; `reviewer` owns final fix convergence |

For the two added checks, reuse the existing boundary/coverage record: affected uses or representations, expected versus actual behavior, source and result/pending obligation. Do not add another matrix, report or broad document-reading pass. The owner independently reconciles specialist evidence before judgment.

Do not make every row mandatory for every PR. Preserve triggered mandatory checks and React/Nest specialist consultation **independently**. One representative boundary trace per risk is preferred to repeating CR's local code review. CR may supply known facts but ADV's current-snapshot conclusion is independent.

## Routing and reporting contract

- `review-planner` uses only PR metadata, changed paths/stats and bounded grep to tag likely `spec-contract`, `consumer-regression`, `auth-permission`, `transaction-side-effect`, or `local-quality`. It does not itself read full code, requirements or produce findings; choose the existing first owner.
- CR remains the local reviewer; ADV remains the cross-boundary reviewer. No `ci:` invocation, Claude session, new layer, broader permission or automatic CR->ADV progression follows merely from this document.
- Keep one accountable owner per root cause. Report `path:line`, affected observable behavior or violated mandatory rule, current code evidence, disconfirming evidence checked, smallest correction, and an explicit pending owner when needed. Reconcile current snapshot, old items and applicable project exception before approval.
- Evidence states: `COMPLIANT / NON_COMPLIANT / NOT_APPLICABLE / UNCONFIRMED`. Inspection is `Checked`; only observed runs are `Executed`. Incomplete scope or missing mandatory consultation cannot become approval.
- Evaluate actual improvement on a small recorded set of known review tickets (both missed bugs and false positives). Compare baseline/new rule with **same source and scope**; record correct detection, false positive, wrongly escalated severity, repeated inspection, and cost. Do not claim quality improvement from the added prompt text alone.
