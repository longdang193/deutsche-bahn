---
name: bounded-change-thread-build-prompt
description: Define a bounded change thread with clear scope, ownership, and completion
  criteria.
type: prompt
stage: planning
entry_points:
- a workstream exists and bounded executable thread slices must be created/refined
prerequisites:
- workstream id/path known
next_steps:
- thread-set-to-spec-set-prompt.md
- workstream-to-spec-prompt.md
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

# Bounded Change Thread Build Prompt

## Not For

roadmap closure decisions
Use this when a registered workstream exists and you want to break it into
discrete, execution-capable slices.

```text
Break this workstream into bounded change threads.

Context:
- workstream id:
- workstream doc:
- jobs to be done / success signals:
- known open gaps:
- known dependencies:
- possible shared surfaces:

Please:
1. identify bounded change threads beneath the workstream
2. separate independent slices from dependency-coupled slices
3. call out shared-surface and sequencing risks
4. recommend which threads need specs first
5. recommend the next artifact after the bounded change thread list
6. format the result so it can be turned directly into lightweight thread files
```

Expected output:
- bounded change thread candidates mapped to proposed thread files under
  `docs/intent/workstreams/threads/<workstream-id>/`
- dependency and shared-surface notes
- per-thread status and short goal statements
- next recommended artifact, usually a spec for one bounded change thread
