---
name: single-lane-merge-and-reconcile-prompt
description: Merge a single lane and reconcile status, evidence, and follow-up records.
type: prompt
stage: execution
entry_points:
- one lane is implementation-complete and needs PR/merge orchestration
- a single lane merge needs lifecycle/evidence reconciliation before closure
prerequisites:
- lane verification evidence is available
- lane branch/worktree context is identified
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

# Single-Lane Merge And Reconcile Prompt

## Not For

multi-lane merge sequencing (use multi-worktree merge/reconcile prompt)

```text
Orchestrate PR/merge for current lane only after closure-evidence reconciliation confirms all in-scope plans and execution-context handoff artifacts are complete: mark completed steps/verification lines `- [x]`, zero unresolved checklist items (`- [ ]`), no stale status fields, and no empty required sections.

Context:
- roadmap/workstream/thread in scope:
- lane record (id, owner, branch/worktree path, status):
- verification evidence:
- open blockers/conflicts:

Entry gate (all required before merge orchestration):
- lane has implementation commits
- lane-active/current plan exists and is execution-complete candidate
- in-scope verification evidence exists
- no active implementation steps remain
If any gate fails: return one minimal unblock action and stop.

Please:
1. verify lane is merge-eligible:
   - bounded scope respected
   - verification evidence present
   - no unresolved critical blockers
2. run bounded-scope doc lifecycle compliance check for changed scope:
   - use `doc-lifecycle-bounded-scope-check-prompt.md`
   - keep checks concise (no repo-wide expansion)
   - block merge on lifecycle `fail` verdict
3. enforce closure-evidence precedence for in-scope plans:
   - treat lane-active/current plan as closure source of truth
   - allow superseded predecessor plans to be closed by reference to successor evidence when criteria are satisfied
4. run concrete closure validators before merge decision:
   - `py scripts/validate_planning_lifecycle.py --strict`
   - `py scripts/validate_checkpoint_packs.py`
   - add `py scripts/validate_template_required_sections.py` only when template-governed docs are in changed scope
   - validator dedupe rule: if same validator already passed and no relevant file changed since pass, reuse prior evidence
5. decide merge path:
   - open/update PR
   - merge now
   - hold/defer with reason
   - do not use stash as a closure shortcut; no `stash-and-forget` flow is allowed
6. after merge, run required post-merge verification and report impact
7. reconcile lifecycle/status/evidence:
   - thread/workstream status updates
   - checkpoint/result-pack evidence linkage
   - unresolved risk log
   - if stash was used during conflict resolution, require explicit stash reconciliation evidence:
     - stash entry id(s)
     - pop/apply outcome
     - resolved files and verification rerun proof
     - zero remaining stash entries for this lane or explicit tracked follow-up item
8. if blockers remain, return the minimal prerequisite action needed to unblock
9. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible

Output rule:
- return one next action only.
```

Expected output:
- single-lane merge/reconcile report with one selected next action (or `close now`)
