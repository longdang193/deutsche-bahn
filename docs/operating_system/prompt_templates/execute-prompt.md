---
name: execute-prompt
description: Guide execution for execute prompt.
type: prompt
stage: execution
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
- execution
distribution_tier: starter_kit
---

# Execute Prompt

## Not For

planning from scratch
Use this when an implementation plan already exists and you want the agent to
carry it out.

## Verification Before Completion Trigger

Required when claiming completion of a plan/task set or pass/fix status:

- run `skill-verification-before-completion` checks before final completion claim

If you are still deciding which roadmap thread the work belongs to, use
`roadmap-to-workstream-prompt.md` or `workstream-alignment-review-prompt.md`
before this prompt.

```text
Execute this implementation plan in this session.

Please:
1. review the plan critically before starting
2. confirm the execution still matches the roadmap thread or the operating-system justification
3. implement it task by task
4. keep source-of-truth docs in sync as changes land
5. keep plan state and canonical context pack state synchronized as progress lands using:
   - template: `docs/operating_system/templates/execution-context-pack-template.md`
   - canonical path: `docs/superpowers/execution_context_packs/<lane-id>/latest.md`
   - governance: `docs/operating_system/governance/execution-context-pack-governance.md`
   - optional mirror: `artifacts/execution_context_pack.md`
6. determine each next action using `implementation-next-action-gate-prompt.md`; do not invent unrelated next steps
7. run the relevant verification commands
8. if this execution closes a plan/workstream, run the closeout gate checks:
   - `python scripts/validate_planning_lifecycle.py --strict`
   - `python scripts/validate_checkpoint_packs.py`
   - `python scripts/validate_repo_contracts.py --fast`
9. summarize what changed and what still needs follow-up
```

Expected output:
- implemented changes plus verification results
- explicit note that plan state and canonical context pack state were updated during execution, or explicit reason they were unchanged
