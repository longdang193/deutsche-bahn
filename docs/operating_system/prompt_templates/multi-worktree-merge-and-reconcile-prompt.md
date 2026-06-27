---
name: multi-worktree-merge-and-reconcile-prompt
description: Guide execution for multi worktree merge and reconcile prompt.
type: prompt
stage: closeout
entry_points:
- multiple worktree lanes are implementation-complete and ready for PR/merge orchestration
- merged lanes require status/evidence reconciliation before closure
prerequisites:
- per-lane verification evidence is available
- lane dependencies and merge order constraints are identified
next_steps:
- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md
- workstream-closeout-readiness-prompt.md
related_skills:
- skill-verification-before-completion
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- closeout
distribution_tier: starter_kit
---

# Multi-Worktree Merge And Reconcile Prompt

## Not For

starting implementation before per-lane verification is complete

```text
Orchestrate PR/merge sequencing for multi-worktree lanes only after closure-evidence reconciliation confirms all in-scope plans and execution-context handoff artifacts are complete: zero unresolved checklist items (`- [ ]`), no stale status fields, and no empty required sections.

Please:
1. verify each lane is merge-eligible:
   - bounded scope respected
   - verification evidence present
   - no unresolved critical blockers
2. determine merge order:
   - dependency-first sequencing
   - conflict-risk minimization
3. for each lane, decide merge path:
   - open/update PR
   - merge now
   - hold/defer with reason
4. after each merge, run required post-merge verification and report impact
5. reconcile lifecycle/status/evidence:
   - thread/workstream status updates
   - checkpoint/result-pack evidence linkage
   - unresolved risk log
6. if blockers remain, return the minimal prerequisite action needed to unblock
7. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible
```

Expected output:
- merge/reconcile decision report with one selected next action (or `close now`)
