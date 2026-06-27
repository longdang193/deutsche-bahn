---
name: roadmap-closeout-readiness-prompt
description: Guide execution for roadmap closeout readiness prompt.
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

# Roadmap Closeout Readiness Prompt

## Not For

spec/plan authoring or implementation task selection

## Verification Before Completion Trigger

Required when proposing roadmap closure or claiming completion/pass status:

- run `skill-verification-before-completion` checks before final close recommendation

Use this when deciding whether a roadmap can be marked `completed`.

```text
Assess roadmap closeout readiness.

Please:
1. Validate roadmap closure invariant:
   - roadmap `completed` is allowed only when all registered workstreams are terminal (`completed | dropped`).
   - for any workstream closing as `completed`, downstream coverage is present:
     - complete spec set map
     - spec-authoring map
     - implementation execution map
     - linked detailed specs
     - linked implementation plans
   - completed threads under completed workstreams have checkpoint evidence.
2. Validate roadmap structure readiness:
   - each phase (`Phase 1/2/3`) has its own non-empty Goal and Key Deliverables.
   - phase deliverables are not mixed across phases.
3. Verify roadmap content readiness:
   - roadmap-level Goal/Key Deliverables remain accurate for current lifecycle state.
   - evaluate deliverable-by-deliverable satisfaction and mark each as satisfied | unsatisfied.
4. List non-terminal workstreams (if any) and why they remain open.
5. Classify each blocker:
   - execution gap | evidence gap | status-hygiene gap | scope-decision gap
6. Recommend immediate next actions (top 3) to reach closeable state.
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
- roadmap closeout verdict, concrete next actions, and one selected next action constrained by existing planning artifacts
