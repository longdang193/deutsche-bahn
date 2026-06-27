---
name: thread-checkpoint-result-pack-prompt
description: Create a checkpoint result pack for thread-level execution evidence.
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
- docs/operating_system/workflows/workflow-roadmap-to-closeout.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Thread Checkpoint Result Pack Prompt

Use this when a bounded change thread had an execution pass and you want a
visible checkpoint artifact with standardized status and outputs.

```text
Create a bounded-thread checkpoint result pack for this execution pass.

Context:
- workstream id (valid ID from `docs/intent/workstreams/`):
- thread id (valid ID from `docs/intent/workstreams/threads/`):
- thread file path:
- thread status (proposed | active | blocked | completed):
- execution pass timestamp (UTC):
- owner (person or agent):
- key commands run:
- files changed:
- verification outputs:
- artifacts produced:

Please:
1. confirm this is the right bounded change thread checkpoint unit
2. summarize the execution intent in one concise section
3. record concrete actions taken
4. include visible outputs (artifacts, verification summary, and diff summary)
5. set checkpoint status as `pass`, `partial`, or `fail`
6. write the next decision as one of: continue, fix-forward, rollback, pause and re-scope
7. write the checkpoint file under
   `docs/intent/workstreams/checkpoints/<workstream-id>/<thread-slug>/`
8. follow `docs/operating_system/templates/checkpoint-result-pack.md`
```

Expected output:
- one checkpoint result-pack Markdown file at
  `docs/intent/workstreams/checkpoints/<workstream-id>/<thread-slug>/`
