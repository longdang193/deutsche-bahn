---
name: thread-closeout-readiness-prompt
description: Guide execution for thread closeout readiness prompt.
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

# Thread Closeout Readiness Prompt

## Not For

initial planning or spec drafting

## Verification Before Completion Trigger

Required when proposing thread closure (`completed` or `dropped`) or claiming fix/pass status:

- run `skill-verification-before-completion` checks before final close recommendation

Use this when deciding whether a bounded change thread can be marked
`completed` or `dropped`.

```text
Assess thread closeout readiness.

Please:
1. Decide whether this thread should close as `completed`, close as `dropped`, or remain open.
2. Validate closure requirements:
   - `completed` requires checkpoint result-pack evidence.
   - `dropped` requires explicit rationale metadata (`drop_reason`, `drop_approved_by`, `dropped_at`).
3. Verify completion semantics:
   - thread Goal and Key Deliverables are satisfied for `completed`.
   - evaluate each Key Deliverable as satisfied | unsatisfied with evidence.
4. List missing prerequisites (if any).
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
   - close as completed | close as dropped | continue execution | re-scope
```

Expected output:
- thread closeout verdict, concrete next actions, and one selected next action constrained by existing planning artifacts
