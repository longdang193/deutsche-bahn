---
name: workflow-test-failure-triage
description: Run the test failure triage workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-systematic-debugging
- skill-test-driven-development
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

# Test Failure Triage Workflow

## Purpose

Resolve failing tests systematically with minimal, spec-aligned fixes and no
unnecessary scope growth.

## Execution Flow

1. Reproduce the failing test(s).
2. Isolate failure boundary:
   - test-level
   - module-level
   - integration-level
3. Classify the failure:
   - regression
   - flaky
   - environment/config issue
   - spec mismatch
   - missing implementation
4. Audit gate:
   - if failure persists and is not proven flaky, create/update audit bundle at `docs/superpowers/plans/audit/<audit_id>/` using canonical template.
   - before closure for qualifying failures, run:

   ```powershell
   .\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
   ```
5. Define minimal required fix.
6. Apply fix.
7. Rerun targeted tests first.
8. Rerun full suite if needed by impact/risk.
9. Confirm stability and no unintended regressions.

## Decision Gates

1. Classification-before-fix gate:
   - do not implement until failure class is explicit.
2. Audit mandate gate:
   - persistent non-flaky failures require audit record (or explicit allowed bypass) per `docs/operating_system/rules/audit-evidence-mandate-rule.md`.
3. Minimal-fix gate:
   - reject broad refactors unless explicitly required to fix boundary.
4. Spec-alignment gate:
   - reject “make tests green only” fixes that violate intended behavior/spec.
5. Stability gate:
   - pass requires targeted rerun success; full rerun required when risk warrants.

## Anti-Patterns To Avoid

- overfitting logic only to satisfy one test path
- changing expected behavior without spec/intended-behavior justification
- expanding scope beyond minimal fix boundary

## Failure/Recovery Path

- if targeted rerun fails, reassess boundary/classification before adding new code
- if failure is flaky, treat stabilization as first-class task with evidence
- if environment/config issue, fix runtime/config root cause before code patching

## Exit Criteria

- failing tests are reproduced and classified
- required audit bundle exists for persistent non-flaky failures (or explicit bypass recorded)
- minimal fix is applied and justified
- targeted rerun passes
- full suite rerun passes when required
- no unintended regressions observed
