---
name: workflow-drift-detection-and-reconciliation
description: Run the drift detection and reconciliation workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-planning-dispatch
tags:
- workflow
- drift
- operating_system
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Drift Detection And Reconciliation Workflow

## Purpose

Detect drift against roadmap/workstream intent and reconcile downstream artifacts without inventing scope.

## Entry Criteria

- suspected drift, stale statuses, or mismatched artifacts are observed
- relevant roadmap/workstream/thread/spec/plan surfaces are identified

## Steps (Ordered)

<LINK>
1. Run drift discovery with [validate-or-drift-prompt.md](../prompt_templates/validate-or-drift-prompt.md)
2. Run divergence review with [roadmap-vs-execution-divergence-prompt.md](../prompt_templates/roadmap-vs-execution-divergence-prompt.md)
3. If roadmap model changed, run [downstream-reconciliation-after-roadmap-format-change.md](../prompt_templates/downstream-reconciliation-after-roadmap-format-change.md)
4. Select one bounded correction action via [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
5. Repeat until blockers are cleared or explicitly escalated
</LINK>

## Decision Gates

- drift gate: confirm real drift vs healthy evolution
- reconciliation gate: ensure updates preserve lineage/dependency/completion semantics
- scope gate: reject unrelated work not implied by approved artifacts

## Exit Criteria

- drift inventory resolved or explicitly documented with next actions
- validation status captured for corrected artifacts
- if an active execution plan was reconciled, its status/checklists reflect the corrected completed, blocked, or deferred state

## Related Prompts

<LINK>
- [validate-or-drift-prompt.md](../prompt_templates/validate-or-drift-prompt.md)
- [roadmap-vs-execution-divergence-prompt.md](../prompt_templates/roadmap-vs-execution-divergence-prompt.md)
- [downstream-reconciliation-after-roadmap-format-change.md](../prompt_templates/downstream-reconciliation-after-roadmap-format-change.md)
- [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
</LINK>

## Failure/Recovery Path

- if reconciliation is ambiguous, record unresolved gaps with options and impact
- pick minimum prerequisite action via next-action gate prompt
- defer closure recommendations until blockers are resolved
