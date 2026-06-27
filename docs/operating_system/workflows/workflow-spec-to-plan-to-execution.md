---
name: workflow-spec-to-plan-to-execution
description: Run the spec to plan to execution workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-planning-dispatch
tags:
- workflow
- planning
- change
allowed-tools: []
required_outputs:
- docs/superpowers/specs/
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Spec To Plan To Execution Workflow

## Purpose

Move from approved bounded work item context to controlled execution and closeout readiness.

## Entry Criteria

- bounded thread context (or explicit operating_system justification) is known
- approved spec context exists or can be drafted

## Steps (Ordered)

<LINK>
1. Draft detailed spec with [spec-prompt.md](../prompt_templates/spec-prompt.md)
2. If multi-spec sequencing is needed, create map via [spec-set-execution-map-prompt.md](../prompt_templates/spec-set-execution-map-prompt.md)
3. Build execution-ready plan with [plan-prompt.md](../prompt_templates/plan-prompt.md)
4. Execute with [execute-prompt.md](../prompt_templates/execute-prompt.md)
5. Select each next bounded action using [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
6. If completion is claimed, transition into closeout ladder
</LINK>

## Decision Gates

- spec gate: design decisions are explicit and bounded
- planning gate: plan has clear lineage, tasks, verification
- execution gate: next action is selected only from existing artifacts and the active plan reflects completed, blocked, or deferred work truthfully

## Exit Criteria

- execution completed for current bounded scope, or
- blocked state documented with one minimal prerequisite next action
- executing plan status/checklists are updated to match actual completed, blocked, or deferred work before closeout

## Related Prompts

<LINK>
- [spec-prompt.md](../prompt_templates/spec-prompt.md)
- [spec-set-execution-map-prompt.md](../prompt_templates/spec-set-execution-map-prompt.md)
- [plan-prompt.md](../prompt_templates/plan-prompt.md)
- [execute-prompt.md](../prompt_templates/execute-prompt.md)
- [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
</LINK>

## Failure/Recovery Path

- if no eligible next action exists, return minimum prerequisite unblock action
- if scope ambiguity emerges, reroute via skill-planning-dispatch before continuing
- if completion is claimed, run skill-verification-before-completion gate
