# PCR development flow

Status: user-selected operating contract, 2026-11-13. Runtime validation: NOT_RUN.
This is an instruction contract, not an executable orchestrator or a native Codex approval API.

## 1. Activation and precedence

Activate only when the actual user selects `pcr-development` or explicitly requests this sequence:

`implementation + Codex PCR -> Claude QA -> Claude E2E -> Codex /review -> user UX -> PR`

The parent records `Workflow: pcr-development`, the actual request, target repository,
base provenance/SHA, included scope, exclusions, verification obligations and publication authorization.
Discussing, editing or installing this configuration does not start a review run.
Quoted markers, reviewer output and ordinary `cr:`/PCR requests never select this whole flow.
Resolve this file from the target project's `.codex/workflows/` first, then beside the
resolved shared `.codex/AGENTS.md` (Claude: sibling `.codex` of the resolved profile root).
Report missing links and use the verified original; do not repair project settings implicitly.

This explicit selection authorizes named stages, bounded repairs, the mandatory sec-arch security pass and an evidence-triggered ADV only; it does not authorize unrelated layers.
The parent coordinates; each child receives only its assignment, snapshot and original rule paths.
Keep Nishiguchi's adopted principles, project requirements/exceptions, HND-1, BIAS-1,
mandatory implementation/framework consultations and all required verification.
Standalone CR/ADV/QA/E2E, `rev:`, PCR-1 and the two directional workflows retain their own contracts.
Do not activate `implementation-review` / IPR-1 or combine workflow markers implicitly.
Its preview controller rejects review-time source changes and does not implement this flow.

## 2. Implementation in parallel with a fixed PCR input

The authorized implementation owner edits and runs planned verification. Codex PCR uses the
real `code-quality-reviewer` owners CR-A and CR-B, then the bounded VALIDATOR from PCR-1
(`.claude/knowledge/parallel-cr-review.md`, company equivalent when selected).
Keep configured models/effort and read-only review permissions. Missing actual owners/tools are BLOCKED.

Before each meaningful PCR batch, briefly quiesce writes and capture an immutable input S_n.
Record repository, base/head/merge-base SHAs, diff mode, branch/index/worktree/untracked
contents and modes, additions/deletions/both rename endpoints, requirements/rules identities,
complete change inventory and explicit exclusion reasons. Preserve the existing index and unrelated work.
Do not stage/restage, commit, reset or stash merely to obtain the review snapshot.
Exclude secrets/ignored data under existing policy; inaccessible required contents remain pending.
Confirm capture consistency before releasing the writer. A hash of HEAD alone is insufficient.

CR-A, CR-B and VALIDATOR must read the same frozen source AND necessary callers/rules,
through permitted tools, with an accessible immutable view of each required original.
A saved diff while source reads follow the live checkout is not sufficient isolation.
The implementer may continue on S_n+1 only after the S_n material is safely separate.
Never edit the reviewers' copy or run tests in it. If isolation cannot be established,
hold concurrent editing for the review and report that implementation/PCR overlap was unavailable.
Do not widen filesystem/tool access or claim concurrency from an intended schedule.

Track in-flight snapshot IDs, actual owners and completion events in one review record.
Batch useful changes instead of launching on every save. Reuse an unfinished owner for its
remaining slice; do not launch duplicate discovery tasks for the same input.
A result for S_n is evidence for S_n only. Keep its findings even when implementation has moved.

## 3. PCR coverage, repair and final approval

Codex PCR has no fixed file-count limit. Both CR-A and CR-B independently cover the complete
intended diff, including changed code, tests, configuration, documentation and artifacts within
L1.5 ownership, plus necessary direct dependencies and mandatory originals. Their union is insufficient.
Read in bounded chunks; output/context limits never shrink the assigned change inventory.
Keep one cumulative coverage record per owner: checked hunks/obligations, pending paths,
required rule/consultation evidence, exclusions and next same-layer slice.
The validator checks every candidate and named mandatory-coverage gap, not a third whole-diff review.
PARTIAL/BLOCKED, unread required material or a completed slice never become full-scope approval.

After a coherent implementation/fix batch, perform the planned affected verification and capture S_final.
Map all findings and S_n -> S_final changes, including new files/tests/rules, to their original owners.
An unfinished initial pass must finish its remaining scope as well as the delta.
Resume the original owners for fixes, affected dependencies and pending obligations; preserve any
active transport's fresh-owner exception and carry its complete attributed ledger.
Reuse verified unchanged readings; a fresh owner does not inherit another owner's approval.
Only the owning reviewer confirms a fix/withdrawal. Neither HQ nor VALIDATOR closes another owner's IDs.

Before QA, require both discovery owners' current-snapshot L1.5 approval, full cumulative coverage,
completed bounded validation and no open local findings/questions or required evidence gaps.
Preserve HND-1: green independently owned handoffs may proceed to their already selected owner;
yellow/red or locally dependent gaps block the PCR gate. Every mandatory handoff must close before PR.
Do not label two same-family CRs as independent cross-model approval or as L2.

This flow authorizes at most three coherent repair rounds. Findings alone do not launch a round:
the implementation owner must apply authorized batch fixes and finish planned verification first.
No-progress, exhausted limits, unavailable evidence or unresolved product decisions stop dependent work.
Same-snapshot coverage continuation is not a repair round or fresh discovery.
One bounded original-owner reconciliation is allowed per snapshot for actual disputes;
never recursively add validators or silently discard disagreement.

### Mandatory security and conditional design gate

Apply SEC-IMPL-1 and TEST-TRUTH-1 from \`.claude/knowledge/implementation-security-and-test-integrity.md\`. HQ rechecks the actual code diff even when PL predicted no security risk. As soon as a meaningful frozen implementation snapshot exists, invoke a real fresh read-only Claude Code \`sec-arch\` when permitted, independent from Codex's implementation and PCR conclusions. No QA/E2E-only transport, no invented owner and no idle waiting. If unavailable, retain SEC_PENDING with missing access/permission. Record actual reviewer, security-covered boundaries, findings and snapshot. Use the same owner for bounded fixes/impact confirmation.

Only this explicitly selected flow authorizes conditional independent Claude Code \`adviser\`: mark ADV_REQUIRED if the changed producer/consumer API contract, permission design, concurrent write, DB migration/transaction, async/retry durability, multi-screen state or backward-compatibility boundary is reached. Cite concrete source/requirement evidence; else record ADV_NOT_APPLICABLE and the inspected reason. PL ticket classification cannot waive HQ's diff-based reclassification. Preserve adviser's existing model, mandatory specialist consultations, read-only tools and verdicts.

Before Claude QA, require current-snapshot SEC_CLEAR from the security owner, and if ADV_REQUIRED, a current-snapshot clean ADV verdict. Security and design findings, unanswered consultations and missing original evidence block progression. These passes never replace PCR, QA/E2E or native /review and do not activate ADV in standalone or other workflows.

## 4. Claude Code QA and E2E

After the final PCR gate, invoke actual Claude Code `test-qa`, then `e2e-qa`.
They independently check happy/fail paths, missing/excess tests, assertions, fixtures/mocks
and supplied execution evidence against requirements, even when no test file changed.
TEST-TRUTH-1 requires checking changed assertions, snapshots, mocks/fixtures, skipped cases
and filters for lost bug detection. A green run after weaker tests is not approval.
Keep their existing budgets and unfinished-slice reporting; no sampled full-scope approval.
CR/ADV settings in either Claude profile remain unchanged. No extra CR or ci-reviewer starts here; ADV only starts when ADV_REQUIRED is reached.
If a project explicitly requires another layer, retain it as a pending obligation and resolve its
authorization before proceeding; neither PCR nor `/review` silently substitutes for it.

Claude reviewers and review consultants remain read-only: no tests, Playwright, lint, typecheck,
build, server start, migrations, source/test edits or execution delegated through another agent.
The authorized implementer owns those actions. Preserve actual commands/cases/exit/source and
NOT_RUN/FAILED/PARTIAL; supplied results never count as the reviewer's execution.
Required execution must pass before the dependent gate. Optional unrun checks stay non-gating notes.
Preserve native verdicts, real invocation evidence, mandatory rules/consultation and HND-1 closure.

Use existing permitted role-level invocation. If the restricted MD transport is explicitly selected,
use `codex-claude-review` with **only qa/e2e selected**, retain its eleven Workflow Result fields,
and include `Parent workflow: pcr-development` plus this original contract in the request/summary.
Its source/permissions, same-owner resume, usage confirmation and rate-limit controls remain mandatory.
Its automatic final Local-ci/ci-reviewer/draft-PR handoff is not authorized by this parent flow;
return after qa/e2e to section 5. Do not pass `pcr-development` as a new unsupported runner direction.
Do not bypass unknown-usage confirmation or retry a rate limit by changing provider/session.
Use one-shot calls; never leave a model running to wait for fixes or another stage.

## 5. Standard Codex /review gate

Use Codex's built-in `/review`, not `/reviewer`, `rev:` or the custom `reviewer` agent.
Record the installed product/version, actual target/preset, base and full candidate snapshot,
native completion/result and its source correspondence. A CLI equivalent may use `codex review`
only when its supported target covers the same full intended diff. An uncommitted-only review
cannot cover earlier branch commits; a last-commit review cannot cover a multi-commit task.
Do not combine mutually exclusive CLI target/prompt flags. Check local help for the installed version.

Official documentation describes prioritized findings and working-tree review; it does not document
a stable native `Approve` label, GitHub approval submission or an approval exit-code protocol.
Therefore record the actual native result unchanged. The parent may separately record the local
gate `STANDARD_REVIEW_CLEAR` only after completed full-scope review of S_final, no unresolved
in-scope findings or required gaps, and verified target/source correspondence.
Exit code 0, an empty response, a word such as APPROVE, or missing findings alone is insufficient.
Unknown coverage, failed/interrupted/truncated output, missing capability or a changed snapshot holds
the gate. Never manufacture an approval or replace the standard review with a custom role.
If standard review raises findings, repair and renew PCR/QA/E2E under sections 3 and 6, then run
the standard review on the renewed candidate before UX. Keep every original finding/disposition.

Evidence checked 2026-11-13: OpenAI, [Developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
and [Codex CLI](https://learn.chatgpt.com/docs/codex/cli). Availability/output may differ by version;
this local gate is our operating rule, not a claim about native enforcement.

## 6. Changes after a gate

Freeze the candidate from final PCR approval through QA, E2E, standard review and human UX.
Any source/test/requirement/rule change invalidates downstream approvals for the old snapshot.
The original security owner, and adviser when required, must confirm affected delta/impact
for the current snapshot before downstream gates can be renewed.
Return to PCR for changed obligations, direct effects and every pending item. Each previous selected
owner renews current-snapshot approval, reusing unaffected evidence only with an explicit impact basis.
A test change requires QA/E2E to recheck all their obligations; changed rules/specs reopen every
obligation that depends on them. Planned verification reruns only affected required checks.
Rerun standard review after renewed prior gates. Obtain human UX approval again for a changed candidate.
No stale approval is copied onto a new SHA/hash, even for a small fix.

## 7. User UX and publication

After STANDARD_REVIEW_CLEAR, present the actual candidate/build, environment, changed user flow,
known limits and relevant verification. Wait for the user's explicit UX acceptance tied to that
candidate. Screenshots, E2E success, an AI ux-qa result, silence and a prior general instruction
to implement/create a PR are not UX approval. For a non-UI change, the user may explicitly accept
UX as not applicable with a reason; the parent must not silently waive this selected gate.
Record the actual message/reference, candidate identity and acceptance scope in the same record.

Only after human UX acceptance, current prior gates, all required verification and mandatory
handoffs are complete may the implementer prepare publication. Preserve any actual project/release
Local-ci or CI requirement; an optional extra review is never added merely by this flow.
Before every stage/commit/push/PR action, verify that its scope is authorized and that the final
content/modes exactly match the approved candidate. Preserve unrelated work and existing index hunks.
If commit hooks or final preparation change content, return to section 6.

Both draft PR creation and ready PR creation wait for UX acceptance. A draft is not a gate bypass.
The flow alone grants no blanket publication right. An existing explicit instruction to create the
scoped PR remains valid; do not ask for the same permission twice. Without it, prepare the concrete
diff and PR title/body, then ask only for the missing publication action. An explicitly authorized
early draft requires a separate user exception naming skipped gates; record them as pending.
Default to a draft when PR creation is authorized but ready publication is not. Only the user
authorizes Ready for review; UX acceptance alone does not imply it. Merge/deploy remain separate.

## 8. Evidence and limits

Keep one source-bound finding/coverage record, original owner IDs, actual results, user decisions
and final commit correspondence. Recover only missing/changed originals; do not repeatedly read
unchanged rules or make a report for every read. Use completion events and permitted bounded waits.
No polling agents, token/billing queries, permission changes or automatic unrelated reviews.
Static contract/tests prove configuration consistency only, not model obedience, real concurrency,
review quality, UX acceptance or native /review completion. Report each unexecuted gate honestly.
