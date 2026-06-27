---
name: live-run-closeout-decision-prompt
description: Guide execution for live run closeout decision prompt.
type: prompt
stage: closeout
entry_points:
- live-run verification finished and closeout decision is required
- closeout draft exists but readiness is uncertain
prerequisites:
- verification result and evidence bundle are available
- traceability from failure to fix to validation is available
next_steps:
- thread-closeout-readiness-prompt.md
- implementation-next-action-gate-prompt.md
related_skills:
- skill-verification-before-completion
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- closeout
distribution_tier: starter_kit
---

# Live Run Closeout Decision Prompt

## Not For

initial debugging before evidence capture and failure boundary identification

```text
Decide whether this live-run lane is closure-ready.

Please:
1. verify closure readiness against Goal and Key Deliverables in current scope
2. verify traceability: failure -> boundary -> fix -> rerun/verification evidence
3. list unresolved blockers and classify them (execution | evidence | scope | status)
4. decide one outcome:
   - close now
   - continue execution
   - return to debugging
   - re-scope
5. if not close now, return one minimal next action from existing artifacts only
6. explain why alternatives are not yet eligible
```

Expected output:
- closeout decision with evidence basis and one constrained next action when closure is blocked
