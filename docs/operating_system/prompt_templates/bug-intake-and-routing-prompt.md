---
name: bug-intake-and-routing-prompt
description: Classify a new bug and choose the correct debugging or patch route.
type: prompt
stage: execution
entry_points:
- a new bug report/failure is received and routing is not yet decided
- debugging started but bug class/severity is still ambiguous
prerequisites:
- initial bug evidence exists (error, failing test, artifact, or report)
- in-scope roadmap/workstream/thread context is available or explicitly unknown
next_steps:
- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
- live-run-system-dispatch-prompt.md
related_skills:
- skill-planning-dispatch
- skill-systematic-debugging
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- drift
distribution_tier: starter_kit
---

# Bug Intake And Routing Prompt

## Not For

claiming fixes before root-cause and route classification

```text
Classify this bug and select one routing path.

Context:
- roadmap/workstream/thread in scope:
- failure signal:
- affected components:
- known blockers:

Please:
1. classify bug type: runtime | test | contract | metadata | drift
2. classify severity: critical | high | medium | low
3. identify likely failure boundary and evidence strength
4. select one route:
   - live-run path
   - test-failure path
   - direct bounded patch path
   - drift reconciliation path
5. return one selected next action and why alternatives are not yet eligible
```

Expected output:
- bug class/severity, selected route, and one selected next action
