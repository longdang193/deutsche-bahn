---
name: workflow-roadmap-to-closeout
description: Run the roadmap to closeout workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-planning-dispatch
tags:
- workflow
- closeout
- intent
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Roadmap To Closeout Workflow

## Purpose

Run a deterministic closure path from active roadmap/workstream/thread state to safe roadmap closeout.

## Entry Criteria

- roadmap/workstream/thread lineage is identified
- current statuses and known blockers are available
- relevant specs/plans/checkpoint evidence are discoverable

## Steps (Ordered)

<LINK>
1. Run thread closure review with [thread-closeout-readiness-prompt.md](../prompt_templates/thread-closeout-readiness-prompt.md)
2. Resolve thread blockers using [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
3. Run workstream closure review with [workstream-closeout-readiness-prompt.md](../prompt_templates/workstream-closeout-readiness-prompt.md)
4. Resolve workstream blockers using [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
5. Run roadmap closure review with [roadmap-closeout-readiness-prompt.md](../prompt_templates/roadmap-closeout-readiness-prompt.md)
6. If closure-ready, run final verification and close
</LINK>

## Decision Gates

- thread gate: close as `completed` or `dropped` only when closure requirements pass
- workstream gate: close only when all child threads are terminal and evidence-complete
- roadmap gate: close only when lifecycle, structure, and deliverable checks pass

## Exit Criteria

- roadmap closure decision returned (`close now` or explicit blocker path)
- if `close now`, validations pass and status update is justified

## Related Prompts

<LINK>
- [thread-closeout-readiness-prompt.md](../prompt_templates/thread-closeout-readiness-prompt.md)
- [workstream-closeout-readiness-prompt.md](../prompt_templates/workstream-closeout-readiness-prompt.md)
- [roadmap-closeout-readiness-prompt.md](../prompt_templates/roadmap-closeout-readiness-prompt.md)
- [implementation-next-action-gate-prompt.md](../prompt_templates/implementation-next-action-gate-prompt.md)
</LINK>

## Failure/Recovery Path

- if closeout gate fails, classify blocker (`execution|evidence|status-hygiene|scope-decision`)
- select one bounded next action via next-action gate prompt
- re-run the failed gate only after blocker completion
