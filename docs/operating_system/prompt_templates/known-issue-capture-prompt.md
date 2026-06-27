---
name: known-issue-capture-prompt
description: Record deferred issues with traceable impact, risk, and follow-up ownership.
type: prompt
stage: execution
entry_points:
- pattern detection found deferred likely/risk items
- unresolved bug findings must be recorded with owner and trigger
prerequisites:
- finding list exists with classification and evidence notes
- current workstream/thread context is identified
next_steps:
- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- maintenance
distribution_tier: starter_kit
---

# Known-Issue Capture Prompt

## Not For

resolving confirmed issues immediately in the same patch

```text
Capture deferred likely/risk findings as known issues.

Context:
- roadmap/workstream/thread in scope:
- source finding report path:
- deferred findings:

Please:
1. normalize each issue with:
   - issue id
   - classification: likely | risk
   - owner
   - trigger condition
   - required evidence to promote to confirmed
   - recommended next lane/prompt
2. remove duplicates and merge equivalent issues
3. identify one highest-priority issue for next execution
4. return one selected next action and why alternatives are not yet eligible
```

Expected output:
- normalized known-issue register entries and one selected next action
