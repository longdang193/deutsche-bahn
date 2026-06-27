---
name: planning-readiness-gate-prompt
description: Decide whether planning is sufficient to proceed to execution gating.
type: prompt
stage: execution
entry_points:
- work is being considered and planning/spec readiness must be decided first
- execution appears likely but feature/scope/design readiness is uncertain
prerequisites:
- initial scope/problem statement exists
- in-scope roadmap/workstream/thread context is available or explicitly unknown
next_steps:
- spec-prompt.md
- plan-prompt.md
- execution-readiness-gate-prompt.md
related_skills:
- skill-planning-dispatch
- skill-brainstorming
- skill-writing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/workflows/workflow-spec-to-plan-to-execution.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Planning Readiness Gate Prompt

## Not For

choosing execution actions before planning readiness is explicit

```text
Assess planning readiness before any execution gate.

Context:
- roadmap/workstream/thread in scope:
- problem statement:
- desired outcome:
- affected area/components:
- constraints:
- known blockers:

Please:
1. classify work type:
   - net-new feature/capability
   - behavior/contract change
   - bounded bugfix with no behavior expansion
   - metadata/documentation hygiene only
2. decide planning requirement:
   - `need_spec` (required for new feature/capability or behavior/contract change)
   - `need_plan` (required for multi-step or multi-lane implementation)
   - `ready_for_execution_gates` (only when scope/design are already sufficiently approved)
3. if `need_spec`, return one next action to draft/refresh spec
4. if `need_plan`, return one next action to draft/refresh implementation plan
5. if `ready_for_execution_gates`, return one next action to run execution-readiness gate
6. explain why alternatives are not yet eligible
```

Expected output:
- planning readiness verdict (`need_spec | need_plan | ready_for_execution_gates`) and one selected next action
