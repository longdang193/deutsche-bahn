---
name: multi-worktree-dispatch-prompt
description: Guide execution for multi worktree dispatch prompt.
type: prompt
stage: execution
entry_points:
- a task should be split into multiple isolated worktrees
- existing multi-lane execution needs deterministic rerouting
prerequisites:
- in-scope roadmap/workstream/thread/spec/plan context is identified
- candidate lane boundaries and blockers are available
next_steps:
- git-worktree-preflight-and-create-prompt.md
- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
- thread-closeout-readiness-prompt.md
related_skills:
- skill-planning-dispatch
- skill-using-git-worktrees
- skill-executing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Multi-Worktree Dispatch Prompt

## Not For

single-lane tasks that do not benefit from decomposition

```text
Determine whether this task should run in multiple worktrees and select one next action.

Please:
1. verify whether splitting into multiple worktrees is justified by scope/dependency boundaries
2. define or refine lane boundaries with owner and expected file touch surface
3. identify overlap/conflict risks and required re-slicing if needed
4. choose one immediate next action from existing artifacts only
5. if no action is eligible, return the minimal prerequisite action needed to unblock
6. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible
```

Expected output:
- lane-split decision with one selected next action constrained by existing artifacts
