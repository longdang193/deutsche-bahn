---
name: workflow-prompt-metadata-spec
description: Run the workflow and prompt metadata specification procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-doc-system-lifecycle
tags:
- workflow
- maintenance
- operating_system
allowed-tools: []
required_outputs:
- docs/operating_system/workflows/
- .agents/skills/
distribution_tier: starter_kit
---

# Workflow And Prompt Metadata Specification

## Goal

Define one minimal metadata contract for `workflows/` and `prompt_templates/`
that supports routing and execution with low management overhead.

## Required Fields

Use YAML frontmatter at the top of each prompt/workflow file.

- `workflow_id` for workflow files, `prompt_id` for prompt files
- `type`: `workflow|prompt`
- `stage`: `planning|execution|closeout|drift|maintenance`
- `entry_points`: non-empty list
- `prerequisites`: non-empty list
- `next_steps`: non-empty list
- `owner_layer`: `intent|operating_system|workstream|change`
- `status`: `active|draft|deprecated`
- `skills`: non-empty list

Optional fields:

- `outputs`
- `validators`
- `notes`

## No Duplication Rule

If a field is in frontmatter, do not duplicate it as a routing/classification
section in the body.

Examples:

- metadata has `prerequisites`: do not add a body section that restates the same list
- metadata has `next_steps`: do not add a duplicate transition list in prose
- metadata has `skills`: do not add a second standalone skills catalog

The body should focus on execution logic:

- ordered actions
- decision gates
- evidence requirements
- failure and recovery handling
- exit criteria

## Agent Usage Model

1. Filter files by `type` and `stage`.
2. Match `entry_points` to observed context.
3. Check `prerequisites`; if missing, return minimal unblock action.
4. Execute body logic using listed `skills`.
5. Transition using `next_steps`.
6. Run listed `validators` when present.
