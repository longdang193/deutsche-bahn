---
name: thread-set-to-spec-set-prompt
description: Convert a thread set into a complete specification set with traceability.
type: prompt
stage: planning
entry_points:
- thread set is known and complete spec inventory must be assembled
prerequisites:
- thread set in scope identified
next_steps:
- spec-set-to-spec-authoring-map-prompt.md
- spec-prompt.md
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

# Thread Set To Spec Set Prompt

## Not For

implementation-only sequencing
Use this when you already have a set of bounded change thread files and want to
determine the complete spec set needed before detailed-spec authoring and
implementation orchestration.

```text
Turn this thread set into the complete spec set.

Context:
- workstream or branch in scope:
- thread files in scope:
- known dependencies between threads:
- known shared surfaces:
- existing specs already visible through `docs/generated/planning_lineage.yaml`:

Please:
1. decide which threads need specs
2. decide whether any threads can share one spec
3. identify missing or redundant specs
4. produce the complete spec set for this thread set
5. recommend the next artifact after the spec set
```

Expected output:
- complete spec inventory for the thread set
- uncovered or redundant spec findings
- split/merge decisions across the thread set
- next artifact recommendation, usually a spec-authoring map
