---
name: execution-readiness-gate-prompt
description: Decide whether execution can start based on planning completeness and
  dependencies.
type: prompt
stage: execution
entry_points:
- execution is being considered and readiness must be validated first
- next-action routing appears to jump to execution without sufficient artifacts
prerequisites:
- in-scope roadmap/workstream/thread/spec/plan context is identified or explicitly
  missing
- current blockers and dependency status are known
next_steps:
- implementation-next-action-gate-prompt.md
- multi-worktree-dispatch-prompt.md
related_skills:
- skill-planning-dispatch
- skill-executing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Execution Readiness Gate Prompt

## Not For

directly implementing changes before readiness status is explicit

```text
Assess execution readiness before next-action routing.

Context:
- roadmap/workstream/thread in scope:
- implementation plan path:
- related detailed spec(s):
- implementation execution map path:
- current completion statuses:
- unresolved issues:

Please:
1. verify scope classification is correct: intent | operating_system | workstream | change
2. verify required artifacts exist and are current:
   - thread/workstream context
   - required spec(s)
   - required plan/execution-map artifacts
3. verify unresolved blockers are explicitly classified
4. verify dependency order and downstream impact are coherent
5. decide whether lane split is required (single-lane vs multi-worktree)
6. return one readiness decision:
   - `ready_for_next_action`
   - `not_ready`
7. if `not_ready`, return one minimal prerequisite action needed to unblock
8. if `ready_for_next_action`, return one selected next action and why alternatives are not yet eligible
```

Expected output:
- readiness verdict (`ready_for_next_action` or `not_ready`) and one selected next step
