---
name: brainstorming-detailed-report-generation-prompt
description: Generate detailed brainstorming report from completed brainstorming output using canonical report template.
type: prompt
stage: planning
entry_points:
- brainstorming output already shared and user explicitly asks for detailed report
prerequisites:
- completed brainstorming output in current thread
- explicit user confirmation to generate detailed report
next_steps:
- hand report back to user for validation and decision
related_skills:
- skill-brainstorming
required_reads:
- docs/operating_system/templates/brainstorming-detailed-report-template.md
- docs/superpowers/plans/brainstorming/README.md
- .agents/skills/skill-brainstorming/SKILL.md
tags:
- prompt
- planning
- brainstorming
distribution_tier: starter_kit
---

# Brainstorming Detailed Report Generation Prompt

## Not For

initial brainstorming, implementation planning, or code execution

```text
Create detailed report from completed brainstorming output in this thread.

Hard requirements:
1. Determine canonical bundle path:
   docs/superpowers/plans/brainstorming/<report_id>/
2. Ensure bundle scaffold exists:
   .\scripts\new_brainstorming_report.ps1 -ReportId <report_id>
3. Write report at:
   docs/superpowers/plans/brainstorming/<report_id>/report.md
4. Follow this template exactly:
   docs/operating_system/templates/brainstorming-detailed-report-template.md
5. Use only facts, constraints, and options already present in thread context.
6. Do not invent missing details. If critical information is missing, state that in final section.
7. Keep writing concise, concrete, and decision-oriented.
8. Return:
   - report path
   - brief completion status
```

Expected output:

- saved report bundle path and completed report content at canonical location
