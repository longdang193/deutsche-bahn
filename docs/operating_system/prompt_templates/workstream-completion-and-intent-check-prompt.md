---
name: workstream-completion-and-intent-check-prompt
description: Check workstream completion against intent-level outcomes and deliverables.
type: prompt
stage: drift
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

# Workstream Completion And Intent Check Prompt

Use this when a long-running workstream may have drifted and you want a clear
completion verdict against original intent.
If you mainly want a divergence map without a completion verdict, use
`roadmap-vs-execution-divergence-prompt.md` instead.
If you mainly want a closure-eligibility decision, use
`workstream-closeout-readiness-prompt.md` instead.

```text
Evaluate whether this workstream is complete and still aligned with intent.

Context:
- workstream id:
- workstream doc:
- intent sources (`docs/intent/*.md`):
- bounded thread files:
- related specs:
- related plans:
- related checkpoint result packs:
- known merged changes:
- known open risks or blockers:

Please:
1. read original intent sources first, then the workstream and its bounded threads
2. compare intent/workstream promises against specs, plans, checkpoint packs, and merged outcomes
3. separate complete, partial, missing, and drifted scope
4. reconcile each bounded thread status with the latest checkpoint result-pack evidence
5. evaluate workstream Goal and each Key Deliverable as satisfied | unsatisfied with evidence
6. call out misclassified `operating_system` work if present
7. decide completion verdict: `complete` | `partial` | `not_complete`
8. recommend next decision: `close` | `continue` | `re-scope`
9. list the minimum concrete follow-up actions
10. before recommending `close`, confirm these checks are expected to pass:
   - `python scripts/validate_planning_lifecycle.py --strict`
   - `python scripts/validate_checkpoint_packs.py`
   - `python scripts/validate_repo_contracts.py --fast`
```

Expected output:
- completion verdict against intent
- explicit done/missing/drifted breakdown
- next decision and concrete follow-up actions
