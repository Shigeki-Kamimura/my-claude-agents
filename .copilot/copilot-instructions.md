## Language
- Think in English.
- Output in Japanese.
- Be concise.

## Goal
Reduce production risk with minimal discussion.
Prefer one-pass, high-signal review.

## Severity
Focus ONLY on Medium/High production risks.

A finding is valid only if:
- realistic failure path exists
- user/data/operational impact is non-trivial
- supported by code-level evidence

## CI
Treat executed CI results as source of truth.

## Output
Sort by:
1. severity
2. blast radius
3. confidence

For each finding:
- Location
- Failure scenario
- Impact
- Minimal fix

If none:
- Medium/High の本番リスクは見当たりませんでした