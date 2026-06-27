---
name: lifecycle-readiness-and-proceed-prompt
description: Assess lifecycle readiness and choose the minimal safe proceed path.
type: prompt
stage: maintenance
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
- maintenance
distribution_tier: starter_kit
---

# Lifecycle Readiness And Proceed Prompt

Use this when you need to check incomplete lifecycle state and decide concrete
next execution actions, not just metadata/doc updates.

```text
Run a lifecycle closure-readiness review and decide the next execution path.

Scope:
- roadmap/workstream/thread lineage in scope:
- related specs/plans/execution maps/checkpoint result packs:
- current statuses:

Goal:
Identify what is incomplete, what is blocked, and the exact next execution path.
Do not stop at metadata/doc updates alone.

Please:
1. Validate closure invariants across lineage:
   - roadmap -> workstream
   - workstream -> thread
   - thread -> checkpoint result-pack evidence
2. List incomplete items by layer:
   - roadmap | workstream | thread | spec | execution map | plan | checkpoint
3. Classify each gap:
   - execution gap | evidence gap | status-hygiene gap | scope-decision gap
4. For each gap, recommend one next action:
   - implement now
   - create bounded thread/spec/plan
   - reconcile status/evidence
   - drop explicitly with rationale
5. Produce a proceed plan:
   - immediate next 3 actions
   - owner per action
   - validation commands after each action
6. Return final recommendation:
   - close now | continue execution | re-scope

Required output:
- readiness verdict
- incomplete inventory
- gap classification table
- proceed plan (next 3 actions)
- blocking risks
- final recommendation
```

Expected output:
- a concrete readiness assessment and next-action execution path
