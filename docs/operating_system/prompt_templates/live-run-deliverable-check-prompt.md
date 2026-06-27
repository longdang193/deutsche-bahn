---
name: live-run-deliverable-check-prompt
description: Trigger live runs and evaluate whether in-scope deliverables are met with evidence-backed verification.
type: prompt
stage: execution
entry_points:
- need to run live system checks against deliverables
- need pass/fail evidence before closeout claim
prerequisites:
- deliverable list and acceptance criteria are explicit
- live-run environment and inputs are ready
next_steps:
- workflow-live-run-execution.md
- workflow-live-run-verification.md
- implementation-next-action-gate-prompt.md
related_skills:
- skill-verification-before-completion
- skill-systematic-debugging
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/workflows/workflow-live-run-system.md
tags:
- prompt
- live-run
- verification
distribution_tier: starter_kit
---

# Live Run Deliverable Check Prompt

## Not For

open-ended debugging without defined deliverables or acceptance criteria

```text
Trigger live runs to verify whether in-scope deliverables are met.

Context:
- roadmap/workstream/thread:
- deliverables to verify:
- acceptance criteria per deliverable:
- live-run command(s):
- environment/profile:
- known constraints/risks:

Please:
1. Confirm readiness before running:
   - criteria are testable and unambiguous
   - required environment/config/data is available
2. Execute live run(s) with bounded scope and capture evidence:
   - commands executed
   - logs/artifacts/traces produced
   - run IDs / timestamps
3. Evaluate each deliverable against acceptance criteria:
   - pass | fail | partial
   - exact evidence for verdict
4. If any deliverable fails:
   - identify failure boundary (stage/component/contract)
   - route to debugging workflow and propose one bounded next fix action
5. If all deliverables pass:
   - confirm verification-ready status
   - list closure prerequisites still required (if any)
6. Return one selected next action from existing artifacts only.
   - if closure criteria are already satisfied, return `close now` and explain why further actions are not eligible

Rules:
- no completion claim without run evidence
- no ambiguous verdicts; each deliverable must have explicit status and supporting evidence
- preserve traceability from command -> output -> verdict
```

Expected output:
- deliverable verification matrix with evidence links
- selected next action (debug, rerun, verification, or `close now`)
