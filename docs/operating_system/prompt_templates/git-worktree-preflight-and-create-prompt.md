---
name: git-worktree-preflight-and-create-prompt
description: Guide safe git worktree creation with mandatory freshness preflight and decision logging.
type: prompt
stage: execution
entry_points:
- create a git worktree for isolated execution
- enforce base-branch freshness and divergence decisions before worktree operations
prerequisites:
- repository root is known
- target branch name is provided
next_steps:
- execution-readiness-gate-prompt.md
- implementation-next-action-gate-prompt.md
related_skills:
- skill-using-git-worktrees
- skill-executing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
- .agents/skills/skill-using-git-worktrees/SKILL.md
tags:
- prompt
- execution
- worktree
- safety
distribution_tier: starter_kit
---

# Git Worktree Preflight And Create Prompt

## Not For

- non-git environments
- tasks that do not require isolated workspace
- PR, merge, closeout, or lifecycle reconciliation orchestration

```text
Set up a git worktree safely with freshness checks.

Do in order:
1) Run `git status --short` on base branch.
   - If dirty, stop and ask for commit/stash/discard decision.
2) Run `git fetch origin`.
3) Run `git rev-list --left-right --count origin/main...main`.
   - If ahead>0: ask whether to push now (recommended) or continue from local-only commits.
   - If behind>0: ask whether to rebase/pull first or continue knowingly.
4) Capture base SHA with `git rev-parse --short main`.
5) Resolve worktree directory using skill policy (existing dir > CLAUDE/GEMINI policy > ask user).
6) Verify ignore protection for project-local worktree dirs via `git check-ignore`.
7) Create/reuse worktree and run baseline setup/tests.
8) Return:
   - worktree path
   - base branch and SHA
   - ahead/behind counts
   - user decision record
   - baseline test status

Stop boundary:
- End after worktree create/reuse result and preflight evidence are captured.
- Do not run closeout validators, PR orchestration, merge decisions, or lifecycle reconciliation in this prompt.
- If caller asks for merge/closeout, route to `single-lane-merge-and-reconcile-prompt.md`.
```

Expected output:
- one safe worktree create/reuse result with freshness evidence
- explicit divergence decision log when ahead/behind was non-zero
- baseline test outcome or blocker requiring user decision
- one selected next action only
