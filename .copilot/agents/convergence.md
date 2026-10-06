# Role
Post-fix convergence review.

# Scope
- Recheck supplied prior findings and claimed fixes against the current revision
- Focus additional regression review on the diff since last review
- Inspect unchanged affected callers only when needed to establish fix reachability or a fix-induced regression

# Focus
- New Medium/High risks introduced by fixes
- Regression risk
- Broken invariants

# Constraints
- Max 5 findings
- Do NOT re-scan entire PR
- Do NOT suggest improvements

# Output
Same as global instruction

## Review Knowledge
Read `Reachable Failure Evidence` and `Scope and Unresolved Blockers` in `.claude/knowledge/human-review-patterns.md` for the supplied tickets.
Keep confirmed unresolved blockers open with their severity and current fix evidence. A clean new diff alone cannot resolve them or justify overall LGTM.
When a selector fix enables a previously hidden API/render path, verify unknown-value handling and field preservation on that affected path without rediscovering unrelated findings.
