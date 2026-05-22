## Available Agents

- req-pl
- adviser
- review-planner
- reviewer
- test-qa
- code-quality-reviewer
- hq-coder

## Routing

- p: / pl: -> req-pl
- rp: / plan: -> review-planner
- r: / rev: -> code-quality-reviewer
- a: / adv: -> adviser
- q: / qa: -> test-qa
- h: / hq: -> hq-coder

## Review Ownership

- requirement clarification -> req-pl
- implementation -> hq-coder
- L0/L1 verification -> test-qa
- L1.5 code quality review -> code-quality-reviewer
- L2+ review -> adviser
- convergence review -> reviewer
