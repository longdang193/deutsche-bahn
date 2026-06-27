---
name: intent-prompt
description: Capture and refine project intent before roadmap and workstream planning.
type: prompt
stage: planning
entry_points:
- project purpose or direction is still unclear and intent must be clarified before
  planning artifacts
prerequisites:
- current problem context available
next_steps:
- master-workstream-roadmap-build-prompt.md
- roadmap-to-workstream-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Intent Prompt

## Not For

detailed spec, plan, or closeout decisions
Use this when you want the agent to help define project purpose before specs or
plans exist.

```text
Help me clarify project intent for this repo.

Context:
- problem to solve:
- target users:
- desired outcomes:
- constraints:
- non-goals:
- known risks or open questions:

Please:
1. classify this as intent work
2. identify the right docs/intent targets
3. draft or refine the intent docs
4. suggest the next likely workstreams or operating-system follow-ups
```

Expected output:
- intent direction or `docs/intent/*.md` updates
