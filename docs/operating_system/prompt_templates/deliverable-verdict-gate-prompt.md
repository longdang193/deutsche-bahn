---
name: deliverable-verdict-gate-prompt
description: Assess whether in-scope deliverables are met using explicit criteria and evidence-backed verdicts.
type: prompt
stage: execution
entry_points:
- need objective verdict on whether deliverables are met
- closeout/readiness decision requires deliverable-level evidence
prerequisites:
- in-scope deliverables and acceptance criteria are identified
- at least one evidence source is available (or explicitly missing)
next_steps:
- implementation-next-action-gate-prompt.md
- workflow-live-run-verification.md
- workflow-live-run-debugging.md
related_skills:
- skill-verification-before-completion
- skill-systematic-debugging
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- verification
- deliverables
distribution_tier: starter_kit
---

# Deliverable Verdict Gate Prompt

## Not For

initial planning when acceptance criteria are not yet defined

```text
Assess whether in-scope deliverables are met, partially met, or not met, using available evidence and explicit acceptance criteria.

Context:
- roadmap/workstream/thread:
- deliverables in scope:
- acceptance criteria per deliverable:
- current evidence (runs/tests/logs/artifacts/reviews):
- known gaps or blockers:

Please:
1. Evaluate each deliverable against its acceptance criteria.
2. Assign one status per deliverable:
   - met
   - partially met
   - not met
   - cannot determine (missing evidence)
3. For each status, provide exact evidence links and short rationale.
4. For partially met / not met / cannot determine:
   - identify failure/gap boundary (component/contract/step)
   - list minimal action needed to reach “met” or to collect missing evidence
5. Return overall readiness:
   - ready for closeout
   - needs more verification
   - needs implementation/debugging
6. Return one selected next action from existing artifacts only.
   - if closure criteria are already satisfied, return `close now` and explain why further actions are not eligible

Rules:
- no “met” verdict without direct evidence
- no ambiguous status; every deliverable must have one explicit verdict
- keep scope bounded to in-scope deliverables only

Expected output:
- deliverable verdict matrix (deliverable, criteria, status, evidence, gap, next step)
- overall readiness decision
- one constrained next action
```
