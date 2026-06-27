---
name: implementation-next-action-gate-prompt
description: Guide execution for implementation next action gate prompt.
type: prompt
stage: execution
entry_points:
- use this prompt when its title scope matches the current planning/execution need
prerequisites:
- relevant in-scope roadmap/workstream/thread/spec/plan context is available
next_steps:
- implementation-next-action-gate-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Implementation Next-Action Gate Prompt

## Not For

initial intent/roadmap construction
execution routing when planning readiness is not yet established

Use this after an agent completes part of an implementation plan and needs the
next allowed action.

```text
Determine the next execution action from existing planning artifacts only, including live-run trigger and verification actions when eligible.

Please:
1. verify what was completed against current item Key Deliverables
2. list unresolved problems and required adjustments
3. verify dependency order and downstream impact
4. identify next eligible action from existing plan/spec/map documents (implementation step, live-run trigger, verification, or closeout)
5. if no action is eligible, return the minimal prerequisite action needed to unblock
6. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now` and explain why further actions are not eligible
7. if next action is eligible and unblocked, execute the smallest concrete safe step now
8. refresh plan state and canonical context pack state as progress lands using:
   - template: `docs/operating_system/templates/execution-context-pack-template.md`
   - canonical path: `docs/superpowers/execution_context_packs/<lane-id>/latest.md`
   - governance: `docs/operating_system/governance/execution-context-pack-governance.md`
   - if selected action is `close now` and no new evidence landed, do not rewrite files; explicitly report "unchanged with reason"
9. if execution cannot proceed safely, return exact blocker and required user input/approval
```

Expected output:
- one constrained next action grounded in existing planning artifacts
- smallest concrete execution step performed now, or explicit blocker with required unblock input
- confirmation that plan state and canonical context pack state were updated, or explicitly unchanged with reason
