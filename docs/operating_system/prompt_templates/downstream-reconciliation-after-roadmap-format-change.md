---
name: downstream-reconciliation-after-roadmap-format-change
description: Reconcile downstream planning and execution artifacts after roadmap format
  changes.
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
- docs/operating_system/workflows/workflow-roadmap-to-closeout.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Downstream Reconciliation After Roadmap Format Change

Use this prompt when `docs/intent/master-workstream-roadmap.md` has been updated to a new required format and downstream artifacts must be reconciled for both structure and content.

## Prompt

You are reconciling downstream planning artifacts after a **main roadmap format update**.

### Objective

Reconcile all downstream workstream/thread/spec/execution-map/plan files with the updated roadmap model, including:

- structure and required sections
- content alignment
- traceability
- dependency and child-item logic
- completion-rule consistency

This is not a cosmetic formatting pass.

### Required Inputs

1. Updated roadmap:
   - `docs/intent/master-workstream-roadmap.md`
2. Canonical templates and rules:
   - `docs/operating_system/templates/task-start-routing-guide.md`
   - `docs/operating_system/templates/master-workstream-roadmap-template.md`
   - `docs/operating_system/templates/registered-workstream-list-template.md`
   - `docs/operating_system/templates/bounded-change-thread-template.md`
   - `docs/operating_system/templates/complete-specification-set-template.md`
   - `docs/operating_system/templates/spec-authoring-map-template.md`
   - `docs/operating_system/templates/detailed-specification-template.md`
   - `docs/operating_system/templates/implementation-execution-map-template.md`
   - `docs/operating_system/templates/implementation-plan-template.md`
   - `docs/operating_system/governance/repo-governance.md`
   - `scripts/validate_planning_lifecycle.py`
   - `scripts/validate_template_required_sections.py`

### Execution Steps

1. Read the updated roadmap first.
2. Extract the roadmapâ€™s current model:
   - phases and ordering rules
   - per-phase Goal and per-phase Key Deliverables boundaries
   - workstream registry expectations
   - lifecycle/completion logic
   - traceability requirements
3. Identify all downstream files connected to the roadmap:
   - workstream registry/list files
   - bounded thread files
   - detailed specs
   - execution maps (`complete_spec_set`, `spec_authoring`, `implementation_execution`)
   - implementation plans
4. Build a reconciliation matrix per file:
   - file path
   - artifact type
   - expected template
   - required format deltas
   - required content deltas
   - traceability deltas
   - dependency/child-item deltas
   - completion-rule deltas
5. Update each downstream file:
   - preserve valid content
   - rewrite outdated/inconsistent sections
   - add missing traceability links
   - align dependency/child references with roadmap/workstream/thread reality
6. Do not invent new scope unless explicitly implied by the updated roadmap.
7. If a required decision is ambiguous, mark as unresolved gap with explicit options and impact.
8. Validate all updated files using template and lifecycle validators.

### Content-Change Decision Rules

Change **content**, not just formatting, when any of the following is true:

1. A section is structurally present but semantically inconsistent with roadmap intent.
2. Workstream/thread/spec/plan lineage references are missing, stale, or contradictory.
3. Dependencies or child items no longer match the updated roadmap ordering.
4. `Goal` or `Key Deliverables` exist but no longer represent current expected outcomes.
5. Phase-level Goal/Key Deliverables are mixed across phases or copied without
   phase-specific meaning.
6. Completion criteria allow closure that violates parent-child terminal-state rules.
7. Status/state metadata conflicts with current lifecycle validator rules.

Keep existing content only when it remains:

1. structurally valid for the target template
2. semantically aligned with updated roadmap intent
3. traceably linked to correct upstream/downstream artifacts

### Guardrails

1. Do not broaden scope beyond roadmap changes.
2. Do not silently drop unresolved inconsistencies.
3. Do not overwrite valid evidence/history unless incorrect.
4. Prefer explicit TODO gap notes over guessed decisions.
5. Keep terminology and status values consistent with governance rules.

### Validation Checklist

For every updated file, verify:

1. Correct template selected and `template_id` set (when required).
2. Required sections present with exact section names.
3. Required sections are non-empty, including `Goal` and `Key Deliverables`.
4. For roadmap docs, each phase has its own non-empty Goal and Key Deliverables.
5. No phase reuses another phase's deliverable list unless explicitly justified.
6. Frontmatter/artifact type matches template and file role.
7. Upstream traceability links are correct (roadmap/workstream/thread/spec).
8. Downstream references (children/dependencies) are current and coherent.
9. Completion rules align with terminal-child requirements.
10. No contradictory statuses across linked artifacts.
11. Validator pass status captured:
   - `python scripts/validate_template_required_sections.py`
   - `python scripts/validate_planning_lifecycle.py --strict` (or justify non-strict run)

### Final Report Format

Return a reconciliation report in this structure:

```md
# Downstream Reconciliation Report

## 1) Scope
- Roadmap source reviewed: `<path>`
- Downstream files discovered: `<count>`
- Files updated: `<count>`

## 2) Files Updated
- `<file-path>`
  - template alignment changes:
  - content changes:
  - traceability changes:
  - dependency/child changes:
  - completion-rule changes:

## 3) Unresolved Gaps
- `<gap-id>`: `<description>`
  - affected files:
  - why unresolved:
  - options:
  - recommended next action:

## 4) Validation Status
- `validate_template_required_sections.py`: pass | fail
- `validate_planning_lifecycle.py --strict`: pass | fail
- other checks run:

## 5) Downstream Risks
- `<risk>`
  - impact:
  - mitigation:
```
