---
name: live-run-system-dispatch-prompt
description: Route live-run work to the correct next workflow stage based on current
  state.
type: prompt
stage: execution
entry_points:
- live-run work is requested and the correct workflow entry point must be selected
- partial live-run state exists and needs deterministic routing
prerequisites:
- current run state and available artifacts are identified
- in-scope roadmap/workstream/thread/spec context is available
next_steps:
- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md
related_skills:
- skill-planning-dispatch
- skill-executing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/workflows/workflow-live-run-system.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Live Run System Dispatch Prompt

```text
Route this live-run task to the correct workflow entry point.

Context:
- roadmap/workstream/thread in scope:
- current live-run state:
- available artifacts/evidence:
- unresolved blockers:
- known run result (if any):

Rules:
1. Do not invent unrelated work.
2. Select from existing live-run workflows only:
   - workflow-live-run-system.md
   - workflow-live-run-scenario-planning.md
   - workflow-live-run-preflight-check.md
   - workflow-live-run-execution.md
   - workflow-live-run-debugging.md
   - workflow-live-run-verification.md
   - workflow-live-run-closeout.md
3. If prerequisites are missing, return the minimal unblock action first.
4. If failure exists, route to evidence-based debugging path.
5. If run passed, route to verification then closeout.

Return:
- selected workflow:
- why this entry point is eligible now:
- why alternatives are not eligible:
- immediate first step:
```

Expected output:
- one selected workflow entry point and one immediate, constrained first action
