---
name: doc-lifecycle-bounded-scope-check-prompt
description: Run bounded-scope documentation lifecycle compliance checks for a worktree lane with evidence-backed verdict and next action.
type: prompt
stage: maintenance
entry_points:
- need doc lifecycle compliance check in bounded scope
- worktree lane closeout needs lifecycle evidence
prerequisites:
- bounded scope paths and changed-file set are available
- adoption mode and relevant planning context are identified
next_steps:
- implementation-next-action-gate-prompt.md
- workflow-drift-detection-and-reconciliation.md
- workflow-live-run-verification.md
related_skills:
- skill-doc-system-lifecycle
- skill-verification-before-completion
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- docs
- lifecycle
- compliance
distribution_tier: starter_kit
---

# Doc Lifecycle Bounded Scope Check Prompt

## Not For

full-repo rewrite planning or unbounded architecture redesign

```text
Run a lean bounded-scope documentation lifecycle compliance check for current worktree lane.

Context:
- worktree path:
- lane/thread id:
- scope paths:
- changed files (or commit range):
- adoption mode:

Do only what is needed for changed scope.

Please:
1. Validate changed files stay in correct source-of-truth layers.
2. Check only high-risk lifecycle failures:
   - wrong ownership layer
   - generated-surface manual edits
   - required schema/validator mismatch directly tied to changed files
3. Run minimal validator set based on changed paths:
   - run `py scripts/validate_repo_contracts.py --fast` only when changed scope touches governed docs/rules/workflows/scripts or contract-sensitive surfaces
   - otherwise run only directly triggered validators for touched artifacts
   - escalate to additional checks only when a concrete path-linked risk is found
4. Return concise verdict per changed area:
   - pass
   - warn
   - fail
5. If warn/fail, return smallest bounded remediation action.
6. Return one next action only (`close now` or one fix step).

Rules:
- stay strictly inside declared scope
- avoid speculative checks and repo-wide expansion
- no long narrative; evidence lines only

Expected output (short):
- scope summary (1-3 lines)
- checks run
- issues (only actionable)
- verdict
- one next action
```
