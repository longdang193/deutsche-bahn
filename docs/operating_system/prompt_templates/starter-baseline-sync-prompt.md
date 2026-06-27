---
name: starter-baseline-sync-prompt
description: Sync a project to the latest starter baseline with controlled drift handling.
type: prompt
stage: maintenance
entry_points:
- use this prompt when its title scope matches the current planning/execution need
prerequisites:
- relevant in-scope roadmap/workstream/thread/spec/plan context is available
next_steps:
- implementation-next-action-gate-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- maintenance
distribution_tier: starter_kit
---

# Starter Baseline Sync Prompt

Use this when you want to sync another repo/worktree to the latest local
`project-OS-starter` baseline.

```text
Sync this repo to the latest local `project-OS-starter` baseline.

Baseline:
- `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter` (pull latest first)

Target:
- repo/worktree: <path>
- branch: <branch>

Do:
1. Diff target vs latest baseline.
2. Classify each change: adopt / adapt / defer (with reason).
3. Apply relevant updates across docs, prompts, scripts, validators, tests, and config contracts.
4. Preserve target-specific product behavior; keep starter governance/validator intent.
5. Reconcile lineage/status metadata if required by new validator rules.
6. Run verification:
   - `python scripts/validate_repo_contracts.py --fast`
   - plus `validate_planning_lifecycle.py --strict` and `validate_checkpoint_packs.py` if present.
7. Output a short report:
   - baseline commit synced
   - files changed
   - adopted/adapted/deferred list
   - validation results
   - required follow-ups
8. Commit:
   - `Sync latest project-OS-starter baseline`
```

Expected output:
- synced target repo with a concise migration report
