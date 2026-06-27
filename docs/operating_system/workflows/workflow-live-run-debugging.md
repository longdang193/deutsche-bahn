---
name: workflow-live-run-debugging
description: Run the live run debugging workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-systematic-debugging
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

# Live Run Debugging Workflow

## Purpose

Handle live-run failures with evidence-first debugging and bounded fixes.

## Execution Flow

1. Reproduce the failure in a live or equivalent runtime path.
2. Capture evidence from:
   - logged artifacts
   - observability systems (traces/metrics/logs)
   - stage outputs and intermediate artifacts
3. Identify the exact failure boundary:
   - stage
   - component
   - contract/invariant that broke
4. Audit gate:
   - if qualifying problem trigger is met and no active audit exists, create audit bundle at `docs/superpowers/plans/audit/<audit_id>/`
   - initialize `report.md` from `docs/operating_system/templates/audit-report-with-evidence-template.md`
   - during verification loop for qualifying failures, run:

   ```powershell
   .\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
   ```

5. Define one bounded fix:
   - minimal scope
   - no unrelated changes
6. Apply the fix.
7. Trigger targeted rerun through `workflow-live-run-execution`.
8. Route to `workflow-live-run-verification` when rerun result is successful;
   continue debugging when rerun fails.
<MUST-DO>
9. Update in-scope execution-context handoff artifacts when failure boundary, fix path, or verification disposition changed.
</MUST-DO>

## Decision Gates

1. No evidence, no fix:
   - do not patch without captured evidence and failure boundary.
2. No boundary, no patch:
   - if failure boundary is unclear, continue investigation rather than coding.
3. Audit mandate gate:
   - when trigger conditions in `docs/operating_system/rules/audit-evidence-mandate-rule.md` apply, debugging is incomplete until audit bundle exists (or explicit allowed bypass is recorded).
4. Minimality gate:
   - reject fixes that alter unrelated modules/contracts.
5. Rerun gate:
   - every fix must be exercised by targeted rerun evidence.
6. Handoff gate:
   - if execution-context handoff artifacts are in scope, debugging pass is blocked until those artifacts are updated with current failure boundary/fix/verification status.

## Traceability Requirements

Record explicit linkage:

- failure evidence -> boundary decision -> audit record -> bounded fix -> rerun evidence -> handoff artifact updates

If linkage is incomplete, do not mark resolved.

## Failure/Recovery Path

- if rerun still fails, classify whether:
  - wrong boundary
  - incomplete fix
  - secondary failure exposed
- return to boundary analysis and apply one new bounded action only
- repeat with updated evidence until verification route is eligible

## Exit Criteria

- failure boundary is explicitly identified
- required audit bundle exists or allowed bypass is explicitly recorded
- bounded fix is applied
- targeted rerun evidence exists for the applied fix
<MUST-DO>
- in-scope execution-context handoff artifacts are updated
</MUST-DO>
- workflow is ready to transition to verification or next bounded debug pass
