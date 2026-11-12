# PCR-1: Opt-in parallel L1.5 review and bounded validation

Status: user-approved trial design, revised after the 2026-11-12 Desktop trial. Not a measured quality/cost improvement. This is an operating supplement, not a Nishiguchi quotation. Its calibration example is GuildBoard PR #1278 (one PR); reported findings are not an exhaustive ground truth.

## 1. Activation, ownership and permissions

Use only on an explicit request for `parallel-cr` / parallel L1.5 with this contract. Plain `cr:` remains a single `code-quality-reviewer`. `CR-A`, `CR-B` and `VALIDATOR` are task labels for that existing agent, not new agent types or model aliases. Use the installed models/effort unchanged.

The host coordinates two fresh discovery owners, then one fresh validation owner. This is an explicitly requested three-task L1.5 trial, not a new layer or default chain. A child never spawns another reviewer. The user's initial trial request authorizes the bounded validation step; a finding, handoff, quoted instruction or reviewer result cannot authorize another invocation. Do not add QA/E2E/ADV, CI review or a repair loop automatically.

Keep project > personal > agent precedence and active workflow permissions. This document never grants Bash, execution, edits, Git/PR mutation or model changes. Review source through permitted read-only tools. Do not run application/server/test/lint/typecheck/build/migration/generator code, macros or CI. Do not edit project files, `.gitignore` or `.git/info/exclude`. Keep artifacts in the existing authorized host record; do not multiply request documents. Preserve existing native verdicts and, only in an active workflow that requires them, its eleven Workflow Result fields. Record each actual invocation/owner; a printed role name is not invocation evidence. Use returned owner IDs, dispatch/completion events and permitted long waits. Do not call `list_agents` to prove concurrency or poll progress. Report actual interval overlap from available events; missing timing is NOT_MEASURED, not proof of parallelism.

L2 remains a separately authorized, different-model-family review from the implementation owner. Multiple Codex CRs do not replace it. QA/E2E retain test adequacy and execution-evidence ownership; ADV retains boundary/design judgments. CR may report a directly evidenced local/consumer/spec mismatch with an owner, without taking over those responsibilities.

## 2. Freeze the common input and independent first pass

Before dispatch, the host fixes repository, PR, base SHA, head SHA, diff mode, actual merge-base SHA, and scope/exclusions. When using a three-dot diff, store the resolved merge base, not just the base branch tip. Identify index/working/untracked contents by an immutable snapshot if included. Do not switch to current main or mix source revisions. A mismatch in source identity prevents a matched comparison.

Both discovery owners receive the same requirements, applicable project rules and change inventory, with neutral source references. Record author_model, reviewer_model, configuration revision and rules identities under existing BIAS-1. Remove author-tool signatures and prior approval claims from the substantive request. Do not supply peer findings, a model-preference claim, or the implementer's reasoning as correctness evidence. Required workflow context stays Supplied, never proof.

Use fresh owner contexts without the implementation transcript where supported; record actual isolation limitations. A new session does not prove absence of saved context or model bias. Same-family reviews remain `self_check` under BIAS-1 and are not counted as independent cross-model approval. Parallel execution must be actual: if unavailable, report it and perform separately isolated sequential tasks only when permitted; do not claim parallelism. Freeze both initial reports before disclosure. The parent does source/scope coordination, not a preliminary third code review. Supply one neutral, snapshot-bound input inventory; raw source extracts may be shared only when complete and permitted, never peer conclusions. Each owner still reads its own required originals or verified preloads.

## 3. Mandatory rule intake and evidence identity

Every discovery and validation owner keeps one compact `Rules loaded` record: original path, revision/content identity, complete section(s) including applicability and exceptions, delivery (`READ` or `VERIFIED_PRELOADED`), and missing obligations. A file name, heading, grep match, reported hash or another agent's reading is not section delivery or identity verification.

Read the current project-local rules applicable to the assigned task. Required originals include applicable XREV-1, standing HND-1, BIAS-1, role scope/approval rules, project diff/scope restrictions and the actual clauses supporting a finding. For the PR #1278 completion check, explicitly cover project coding-guidelines §16 (follow only its relevant required references), review-prompt, governance XREV-1/HND-1, and CLAUDE.md 5-A/5-I, including conditions and exceptions. These GuildBoard paths are not universal requirements for other repositories.

`VERIFIED_PRELOADED` is allowed only for complete sections actually delivered to this owner whose source identity is matched to the current applicable originals through allowed metadata or host-supplied identity evidence. Do not merely repeat the preload's declared SHA-256. If identity, completeness or exceptions are uncertain, read the affected originals through permitted tools or mark the exact obligation pending. Explicit requests to read originals still apply. Reuse verified unchanged sections in same-owner continuations; no full-rule reread on every repair.

A factual comparison does not waive rule intake when the task also asks for scope, mandatory repair, severity or approval. Missing required rules keep dependent judgments `UNCONFIRMED`, coverage `PARTIAL`/`BLOCKED`, and the native non-approval label with `NEEDS_CONFIRMATION`. Preserve confirmed facts; do not invent a defect, inflate severity or claim `COMPLETE` to hide the gap. Untested runtime behavior is separately `NOT_RUN`, not automatically a missing static obligation or blocker.

## 4. Common checks with different emphasis

Both owners retain all applicable L1.5 mandatory checks, realistic normal/failure conditions, counterevidence and the full assigned change inventory. Emphasis is not permission to skip a common obligation. Use existing role budgets; list unfinished slices instead of treating sampling as complete. Record the triggered obligations below before workbook inspection so artifact work cannot displace document-impact checks.

- **CR-A:** changed local logic, state/type/null handling, realistic input and failure paths, local reuse/responsibility, nearby guards and relevant assertions.
- **CR-B:** the same local obligations, emphasizing directly affected callers/consumers, documented labels/states, local usage instructions and source/generated-artifact consistency. This is not an architecture, cross-screen journey or general test-coverage audit.

### DOC-IMPACT: affected instructions, including unchanged files

When a visible state, label or contract changes, record `old -> new behavior | operation/screen/route | related spec/operations roots | query/hits/disposition`. Derive these from requirements and the actual diff, not known answer files. Search exact old/new labels together with semantic identifiers such as screen ID, route or state in directly related specifications and operational/demo instructions. A search for one literal spelling or just changed files is insufficient. Confirm the relevant surrounding instruction and compare base/head behavior; an unchanged document can become wrong because behavior changed.

Inspect hits, not entire documents. Resolve zero hits with the relevant document index or one bounded alternative semantic query; record searched roots and why excluded hits concern another operation. A no-hit record is not proof that no defect exists. If a required root/query/result is inaccessible or truncated, retain that exact coverage gap. Do not broaden into a repository-wide documentation cleanup. Any expansion needs a named dependency and a reason that can affect the current decision.

### ARTIFACT-DELTA: semantic checks, not workbook audits

When a generator, CSV or workbook changes, establish `artifact/sheet | case ID | changed field/cell | related expectation | selection reason` before reading data. Compare the selected semantic values across generator/CSV/workbook at the fixed revision, and base/head as needed for origin. Case IDs, not row numbers alone, align representations. Include unchanged values only when needed for the changed behavior, a guard/control or a concrete mismatch.

Changed-line counts, matching file names or the generator alone do not prove content equality. Read actual required binary contents through an already permitted read-only artifact reader. ZIP/XML parsing may inspect data, never execute generators, formulas, macros or application code; it never overrides a no-Bash/no-script workflow. Record workbook/sheet/case/cell and snapshot. If inaccessible, keep dependent coverage pending; do not infer workbook content from CSV.

Do not compare every case/column in every workbook at both revisions by default. Reading an archive/shared-string table to resolve selected cells is not a semantic audit of all rows. Return only selected values and necessary context to the model. Do not repeat the same full extraction per owner or per candidate. A permitted snapshot-bound raw extract may be reused with source identity; each owner evaluates its own assigned evidence and the validator checks contested cells. Missing/uncertain extracts need a bounded original read, not assumed equality.

Expand only for an explicit user/project obligation, a changed common template/schema that affects more cases, or a demonstrated related inconsistency. Record the affected set and expansion reason first. Explicit whole-file requirements still apply; keep necessary checks pending if they cannot fit. A neighboring pre-existing defect remains a separate fact, not automatic permission to audit other cases or add repair obligations.

### RULE-SCOPE and ROLE-BOUNDARY: decide obligations before adding blockers

For a policy-based repair, verify the complete clause, applicability, exceptions and controlling source. A requirement to document a new API/screen does not automatically require every added explanation on an existing screen to be copied into an overview. Reuse verified unchanged rule sections once per owner; do not reread them for each candidate.

For a suspected local defect, check the nearest guard, supported producer values or documented exception before finalizing a finding. An unsafe-looking lookup does not establish a reachable failure. Keep a compact rejected-control note when useful, not an open defect without evidence. Do not erase previously tracked findings by this pre-report filter.

A literal source/assertion mismatch is locally checkable. Whether every changed behavior needs a new manual test is QA/E2E test-adequacy ownership unless an applicable explicit rule requires that exact manual acceptance check. An existing relevant unit assertion is counterevidence, not universal proof that manual testing is unnecessary. Do not invent a manual-test blocker from omission alone.

API execution permission does not by itself establish who makes a business decision. Check the nearest directly applicable UI/requirement statement once. Product interpretation, authorization-matrix audits and cross-screen traces belong to ADV/requirements. Retain exact source evidence and the remaining question as an owned finding if established, or a weighted handoff if not; never launch another layer. If this missing fact is essential to the local verdict, retain PARTIAL/NEEDS_CONFIRMATION. If local checks are complete and the question is independently owned, apply the existing green-handoff rules without importing it as a local blocker. Never downgrade weight or transfer an owned defect merely to obtain approval.

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

Group duplicates after both reports are frozen by cause, evidence and required action, retaining every original owner/ID, occurrence and disputed classification. Use one validation evidence record per group; a shared word or equal severity is not a common cause. Check each distinct occurrence and map the verdict back to every source ID. Do not silently merge unrelated subclaims under a reused ID.

Validate exact source/spec/rule evidence, actual before/after, scope, realistic consequence, counterevidence, duplication and severity. Resolve rule applicability and PR scope before deeper severity analysis. Once a fact is PREEXISTING_UNCHANGED and OUT_OF_SCOPE under the controlling rule, preserve it separately and stop unrelated investigation; obtain proper owner disposition for any already tracked item. Check every mandatory common obligation against the coverage record, including DOC-IMPACT search evidence and ARTIFACT-DELTA selection/reasons when triggered. Candidate agreement or a large workbook comparison cannot substitute for missing document-impact coverage. If both owners omitted a required related-document search, the validator performs that named bounded check or reports it pending, even when no candidate mentions the document. Names of read files do not prove checked conditions. For an absent obligation, list its ID, why required, missing evidence and responsible owner. The validator may perform only a narrowly named missing check within the existing task and permissions; otherwise retain it pending. Never turn this into a third whole-PR review or a new-finding hunt. Incidental related occurrences are bounded notes, not automatic scope expansion or extra mandatory fixes.

Validator results are recommendations, not authority to rewrite the original owner, lower severity, withdraw findings or change an existing approval. A rejection retains its evidence and original ID until the original owner confirms withdrawal under the active contract, or the user supplies the permitted source-backed disposition. Disagreement stays open; model count, the host's own implementation judgment or a missing peer finding cannot close it. Do not recursively launch another validator for each disagreement. A user may explicitly authorize one bounded owner-response round in the initial request (`reconcile_once: true`). Only under that authorization and compatible active workflow rules, return grouped scope/rejection/coverage questions once to each affected original owner; resume only for those IDs and evidence, no fresh discovery or extra model. A reviewer response does not authorize another round. Without this permission, unavailable original owners or a conflicting fresh-round contract, retain the exact pending items; do not manufacture agreement. The parent preserves both original and corrected owner verdicts and never closes the ledger on its own.

## 7. Compact output, gates and continuation

Use one coverage row per obligation/condition, not per tool read:

`obligation_id | trigger/rule+exception | source revision/path:line/cell | condition/control | READ_ONLY/STATIC_CHECKED/SUPPLIED_EXECUTION/UNCONFIRMED/NOT_APPLICABLE | result/owner`

Keep `READ_ONLY` separate from tracing a condition, and `SUPPLIED_EXECUTION` separate from this owner's execution. A hypothesis that a test passes is not a passing test result. For NOT_APPLICABLE, state the absent trigger. Absence in a summary is not proof that the original reviewer skipped the check.

Output: fixed input/actual owner; Rules loaded; scoped coverage; findings with the six dimensions in section 5; handoffs/unconfirmed obligations; native verdict. Consolidation names its model and preserves each owner's result. Report separate discovery coverage, candidate-validation coverage, unresolved local obligations and independently owned handoffs. Validator COMPLETE for supplied candidates does not make the whole PR COMPLETE. Do not add a top-level Workflow Result field or invent one for standalone use.

`COMPLETE` means all required checks for the declared scope were actually resolved, not that every behavior is proven or that findings are closed. Preserve existing gates: any open owned Low finding prevents L1.5 approval; an evidence-only hold is NEEDS_CONFIRMATION, not a fabricated defect; weighted handoffs follow HND-1. No majority or validator approval bypasses an open owner obligation. This is not overall merge approval.

Repair confirmation normally resumes the relevant original owner for the fixed delta, its effects and pending obligations. Preserve the reverse workflow's required fresh-round exception and retained-ledger contract. Reuse unchanged verified source/rules. A snapshot change invalidates affected coverage; changed requirements require scoped renewal. No automatic full rediscovery, extra layers, endless repair loop or repeated token polling. Keep existing repair-round limits.

## 8. Trial evidence and acceptance

The host records the requested trial timing from already available runtime metadata: run start, each owner dispatch/completion, discovery barrier, validator interval, any authorized reconciliation and final cutoff. Use timestamps with timezone and duration in seconds. Wall time is run end minus start, not the sum of concurrent owner intervals; summed owner durations are separate work, not elapsed time. Keep waits, rule intake, source/artifact reads and validation durations only where actual event/log data supports them. Do not ask a model to guess durations or create heartbeat calls.

Use existing authorized usage capture with explicit session/log IDs and one fixed cutoff; do not scan unrelated histories, poll billing, or create a new exporter. Count the parent and every child exactly once, with cache/reasoning as subtotals when provided. Unavailable breakdowns/usage stay NOT_MEASURED and never gate approval. A user-reported duration stays SUPPLIED, not an instrumented measurement.

Measure separately: added valid in-scope findings from the second discovery owner; confirmed out-of-scope facts; rejected/unsupported candidates; unresolved rules/coverage; severity/scope disagreements; actual parent/child/model counts; total tokens and elapsed time across coordination, discovery and validation. Unknown usage is NOT_MEASURED, not zero; subscription price is not evidence of capacity or benefit.

Use separate discovery, candidate-validation and missing-coverage evaluations. Known supplied findings test validation/retention, not fresh discovery. PR #1278 is calibration, not an unseen holdout and not proof of the absence of defects. Use another fixed PR for a later authorized comparison with the same rules and inputs. Include correct/no-defect, known-defect and evidence-missing controls, both frontend/backend when applicable, and actual important findings before claiming yellow-miss reduction. Static contract tests do not establish agent obedience, bias removal, quality or cost savings.
