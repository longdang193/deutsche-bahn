---
name: parent-complete-only-when-children-terminal-prompt
description: Validate parent completion only when all child items are terminal.
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

# Parent Complete Only When Children Terminal Prompt

Deprecated: prefer scoped closeout prompts instead:

- `roadmap-closeout-readiness-prompt.md`
- `workstream-closeout-readiness-prompt.md`
- `thread-closeout-readiness-prompt.md`

Use this only for ad hoc parent/child checks outside normal roadmap/workstream/
thread closure flows.

```text
Check and enforce this lifecycle invariant:
parent can be `completed` only when all children are terminal.

Scope:
- parent type: workstream | thread-group | other
- parent id/path:
- child source (paths/ids):
- terminal statuses allowed: `completed`, `dropped`

Please:
1. list all children under the parent
2. classify each child status as terminal or non-terminal
3. if parent is `completed` and any child is non-terminal, mark invariant failure
4. propose exact metadata updates needed to reconcile
5. if child is `dropped`, ensure rationale metadata is present (or call out missing fields)
6. report final closeability decision: `can_close: true|false`
```

Expected output:
- child status table
- invariant pass/fail result
- exact remediation actions
- `can_close` decision
