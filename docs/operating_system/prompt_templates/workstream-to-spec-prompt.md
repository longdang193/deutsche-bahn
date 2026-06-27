---
name: workstream-to-spec-prompt
description: Map workstream scope into detailed specification authoring tasks.
type: prompt
stage: planning
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
- docs/operating_system/workflows/workflow-roadmap-to-closeout.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Workstream To Spec Prompt

Use this when you already know both the workstream and the bounded change
thread that should advance next, and you want the spec for that thread.

If the next thread is not chosen yet, use
`bounded-change-thread-build-prompt.md` first.

```text
Draft the next spec that should advance this bounded change thread.

Workstream context:
- workstream id (use a valid ID from `docs/intent/workstreams/`):
- workstream doc:
- bounded change thread file:
- roadmap context:
- problem to solve next:
- desired outcome:
- constraints:
- invariants:

Please:
1. confirm the work belongs to this workstream
2. confirm the chosen bounded change thread is the right next slice
3. classify the bounded change
4. identify the owning docs and targets
5. draft the spec in docs/superpowers/specs/
6. recommend the next implementation step after the spec
```

Expected output:
- a spec in `docs/superpowers/specs/` tied to the chosen thread file
