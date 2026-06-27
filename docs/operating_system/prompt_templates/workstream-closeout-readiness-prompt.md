---
name: workstream-closeout-readiness-prompt
description: Guide execution for workstream closeout readiness prompt.
type: prompt
stage: closeout
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
- closeout
distribution_tier: starter_kit
---

# Workstream Closeout Readiness Prompt

## Not For

thread creation or spec authoring

## Verification Before Completion Trigger

Required when proposing workstream closure or claiming completion/pass status:

- run `skill-verification-before-completion` checks before final close recommendation

Use this when deciding whether a workstream can be marked `completed`.

```text
Assess workstream closeout readiness.

Please:
1. Validate workstream closure invariant:
   - workstream `completed` is allowed only when all child threads are terminal (`completed | dropped`).
2. Validate evidence readiness:
   - completed threads must have checkpoint result-pack evidence.
3. Verify completion semantics:
   - current Goal and Key Deliverables are still accurate for this workstream state.
   - evaluate each Key Deliverable as satisfied | unsatisfied with evidence.
4. List non-terminal or evidence-missing threads (if any).
5. Classify each blocker:
   - execution gap | evidence gap | status-hygiene gap | scope-decision gap
6. Recommend immediate next actions (top 3).
7. For the immediate next step, select one action only from existing artifacts:
   - roadmap/workstream/thread scope
   - approved specs
   - execution-map ordering/dependencies
   - current implementation plan tasks
   - open blockers and downstream impact
8. Return final recommendation:
   - close now | continue execution | re-scope
```

Expected output:
- workstream closeout verdict, concrete next actions, and one selected next action constrained by existing planning artifacts
