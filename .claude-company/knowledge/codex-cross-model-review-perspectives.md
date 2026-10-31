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
| Changed UI selector, URL, data source, mapper, or shared API consumer | Trace real user input -> selection/filter -> request -> producer response -> mapper -> screen, including affected independent/combined/cleared/URL-restored states and applicable legacy/unknown values | Establish actual reachable producer data. Do not claim a crash based only on a TypeScript type or a mock fixture |
| Authn/authz or data ownership changes | Trace authenticated actor/tenant, resource scope, server guard/service enforcement, forbidden/foreign-resource path and visible response | Handoff precise trust-boundary questions to `sec-arch`; no UI-only authorization claims |
| Write, queue, notification, external side effect or retry change | Trace dependent writes/transaction, uniqueness/conditional update, commit -> dispatch -> handler -> retry/crash recovery; evaluate N+1/scale where affected | For partial writes, pre/post-commit effect gap, idempotency or data growth, consult `data-platform` as evidence requires; do not assume Promise.all cancels work |
| New cross-module or browser flow, changed validation or failure response | Check real-world happy/fail route and which tests/fixtures would expose the changed contract, including a realistic normal path and meaningful failure | Specify required QA/E2E evidence and owner, not run tests or certify their coverage |
| Historical finding or claimed remedy | Compare current source against original failure and disconfirming guards/requirements; explicitly retain, resolve or withdraw with a reason | Keep all existing tickets/owners; `reviewer` owns final fix convergence |

Do not make every row mandatory for every PR. Preserve triggered mandatory checks and React/Nest specialist consultation **independently**. One representative boundary trace per risk is preferred to repeating CR's local code review. CR may supply known facts but ADV's current-snapshot conclusion is independent.

## Routing and reporting contract

- `review-planner` uses only PR metadata, changed paths/stats and bounded grep to tag likely `spec-contract`, `consumer-regression`, `auth-permission`, `transaction-side-effect`, or `local-quality`. It does not itself read full code, requirements or produce findings; choose the existing first owner.
- CR remains the local reviewer; ADV remains the cross-boundary reviewer. No `ci:` invocation, Claude session, new layer, broader permission or automatic CR->ADV progression follows merely from this document.
- Keep one accountable owner per root cause. Report `path:line`, affected observable behavior or violated mandatory rule, current code evidence, disconfirming evidence checked, smallest correction, and an explicit pending owner when needed. Reconcile current snapshot, old items and applicable project exception before approval.
- Evidence states: `COMPLIANT / NON_COMPLIANT / NOT_APPLICABLE / UNCONFIRMED`. Inspection is `Checked`; only observed runs are `Executed`. Incomplete scope or missing mandatory consultation cannot become approval.
- Evaluate actual improvement on a small recorded set of known review tickets (both missed bugs and false positives). Compare baseline/new rule with **same source and scope**; record correct detection, false positive, wrongly escalated severity, repeated inspection, and cost. Do not claim quality improvement from the added prompt text alone.
