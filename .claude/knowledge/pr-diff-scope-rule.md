# PR Diff Scope Rule

Never assume `main` is the correct PR review base.

Always resolve PR metadata first:

```bash
gh pr view <number> --json number,baseRefName,headRefName,title
```

Review against the actual PR base:

```bash
gh pr diff <number> --name-only
gh pr diff <number> --stat
git diff origin/<baseRefName>...HEAD -- <path>
```

Do not use `git diff origin/main...HEAD` unless `baseRefName == main`.

For stacked PRs:
- the parent branch is the current review base
- ignore already-reviewed parent-branch changes
- report only issues introduced in the current PR layer
- do not treat visibility in `main...HEAD` as current-layer ownership

If the base branch is unclear:
- state the assumption explicitly
- avoid broad rediscovery review
- ask only when safe review is impossible
