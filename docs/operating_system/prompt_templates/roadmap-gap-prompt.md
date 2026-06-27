---
name: roadmap-gap-prompt
description: Identify roadmap coverage gaps and propose bounded corrective additions.
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
- drift
distribution_tier: starter_kit
---

# Roadmap Gap Prompt

Use this when you think the master roadmap may be missing an important durable
thread.

If the roadmap already exists and you want to compare it against execution so
far, use `roadmap-vs-execution-divergence-prompt.md` instead.

```text
Assess whether the master roadmap is missing a real workstream or just needs refinement.

Gap context:
- intent docs:
- roadmap section reviewed:
- missing need or repeated request:
- why it seems durable:
- known related workstreams:

Please:
1. assess whether this is a real roadmap gap, an existing workstream that needs refinement, or operating_system work
2. recommend whether to add a new workstream, refine an existing one, or leave the roadmap unchanged
3. name the next artifact to create
4. explain the recommendation briefly
```

Expected output:
- gap assessment plus the recommended next artifact
