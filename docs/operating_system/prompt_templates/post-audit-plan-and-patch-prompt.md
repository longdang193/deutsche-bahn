---
name: post-audit-plan-and-patch-prompt
description: Guide post-audit routing to either plan-first or direct bounded patch, then pattern scan and validation.
type: prompt
stage: execution
entry_points:
- audit report completed and next implementation action is needed
- root cause and failure boundary are known and ready for remediation
prerequisites:
- audit findings are documented with evidence links
- failure boundary and affected components are identified
next_steps:
- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
related_skills:
- skill-systematic-debugging
- skill-writing-plans
- skill-executing-plans
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/rules/audit-evidence-mandate-rule.md
tags:
- prompt
- audit
- execution
distribution_tier: starter_kit
---

# Post-Audit Plan And Patch Prompt

## Not For

new issue intake before a failure boundary and root cause are known

```text
Use completed audit findings to plan and execute next bounded fix safely.

Context:
- audit_id:
- failure boundary:
- root cause summary:
- affected components:
- current evidence links:
- known constraints/contracts:

Please:
1. Decide whether to plan first or patch directly.
   - If scope is cross-file, contract-sensitive, or unclear, create a bounded patch plan first.
2. If planning is needed, produce a minimal implementation plan:
   - target files
   - exact behavior to change
   - invariants/contracts to preserve
   - verification steps
   - rollback/fallback notes
3. Apply patch with strict scope control:
   - no unrelated edits
   - preserve valid behavior
   - keep docs/templates/contracts aligned
4. Run pattern detection for similar failure modes in related files.
   - classify findings: confirmed | likely | risk
   - decide: fix now vs defer
5. Validate:
   - original issue resolved
   - no regressions introduced
   - contract and traceability preserved
6. Update audit bundle with outcomes and evidence links.
7. Return:
   - patch summary
   - files changed
   - pattern findings + decisions
   - verification results
   - one selected next action (or `close now` with reason)
```

Expected output:
- post-audit execution report with plan/patch decision, validation evidence, and one selected next action
