# Engineering Governance

## Authority and provenance

The user adopts Nishiguchi's review policy as constitutional engineering principles for this configuration, for both implementation and review.
Company-wide adoption is not confirmed. This file is an operational interpretation, not Nishiguchi's original wording.

- Preserve the existing principles and examples in `human-review-patterns.md` in this same knowledge directory.
- Do not invent quotations, add new preferences under Nishiguchi's name, or silently rewrite an authoritative source.
- Separate source principle, project-specific rule, and new operational safeguard in any proposed policy change.
- When an original guideline is supplied, retain its source/revision and compare this interpretation against it. Do not claim original-source conformance without reading it.
- Platform instructions, security controls, and explicit project requirements retain their actual precedence. A material conflict with the adopted principles requires `NEEDS_CONFIRMATION`; do not silently weaken either side.

Within this configuration's engineering rules, principles and explicit project contracts take priority over agent convenience, token targets, sample/file budgets, and duplicate-output reduction.
Project rules specify concrete behavior. Do not impose a project's Suspense, ORM, audit, or API convention on unrelated projects without an applicable source.

## Principle application

Before implementation or a scoped review, read the applicable sections of `human-review-patterns.md` and the minimum relevant project rules.
The current operational baseline includes responsibility separation, meaningful exception boundaries, type safety, focused refactoring, and design-document alignment.

Use this compact evidence chain for each triggered principle:
`source/section -> changed responsibility or invariant -> checked evidence -> result`

- Prefer the smallest design-correct change, not a short patch that preserves a known rule violation.
- Do not add catches, casts, abstractions, or unrelated cleanup merely to make a change pass.
- Distinguish a sourced mandatory rule violation from an optional improvement. Neither runtime impact nor style preference alone establishes the other's severity.
- Report `COMPLIANT`, `NON_COMPLIANT`, `NOT_APPLICABLE`, or `UNCONFIRMED` only for the scope actually checked.
- For a defect, include the reachable precondition, causal code path, consequence, and verification method. Label code inspection separately from execution.
- For a mandatory rule violation, cite the applicable rule and the concrete mismatch; do not invent a runtime failure to justify it.
- If budget is insufficient, split the remaining scope or record it as pending. Sampling and an unanswered specialist request never establish full approval.

## Mandatory framework consultation

A framework agent is a read-only consultant. HQ owns edits; the requested review owner owns its judgment. No consultant may rewrite source or approve the whole PR.

The coordinator must evaluate these triggers on implementation tasks and first-pass L2 review, without requiring the user to name an agent.
Use task paths/symbols and the owner's targeted intake or boundary trace. A file extension or installed dependency alone is insufficient.

| Matching behavior change | Required consultant |
| --- | --- |
| React component/prop/state ownership, Context/Provider, hooks/effects, async UI, forms/dialogs, query/cache, selectors/filter/URL synchronization, API-to-view mapping | `react-ui-flow` |
| NestJS controller/module/service/DI responsibility, DTO validation/transformation, guards/pipes/interceptors/filters, exception behavior, API serialization or producer contract | `nestjs-backend` |

- Matching routine work also triggers consultation. Do not wait until the owner says the work is difficult or high-risk.
- A UI/API change may require both consultants, with distinct frontend and backend questions.
- Pure text, formatting, styling, generated output, or unrelated-framework changes may be `NOT_APPLICABLE`; state the concrete reason. A component's changed meaning or responsibility is not a naming-only exemption.
- Retain Spring/Vue/security/data/QA routes for their existing scopes. Do not send them to React/Nest by analogy alone.
- Consult once per applicable framework, phase, and unchanged evidence set. Batch related questions; reopen only changed or unresolved evidence.

### Phase and layer ownership

- Implementation: HQ performs a bounded intake, requests the matching consultant before committing to a behavior-affecting design/edit, then accepts or rejects advice with evidence. HQ remains the only implementation owner.
- First-pass L2: Adviser first traces the relevant boundary, then obtains matching framework evidence before its final scoped judgment. Adviser still owns risk ordering and cross-layer conclusions.
- L1.5: keep `code-quality-reviewer` self-contained. Local framework/project-rule checks remain its responsibility. Cross-layer concerns become `L2+ Handoff`; do not secretly launch L2 from `cr:`.
- Convergence: consult only for supplied tickets or fix-induced risks that require framework evidence. Do not restart a full framework review.
- QA/E2E: retain existing test ownership. Framework inspection is not a substitute for executed tests.

Framework consultation within an already requested implementation/L2 task is continuation of that task, not permission to chain `cr -> qa -> adv -> rev` automatically.
Existing high-risk-only specialist defaults do not suppress the matching React/Nest behavior triggers above.

### Coordinator handshake

The coordinator includes the applicable principle clauses, this phase's trigger contract, and source paths in every delegation. Do not assume custom agents inherit the parent's developer prompt, conversation, or memory.

An owner may call an allowed consultant directly when the runtime exposes that tool.
Otherwise it returns this request to the coordinator, without a completed implementation/review verdict:

```text
SPECIALIST_REQUEST
Owner: <hq-coder | adviser | reviewer>
Phase: <implementation | L2 | convergence>
Specialist: <react-ui-flow | nestjs-backend>
Revision: <base/head SHA; include uncommitted scope when relevant>
Trigger: <changed behavior and file/symbol>
Question: <one bounded framework decision>
Rules: <applicable source/sections>
Scope: <allowed paths/boundaries>
Evidence checked: <facts, not an approval claim>
Return to: <same owner and unfinished decision>
```

The coordinator must actually spawn the named specialist, await its result, and resume the same owner with the evidence.
Keep reviewers read-only; lack of an Agent tool is handled through the coordinator, not by adding write permissions or pretending delegation happened.
If spawning is unavailable, report `UNAVAILABLE` and retain the unchecked obligation. Do not silently replace it with owner self-approval.

Final handoff records `Specialist Usage` for each candidate:
- `USED`: actual agent invocation/reference, assigned scope, returned evidence, and how the owner used it.
- `NOT_APPLICABLE`: inspected trigger and reason.
- `PENDING` / `UNAVAILABLE`: remaining obligation and cause.

A proposed route, a read agent-definition file, or owner imitation of a specialist is not `USED`.

## Independent review input

First-pass reviewers receive requirements, applicable rules, the immutable revision/diff, and relevant code/test artifacts.
Do not use the implementer's confidence, conversation summary, or a prior clean verdict to exclude risk or decide the answer.
Use a fresh review task/context where supported; do not assume this setting disables saved memory or guarantees context isolation.

Framework review is also independent of implementation consultation. Reuse source locations and observed facts, not an implementation-phase approval as L2 proof.
After independent inspection, reconcile prior findings. Retain validated unresolved blockers and explicitly resolve conflicting claims. Deduplicate tickets, not mandatory checks.
No majority vote overrides a reproducible blocker or a sourced mandatory rule violation.

## Scope of enforcement

This is an agent instruction contract. It does not modify company policy, branch protection, CI merge gates, or client runtime behavior.
Configuration checks do not prove agents actually delegated or found defects. Validate routing with real task traces and defect detection with known-bad revisions.
