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

Every implementing/reviewing owner reads this contract and the applicable sections of `human-review-patterns.md`, even when invoked directly.
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
- Finding counts are presentation targets only. Never hide a fourth blocker or a third important handoff because a template prefers fewer entries. Group by root cause and keep every evidenced blocker visible.
- A proven blocker permits an early `REQUEST_CHANGES` with `Review Coverage: PARTIAL`; list remaining scope. Do not present this as an exhaustive review or silently discard supplied tickets.
- Zero findings is valid. Do not invent issues, require a quota, or increase severity to appear strict.
- `COMPLETE` means the declared scope and its required checks are covered; it does not guarantee defect-free code or overall PR approval.

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
Keep framework consultants read-only. Do not widen permissions, bypass approval, or pretend a call succeeded to complete the workflow.
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
