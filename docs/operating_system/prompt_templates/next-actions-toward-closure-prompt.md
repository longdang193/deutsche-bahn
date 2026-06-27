---
name: next-actions-toward-closure-prompt
description: Select and execute next closure actions only after strict reconciliation and evidence gates pass.
type: prompt
stage: closeout
entry_points:
- closure-ready lane needs deterministic final merge/push action sequence
- single-lane reconciliation has passed and final closure execution is pending
prerequisites:
- closure-evidence reconciliation is complete for in-scope artifacts
- lane branch/worktree context and target branch are identified
next_steps:
- single-lane-merge-and-reconcile-prompt.md
- thread-closeout-readiness-prompt.md
- workstream-closeout-readiness-prompt.md
related_skills:
- skill-verification-before-completion
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- closeout
distribution_tier: starter_kit
---

# Next Actions Toward Closure Prompt

## Not For

multi-lane merge sequencing (use multi-worktree merge/reconcile prompt)

```text
Proceed with next actions toward closure for current lane, with strict evidence-first control.

Precondition gate (must all pass before any PR/merge/push action):
- Reconciliation is complete against `docs/operating_system/prompt_templates/single-lane-merge-and-reconcile-prompt.md`.
- All in-scope plan and execution-context handoff artifacts are complete.
- All completed steps and verification lines are marked `- [x]`.
- Zero unresolved checklist items remain (`- [ ]` count = 0).
- No stale status fields remain.
- No required section is empty.

If any gate fails:
- Stop.
- Do not perform PR/merge/push.
- Return blocking report with:
  1) failed gate,
  2) exact file path + section/line reference,
  3) minimal fix per item.

If all gates pass:
1. Summarize closure-readiness evidence.
2. List exact closure actions in order for current lane only.
3. Run pre-merge checks:
   - if `scripts/sync_architecture_docs.py` exists in current repo, run:
     - `.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py --check`
   - always run:
     - `.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast`
4. Merge lane into local `main` safely:
   - `git checkout main`
   - `git pull --ff-only`
   - `git merge --ff-only <lane-branch>`
   - If fast-forward is not possible:
     - stop automatic merge,
     - return `reconciliation-required` with exact conflicting files and cause,
     - propose one minimal resolution plan (rebase lane onto `main` or bounded non-ff merge with justification),
     - require explicit approval before executing conflict resolution or non-ff merge.
5. Resolution policy:
   - Do not auto-resolve semantic conflicts.
   - Do not use stash as an untracked temporary resolution path (`stash-and-forget` is prohibited).
   - If stash is used intentionally, closure is blocked until stash reconciliation proof is recorded:
     - stash entry id(s),
     - pop/apply result,
     - resolved files,
     - verification rerun result,
     - confirmation that no lane-related stash remains (or explicit tracked follow-up).
   - Do not continue to push while conflicts or reconciliation blockers remain.
   - After approved resolution, rerun pre-merge checks before merge/push.
6. Run post-merge checks on `main` (same commands).
7. Push:
   - `git push origin main`
8. Produce final closure report with:
   - completed actions,
   - verification outcomes,
   - merge/push proof,
   - remaining risks (if any),
   - explicit recommendation (`main pushed` or `blocked`).
```

Expected output:
- closure action report with either `main pushed` or `blocked`
