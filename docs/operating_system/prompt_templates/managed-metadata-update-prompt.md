---
name: managed-metadata-update-prompt
description: Update or repair managed architecture metadata in source-of-truth order.
type: prompt
stage: maintenance
entry_points:
- "repository is already in source_of_truth_owner (alias: managed_architecture_metadata) mode and metadata drift/fixes are needed"
- validator findings indicate managed metadata inconsistency across source and generated
  surfaces
prerequisites:
- adoption mode is known from repo_config/adoption-mode.yaml
- in-scope feature/stage/source metadata surfaces are identified
next_steps:
- implementation-next-action-gate-prompt.md
- validate-or-drift-prompt.md
related_skills:
- skill-doc-system-lifecycle
- skill-planning-dispatch
- skill-verification-before-completion
required_reads:
- docs/operating_system/governance/repo-governance.md
- docs/operating_system/adoption/project-adoption-migration-guide.md
- AGENTS.md
tags:
- prompt
- maintenance
- metadata
distribution_tier: starter_kit
---

# Managed Metadata Update Prompt

Use this when the repo is already in `managed_architecture_metadata` and you
want to update or repair managed metadata surfaces in place.

If the repo is still in `starter_method_only`, use
`mode-migration-prompt.md` first.

```text
Update or fix the managed architecture metadata surfaces for this repo.

Repo context:
- repo:
- adoption mode:
- in-scope managed surfaces:
- feature or stage source files that should change:
- known validator findings or drift:
- whether this is a targeted update, drift remediation, normalization pass, or generated refresh:
- roadmap thread this work follows (use a valid ID from `docs/intent/workstreams/`, or `none` if operating_system work):
- if `none`, why:

Please:
1. confirm whether the repo is already in managed mode, or say if migration is the better entrypoint
2. identify the human-owned source files that should change first
3. identify the generated outputs that should be refreshed later rather than hand-edited
4. update the managed metadata surfaces in the right source-of-truth order
5. run the canonical validator or sync/check path, or explain the required checks
6. summarize what changed, what was regenerated, and what drift still remains
```

Expected output:
- updated managed source files
- refreshed generated metadata outputs
- validator or sync/check results
- a spec or implementation plan when the work is too large for one safe pass
