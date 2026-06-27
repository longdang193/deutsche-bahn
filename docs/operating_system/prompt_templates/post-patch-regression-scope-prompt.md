---
name: post-patch-regression-scope-prompt
description: Determine regression-check scope after a patch using risk and dependency
  impact.
type: prompt
stage: execution
entry_points:
- a patch was applied and regression validation scope must be decided
- uncertainty exists between targeted tests and broader/full regression
prerequisites:
- patch diff and affected components are known
- at least one targeted verification command is available
next_steps:
- implementation-next-action-gate-prompt.md
- thread-closeout-readiness-prompt.md
related_skills:
- skill-verification-before-completion
- skill-systematic-debugging
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Post-Patch Regression Scope Prompt

## Not For

initial patch design before any code change

```text
Decide the minimum sufficient regression scope after this patch.

Context:
- patch summary:
- affected files/modules/contracts:
- related workflows/specs:
- risk indicators:

Please:
1. classify impact scope: local | adjacent | cross-cutting
2. choose verification scope:
   - targeted only
   - targeted + expanded subset
   - full suite
3. justify choice with risk and dependency impact
4. list exact commands to run now
5. return one selected next action and why alternatives are not yet eligible
   - if closure criteria are already satisfied, select `close now`
```

Expected output:
- regression-scope decision, exact verification commands, and one selected next action
