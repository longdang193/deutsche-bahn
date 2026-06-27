---
name: patch-and-pattern-detection-prompt
description: Guide execution for patch and pattern detection prompt.
type: prompt
stage: execution
entry_points:
- next eligible action is a bounded patch and recurrence risk should be checked
- a local fix is required and similar issues may exist across related artifacts
prerequisites:
- in-scope roadmap/workstream/thread/spec/plan context is identified
- concrete failure mode and target patch scope are identified
next_steps:
- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md
related_skills:
- skill-systematic-debugging
- skill-executing-plans
- skill-verification-before-completion
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Patch + Pattern Detection Prompt

## Not For

open-ended refactoring or broad redesign without a concrete failure boundary

```text
Please apply this patch, then check for similar issues in related files with bounded scope control.

Please:
1. Understand the patch in context:
   - what is broken, why, exact failure mode, and affected components
   - upstream intent linkage (roadmap/spec)
   - downstream impact linkage (implementation/execution/observability)
2. Apply the patch with strict controls:
   - minimal bounded scope
   - no unrelated edits
   - preserve valid behavior
   - keep templates/contracts/metadata alignment
3. Verify completion semantics where applicable:
   - Goal and Key Deliverables remain valid
   - StageResult and other required contracts remain valid
   - observability and traceability are not degraded
4. Detect similar problems (pattern detection):
   - derive failure pattern
   - scan similar files/workflows/specs/plans/stages
   - classify findings as confirmed | likely | risk
5. Decide scope per finding:
   - fix now (safe, low-risk, same pattern)
   - defer as follow-up patch
   - log as known issue
   - do not expand scope uncontrollably
6. Validate:
   - original issue resolved
   - no regressions introduced
   - contract/template consistency preserved
   - downstream dependencies remain valid
7. Return required output:
   - Patch summary (fix, root cause, affected components)
   - Changes applied (files + key modifications)
   - Pattern detection report (finding + classification + recommendation)
   - Scope decision (fixed now vs deferred)
   - Validation results (correctness/consistency/risks)
8. Return one selected next action from existing artifacts only and explain why alternatives are not yet eligible.
   - if closure criteria are already satisfied, return `close now` and explain why further actions are not eligible
```

Expected output:
- bounded patch implementation, structured pattern-detection report, and one selected next action (or `close now`)
