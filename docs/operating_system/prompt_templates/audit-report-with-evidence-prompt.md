---
name: audit-report-with-evidence-prompt
description: Guide creation and validation of mandatory audit report bundles using canonical template.
type: prompt
stage: execution
entry_points:
- qualifying technical failure detected and audit evidence required
- audit bundle missing or incomplete during debugging, verification, or closeout
prerequisites:
- failure boundary and core evidence are identified
- applicable trigger check completed against audit-evidence-mandate-rule.md
next_steps:
- implementation-next-action-gate-prompt.md
- live-run-closeout-decision-prompt.md
related_skills:
- skill-systematic-debugging
- skill-verification-before-completion
required_reads:
- docs/operating_system/rules/audit-evidence-mandate-rule.md
- docs/operating_system/templates/audit-report-with-evidence-template.md
tags:
- prompt
- audit
- evidence
distribution_tier: starter_kit
---

# Audit Report With Evidence Prompt

## Not For

non-qualifying routine changes that do not trigger audit mandate

```text
First, verify whether this work meets an audit trigger under the audit-evidence mandate.
If an audit-triggering failure is identified, create or update an audit bundle using the canonical template and evidence contract.

Inputs:
- audit_id:
- problem class / trigger reason:
- failure boundary (stage/component/contract):
- evidence sources (logs/traces/artifacts/repro):
- current bundle path (if exists):

Do:
1. Determine canonical path:
   - `docs/superpowers/plans/audit/<audit_id>/`
2. Ensure required structure exists:
   - `report.md`
   - `manifest.yaml`
   - `evidence/`
   - `repro/`
3. Create `report.md` from:
   - `docs/operating_system/templates/audit-report-with-evidence-template.md`
4. Populate report with source-grounded content only:
   - trigger/qualification rationale
   - boundary decision
   - attempted fix path and outcomes
   - verification evidence links
   - residual risks and disposition
5. Register evidence with durable references and checksums.
6. Run completeness gate:

   ```powershell
   .\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
   ```

7. If gate fails, return exact missing fields/files and minimal next action.
8. If gate passes, return bundle-ready confirmation with key evidence index.

Rules:
- no closure claim when audit gate fails
- no placeholder text in required sections
- no unresolved checklist items (`- [ ]`) in report sections that require decision/disposition
```

Expected output:
- audit bundle status (`pass`|`fail`)
- missing items list (if fail)
- next bounded action
