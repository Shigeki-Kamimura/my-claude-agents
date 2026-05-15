# AGENTS.md

## Available Agents

- req-pl
- review-planner
- adviser
- reviewer
- test-qa
- hq-coder

## Routing

- p: / pl: -> req-pl
- adv: -> adviser
- q: / qa: -> test-qa
- h: / hq: -> hq-coder

## Review Ownership

- requirement clarification -> req-pl
- implementation -> hq-coder
- L0/L1 verification -> test-qa
- L2+ review -> adviser
- convergence review -> reviewer

See:
- CLAUDE.md
- REVIEW_PLAYBOOK.md
- agents/*.md

## Backlog Ticket Reference

Backlog tickets are manually fetched and stored outside the working repository.

Canonical ticket directory:

```bash
~/work-flow-helper/projects/guildboard-training-management/output/raw/