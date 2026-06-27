---
name: workflow-live-run-closeout
description: Run the live run closeout workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-verification-before-completion
- skill-planning-dispatch
tags:
- workflow
- closeout
- change
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Live Run Closeout Workflow

## Goal

Finalize live-run resolution with durable evidence and route learnings into
tests, specs, and future scenarios.

## Execution Flow

1. Record root cause and failure boundary summary.
2. Record applied bounded fix and scope.
3. Record validation evidence proving resolution.
4. Audit gate:
   - if qualifying trigger applied, confirm audit bundle path and disposition (`open | mitigated | resolved | accepted-risk`).
   - run:

   ```powershell
   .\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
   ```

5. Identify follow-up updates for:
   - tests
   - specs
   - scenario catalog
6. Decide:
   - closeout ready -> pass to thread closeout readiness prompt
   - closeout blocked -> return to scenario planning for explicit follow-ups

## Decision Gates

1. Evidence gate:
   - no closeout without root cause/fix/validation evidence bundle.
2. Audit closure gate:
   - no closeout for qualifying problems without audit record (or explicit allowed bypass) and verification evidence linked.
   - non-zero exit from `scripts/audit_check.py` is a hard fail.
3. Learning gate:
   - at least one explicit backfeed decision is required
     (tests/specs/scenarios: update now, defer with reason, or no-change with reason).
4. Traceability gate:
   - closeout fails if linkage is missing.

## Exit Criteria

- Closeout bundle is complete, includes required audit linkage/disposition, passing audit_check result, and is actionable for lifecycle closure, or
- Blockers are explicitly recorded with next correction path.
