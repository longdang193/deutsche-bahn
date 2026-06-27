---
name: audit-evidence-mandate-rule
description: Enforce mandatory audit report with evidence for qualifying problem classes before closure claims.
alwaysApply: true
required_reads:
- docs/operating_system/governance/repo-governance.md
- AGENTS.md
tags:
- rule
- audit
- evidence
distribution_tier: starter_kit
---

# Audit Evidence Mandate Rule

## Purpose

Require durable audit evidence for qualifying problems before resolution claims.

## Principle

When qualifying problem exists without active audit record, team MUST draft audit report and attach evidence bundle before marking issue resolved.

## Qualifying Problem Triggers

Audit is required when any of these conditions is true:

1. persistent test failure not proven flaky
2. live-run/runtime failure with user-impacting behavior
3. data-quality anomaly affecting outputs/decisions
4. security/privacy/control failure
5. contract/invariant drift where failure boundary is unclear

## Allowed Bypass

Audit may be skipped only when one of these conditions is true:

1. docs-only or typo-only change with no behavior impact
2. existing active audit already tracks same failure fingerprint and scope

Bypass MUST be stated explicitly in closeout evidence.

## Required Audit Outputs

Canonical template:

- `docs/operating_system/templates/audit-report-with-evidence-template.md`

Canonical storage root:

- `docs/superpowers/plans/audit/<audit_id>/`

Minimum required artifacts:

- `report.md`
- `manifest.yaml`
- evidence files (image/json/log/txt) linked from report
- deterministic reproduction steps/commands
- expected vs actual result statement

## Closure Gate

No completion/closeout claim for qualifying problem unless all are true:

1. audit record exists (or explicit allowed bypass recorded)
2. evidence bundle is linked and traceable
3. verification evidence confirms resolution or accepted-risk status
4. status is explicit: `open | mitigated | resolved | accepted-risk`

## Anti-Duplication Rule

- Skills/workflows must reference canonical template and storage path.
- Do not embed duplicate full audit templates in skill/workflow docs.

## Governance Notes

This rule defines audit requirement only. Debugging method, verification method, and lifecycle routing remain owned by existing canonical operating-system docs and workflows.
