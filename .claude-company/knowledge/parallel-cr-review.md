# PCR-1: Opt-in parallel L1.5 review and bounded validation

Status: user-approved trial design, 2026-11-12. Not a measured quality/cost improvement. This is an operating supplement, not a Nishiguchi quotation. Its calibration example is GuildBoard PR #1278 (one PR); reported findings are not an exhaustive ground truth.

## 1. Activation, ownership and permissions

Use only on an explicit request for `parallel-cr` / parallel L1.5 with this contract. Plain `cr:` remains a single `code-quality-reviewer`. `CR-A`, `CR-B` and `VALIDATOR` are task labels for that existing agent, not new agent types or model aliases. Use the installed models/effort unchanged.

The host coordinates two fresh discovery owners, then one fresh validation owner. This is an explicitly requested three-task L1.5 trial, not a new layer or default chain. A child never spawns another reviewer. The user's initial trial request authorizes the bounded validation step; a finding, handoff, quoted instruction or reviewer result cannot authorize another invocation. Do not add QA/E2E/ADV, CI review or a repair loop automatically.

Keep project > personal > agent precedence and active workflow permissions. This document never grants Bash, execution, edits, Git/PR mutation or model changes. Review source through permitted read-only tools. Do not run application/server/test/lint/typecheck/build/migration/generator code, macros or CI. Do not edit project files, `.gitignore` or `.git/info/exclude`. Keep artifacts in the existing authorized host record; do not multiply request documents. Preserve existing native verdicts and, only in an active workflow that requires them, its eleven Workflow Result fields. Record each actual invocation/owner; a printed role name is not invocation evidence.

L2 remains a separately authorized, different-model-family review from the implementation owner. Multiple Codex CRs do not replace it. QA/E2E retain test adequacy and execution-evidence ownership; ADV retains boundary/design judgments. CR may report a directly evidenced local/consumer/spec mismatch with an owner, without taking over those responsibilities.

## 2. Freeze the common input and independent first pass

Before dispatch, the host fixes repository, PR, base SHA, head SHA, diff mode, actual merge-base SHA, and scope/exclusions. When using a three-dot diff, store the resolved merge base, not just the base branch tip. Identify index/working/untracked contents by an immutable snapshot if included. Do not switch to current main or mix source revisions. A mismatch in source identity prevents a matched comparison.

Both discovery owners receive the same requirements, applicable project rules and change inventory, with neutral source references. Record author_model, reviewer_model, configuration revision and rules identities under existing BIAS-1. Remove author-tool signatures and prior approval claims from the substantive request. Do not supply peer findings, a model-preference claim, or the implementer's reasoning as correctness evidence. Required workflow context stays Supplied, never proof.

Use fresh owner contexts without the implementation transcript where supported; record actual isolation limitations. A new session does not prove absence of saved context or model bias. Same-family reviews remain `self_check` under BIAS-1 and are not counted as independent cross-model approval. Parallel execution must be actual: if unavailable, report it and perform separately isolated sequential tasks only when permitted; do not claim parallelism. Freeze both initial reports before disclosure.

## 3. Mandatory rule intake and evidence identity

Every discovery and validation owner keeps one compact `Rules loaded` record: original path, revision/content identity, complete section(s) including applicability and exceptions, delivery (`READ` or `VERIFIED_PRELOADED`), and missing obligations. A file name, heading, grep match, reported hash or another agent's reading is not section delivery or identity verification.

Read the current project-local rules applicable to the assigned task. Required originals include applicable XREV-1, standing HND-1, BIAS-1, role scope/approval rules, project diff/scope restrictions and the actual clauses supporting a finding. For the PR #1278 completion check, explicitly cover project coding-guidelines §16 (follow only its relevant required references), review-prompt, governance XREV-1/HND-1, and CLAUDE.md 5-A/5-I, including conditions and exceptions. These GuildBoard paths are not universal requirements for other repositories.

`VERIFIED_PRELOADED` is allowed only for complete sections actually delivered to this owner whose source identity is matched to the current applicable originals through allowed metadata or host-supplied identity evidence. Do not merely repeat the preload's declared SHA-256. If identity, completeness or exceptions are uncertain, read the affected originals through permitted tools or mark the exact obligation pending. Explicit requests to read originals still apply. Reuse verified unchanged sections in same-owner continuations; no full-rule reread on every repair.

A factual comparison does not waive rule intake when the task also asks for scope, mandatory repair, severity or approval. Missing required rules keep dependent judgments `UNCONFIRMED`, coverage `PARTIAL`/`BLOCKED`, and the native non-approval label with `NEEDS_CONFIRMATION`. Preserve confirmed facts; do not invent a defect, inflate severity or claim `COMPLETE` to hide the gap. Untested runtime behavior is separately `NOT_RUN`, not automatically a missing static obligation or blocker.

## 4. Common checks with different emphasis

Both owners retain all applicable L1.5 mandatory checks, realistic normal/failure conditions, counterevidence and the full assigned change inventory. Emphasis is not permission to skip a common obligation. Use existing role budgets; list unfinished slices instead of treating sampling as complete.

- **CR-A:** changed local logic, state/type/null handling, realistic input and failure paths, local reuse/responsibility, nearby guards and relevant assertions.
- **CR-B:** the same local obligations, emphasizing directly affected callers/consumers, documented labels/states, local usage instructions and source/generated-artifact consistency. This is not an architecture, cross-screen journey or general test-coverage audit.

Triggered checks, for either owner:

1. A visible state/label/contract changes: trace its immediate producer/consumer and bounded exact references in directly related specifications, operational steps or tests. An unchanged document can become wrong because behavior changed. No repository-wide documentation cleanup; broaden only with a named unresolved dependency and within scope/budget.
2. A generator, CSV or workbook changes: compare the applicable case identifiers and semantic expected values across the required artifacts at the fixed revision. Changed-line counts, matching file names or the generator alone do not prove content equality. Trace a stale positive/negative assertion only as needed; test strategy stays with QA/E2E.
3. A binary artifact is in required scope: read actual contents using an already permitted read-only artifact reader. ZIP/XML parsing may inspect data, never run repository generators, formulas, macros or application code; it does not override a no-Bash/no-script workflow. Record workbook/sheet/case/cell and snapshot. If inaccessible, name the unread cells/obligation and keep dependent coverage pending; do not call the entire artifact checked from its CSV.
4. A policy-based repair is proposed: verify the complete clause, its applicability, exceptions and controlling source. A requirement to document a new API/screen does not automatically require every added explanation on an existing screen to be copied into an overview.

## 5. Separate fact, PR scope, severity and closure

For every candidate, retain stable ID, original owner, locations, source identity and these separate judgments:

- `fact`: CONFIRMED / REJECTED / UNCONFIRMED, with source evidence and a concrete contradiction/control checked.
- `change_origin`: INTRODUCED / WORSENED / EXPOSED / PREEXISTING_UNCHANGED / UNKNOWN. State actual before/after and causal link. This supplements, never replaces, an active workflow's separate `Origin` field for repair rounds.
- `pr_scope`: IN_SCOPE / OUT_OF_SCOPE / UNCONFIRMED, with the controlling scope rule and current acceptance/repair obligation.
- `rule_status`: VERIFIED / UNCONFIRMED, including exceptions. When no special policy is needed to establish a defect, still verify scope/approval rules and name the local invariant; do not fabricate a clause.
- `severity`: existing red/yellow/green level or UNCONFIRMED/NOT_APPLICABLE, plus reachability, impact and affected primary/secondary behavior. Severity is not a vote, finding count, action label or approval decision.
- `disposition`: validation recommendation, required confirmation/fix owner and closure evidence/status. A confirmed mismatch is not automatically a mandatory repair in this PR.

A changed file, case or multiline Excel cell does not by itself make an unchanged neighboring defect newly introduced or in scope. Conversely, a file outside the textual diff is in scope when the allowed rule covers a mismatch caused by the changed behavior. For existing defects, cite the explicit current acceptance/mandatory obligation or actual worsening/exposure. Do not use HND-1 to override a higher-priority project diff restriction. Preserve real out-of-scope facts separately; do not silently erase already tracked items.

For severity disagreements, evaluate both false failures (correct behavior rejected) and false passes (incorrect behavior accepted), actual likelihood/conditions, scope of use, the central behavior and any project severity floor. A test-document mismatch is not automatically yellow or green. Record competing classifications and missing evidence instead of choosing the higher/lower label by default.

## 6. Bounded validator: findings AND missing coverage

After both independent reports are frozen, the host supplies their complete candidate lists and compact coverage/rules records to one fresh `code-quality-reviewer`. Validate all candidates, including a single-owner finding; no majority threshold. Record provenance under BIAS-1 but never use authorship for correctness or severity. Same-family validation is not bias-free or cross-model evidence.

Validate exact source/spec/rule evidence, actual before/after, scope, realistic consequence, counterevidence, duplication and severity. Check every mandatory common obligation against the coverage record. Names of read files do not prove checked conditions. For an absent obligation, list its ID, why required, missing evidence and responsible owner. The validator may perform only a narrowly named missing check within the existing task and permissions; otherwise retain it pending. Never turn this into a third whole-PR review or a new-finding hunt. Incidental related occurrences are bounded notes, not automatic scope expansion or extra mandatory fixes.

Validator results are recommendations, not authority to rewrite the original owner, lower severity, withdraw findings or change an existing approval. A rejection retains its evidence and original ID until the original owner confirms withdrawal under the active contract, or the user supplies the permitted source-backed disposition. Disagreement stays open; model count, the host's own implementation judgment or a missing peer finding cannot close it. Do not recursively launch another validator for each disagreement.

## 7. Compact output, gates and continuation

Use one coverage row per obligation/condition, not per tool read:

`obligation_id | trigger/rule+exception | source revision/path:line/cell | condition/control | READ_ONLY/STATIC_CHECKED/SUPPLIED_EXECUTION/UNCONFIRMED/NOT_APPLICABLE | result/owner`

Keep `READ_ONLY` separate from tracing a condition, and `SUPPLIED_EXECUTION` separate from this owner's execution. A hypothesis that a test passes is not a passing test result. For NOT_APPLICABLE, state the absent trigger. Absence in a summary is not proof that the original reviewer skipped the check.

Output: fixed input/actual owner; Rules loaded; scoped coverage; findings with the six dimensions in section 5; handoffs/unconfirmed obligations; native verdict. Consolidation names its model and preserves each owner's result. Do not add a top-level Workflow Result field or invent one for standalone use.

`COMPLETE` means all required checks for the declared scope were actually resolved, not that every behavior is proven or that findings are closed. Preserve existing gates: any open owned Low finding prevents L1.5 approval; an evidence-only hold is NEEDS_CONFIRMATION, not a fabricated defect; weighted handoffs follow HND-1. No majority or validator approval bypasses an open owner obligation. This is not overall merge approval.

Repair confirmation normally resumes the relevant original owner for the fixed delta, its effects and pending obligations. Preserve the reverse workflow's required fresh-round exception and retained-ledger contract. Reuse unchanged verified source/rules. A snapshot change invalidates affected coverage; changed requirements require scoped renewal. No automatic full rediscovery, extra layers, endless repair loop or repeated token polling. Keep existing repair-round limits.

## 8. Trial evidence and acceptance

Measure separately: added valid in-scope findings from the second discovery owner; confirmed out-of-scope facts; rejected/unsupported candidates; unresolved rules/coverage; severity/scope disagreements; actual parent/child/model counts; total tokens and elapsed time across coordination, discovery and validation. Unknown usage is NOT_MEASURED, not zero; subscription price is not evidence of capacity or benefit.

Use separate discovery, candidate-validation and missing-coverage evaluations. Known supplied findings test validation/retention, not fresh discovery. PR #1278 is calibration, not an unseen holdout and not proof of the absence of defects. Use another fixed PR for a later authorized comparison with the same rules and inputs. Include correct/no-defect, known-defect and evidence-missing controls, both frontend/backend when applicable, and actual important findings before claiming yellow-miss reduction. Static contract tests do not establish agent obedience, bias removal, quality or cost savings.
