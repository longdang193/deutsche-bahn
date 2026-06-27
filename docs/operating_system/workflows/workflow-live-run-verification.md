---
name: workflow-live-run-verification
description: Run the live run verification workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-verification-before-completion
- skill-test-driven-development
tags:
- workflow
- closeout
- change
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Live Run Verification Workflow

## Goal

Confirm issue resolution and expected behavior using evidence, while screening
for regressions before closeout.

## Execution Flow

1. Validate expected outputs against scenario/spec acceptance criteria.
2. Validate resolution evidence against prior failure boundary.
3. If failure path was audit-qualifying, validate linked audit report/evidence bundle completeness.
4. Run audit validator for qualifying failures:

   ```powershell
   .\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
   ```

5. Run targeted regression checks for impacted scope.
6. Decide:
   - pass -> closeout
   - fail/regression -> debugging

## Decision Gates

1. Evidence gate:
   - verification fails if expected output evidence is incomplete.
2. Audit gate:
   - for qualifying failures, verification fails if audit bundle is missing, unlinked, or incomplete per `docs/operating_system/rules/audit-evidence-mandate-rule.md`.
   - non-zero exit from `scripts/audit_check.py` is a hard fail.
3. Regression gate:
   - verification fails if new regressions are detected.
4. Contract gate:
   - reject fixes that pass run status but violate intended behavior/spec.

## Exit Criteria

- Verification pass with explicit evidence, regression assessment, required audit linkage, and passing audit_check result, or
- Verification fail with debug re-entry reason.
