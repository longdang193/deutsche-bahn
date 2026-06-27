---
name: validate-or-drift-prompt
description: Choose validation or drift-reconciliation path based on current artifact
  state.
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
tags:
- prompt
- drift
distribution_tier: starter_kit
---

# Validate Or Drift Prompt

Use this when you want to know what is missing, drifting, or outgrown.

Use this to discover problems first. If the repo is already managed and you
already know you want to update or repair managed surfaces, use
`managed-metadata-update-prompt.md`.
If the main question is whether execution has drifted from the roadmap or a
registered workstream, use `roadmap-vs-execution-divergence-prompt.md`.

```text
Check this repo for validation gaps, drift, or maturity signals.

Focus:
- missing docs:
- metadata drift:
- mode mismatch:
- starter drift:
- other concerns:

Please:
1. run the relevant validators or repo checks
2. report the real findings first
3. separate hard failures from warnings
4. say what should be fixed now vs later
5. recommend the next best move
```

Expected output:
- findings, severity, and next moves
