---
template_id: master-workstream-roadmap
document_type: master_workstream_roadmap
target_globs:
- docs/intent/master-workstream-roadmap.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Workstream Index
- Completion Criteria
distribution_tier: starter_kit
---

# Master Workstream Roadmap Template

## Goal

<what this roadmap is trying to achieve>

## Key Deliverables

Use this section for roadmap-wide outcomes only.
Do not restate phase sequencing, phase gates, or workstream-registry details here.

### <deliverable 1>

Describe one concrete roadmap-wide outcome this document must deliver, including scope, intended result, and how success will be recognized at roadmap level.

### <deliverable 2>

Describe one additional roadmap-level outcome this document must deliver, including why it matters and which downstream workstreams it enables.

## Task/Wave Breakdown

Use `Phase` blocks for strategic sequencing.
Within each phase:

- `Goal` owns the phase outcome
- `Depends On` and `Enables` own sequencing context
- `Exit Criteria` owns the gate for moving to later phases

Do not restate roadmap-wide Key Deliverables or copy the Workstream Index into phase prose.

### Phase 1: <phase name>

#### Goal

<phase-1 outcome>

#### Enables

- <downstream phase, workstream, or decision this phase unlocks>

#### Exit Criteria

- <what must be true before later phases can safely begin>

### Phase 2: <phase name>

#### Goal

<phase-2 outcome>

#### Depends On

- Phase 1

#### Enables

- <downstream phase, workstream, or decision this phase unlocks>

#### Exit Criteria

- <what must be true before later phases can safely begin>

### Phase 3: <phase name>

#### Goal

<phase-3 outcome>

#### Depends On

- Phase 2

#### Exit Criteria

- <what proves the roadmap target state is complete or ready for closeout>

## Workstream Index

This section is the canonical workstream registry for the roadmap.
Do not restate phase sequencing here.

- `<workstream-id>` - <summary>

## Completion Criteria

A roadmap item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
