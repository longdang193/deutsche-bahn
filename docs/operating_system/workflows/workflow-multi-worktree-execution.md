---
name: workflow-multi-worktree-execution
description: Run the multi-worktree execution workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-using-git-worktrees
- skill-dispatching-parallel-agents
- skill-executing-plans
- skill-verification-before-completion
tags:
- workflow
- execution
- change
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Multi-Worktree Execution Workflow

## Goal

Execute multiple independent development lanes safely using isolated worktrees,
bounded scope, and explicit merge/closeout controls.

## Execution Flow

1. Run routing gate and decide whether lane splitting is warranted.
2. Define lane registry:
   - lane id
   - owner
   - objective
   - expected files/modules
   - verification commands
3. Create one worktree per lane with clean baseline checks.
4. Execute each lane with bounded changes only.
5. Apply patch-pattern detection for patch-heavy lanes.
6. Verify each lane before merge claims.
7. Merge in dependency-safe order and rerun shared regression checks.
8. Reconcile lifecycle/status evidence and close out.

## Decision Gates

1. Decomposition gate:
   - split lanes only when scope boundaries are independent enough.
2. Overlap gate:
   - if two lanes require the same hot files, re-slice before execution.
3. Evidence gate:
   - no lane can claim complete without fresh verification evidence.
4. Merge gate:
   - merge only lanes that satisfy bounded scope + validation requirements.
5. Closeout gate:
   - run thread/workstream closeout prompts when lifecycle states change.

## Partial Entry Rules

- If worktrees already exist, enter at lane execution/verification.
- If a lane already failed, enter at lane debugging and bounded rerun.
- If implementation is done but closure is pending, enter at lifecycle reconciliation.

## Exit Criteria

- All active lanes are terminal (merged or explicitly deferred).
- Evidence and status updates are reconciled.
- Next action is explicitly selected if any lane remains open.
