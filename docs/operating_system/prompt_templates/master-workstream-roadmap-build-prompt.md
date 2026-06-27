---
name: master-workstream-roadmap-build-prompt
description: Build a master workstream roadmap from intent with phase-structured deliverables.
type: prompt
stage: planning
entry_points:
- intent is clear and a master roadmap structure must be authored or revised
prerequisites:
- intent context is available
next_steps:
- registered-workstream-set-build-prompt.md
- downstream-reconciliation-after-roadmap-format-change.md
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

# Master Workstream Roadmap Build Prompt

## Not For

thread-level execution or implementation planning
Use this when intent exists but the major delivery threads needed to reach the
end goal have not yet been mapped clearly enough.

```text
Build or refine the master workstream roadmap from the current intent docs.

Context:
- intent docs:
- end goal:
- important outcomes:
- constraints and non-goals:
- known operating_system concerns:

Please:
1. identify the major delivery threads needed to reach the end goal
2. distinguish product workstreams from `operating_system`
3. call out missing or vague top-level threads
4. draft or refine the master workstream roadmap
5. recommend the next artifact after the roadmap
```

Expected output:
- a proposed or updated master workstream roadmap
- identified major delivery threads
- next recommended artifact, usually the registered workstream set
