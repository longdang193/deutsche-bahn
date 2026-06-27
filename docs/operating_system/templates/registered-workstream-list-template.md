---
template_id: registered-workstream-list
document_type: registered_workstream_list
target_globs:
- docs/superpowers/workstreams/registered-workstream-list.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Registered Workstreams
- Traceability
- Completion Criteria
distribution_tier: starter_kit
---

# Registered Workstream List Template

## Goal

<what this registered workstream set covers>

## Key Deliverables

Use this section for artifact-level outcomes such as ownership clarity, sequencing clarity, and roadmap coverage confidence.
Do not restate the canonical registry rows here.

### <deliverable 1>

Describe one concrete output this registered workstream set must provide, such as ownership clarity, sequencing coverage, or status visibility for the roadmap.

### <deliverable 2>

Describe another concrete output this workstream set must provide, such as gap detection, prioritization signal, or durable ownership mapping.

## Task/Wave Breakdown

Use this section for assembly and reconciliation sequence.
Do not duplicate the canonical workstream records here.

### Wave 1: Initial inventory and ownership pass

**Purpose:**
- identify all workstreams required by current roadmap coverage

**Steps:**
- [ ] extract workstream candidates from roadmap outcomes
- [ ] merge duplicate or overlapping lanes
- [ ] assign initial status and ownership intent
- [ ] identify obvious coverage gaps or unresolved boundaries

**Verification:**
- [ ] every major roadmap lane maps to a workstream or explicit gap note

**Exit Criteria:**
- initial workstream inventory is complete enough for refinement

### Wave 2: Sequencing and reconciliation pass

**Purpose:**
- refine the registered set so it is durable, traceable, and planning-ready

**Steps:**
- [ ] confirm workstream summaries and statuses
- [ ] confirm sequencing and dependency relationships
- [ ] confirm roadmap alignment for each registered workstream
- [ ] record deferred or unresolved items explicitly

**Verification:**
- [ ] registered workstream set has no unexplained ownership or sequencing gaps

**Exit Criteria:**
- registered workstream list is stable enough for downstream thread planning

## Registered Workstreams

This section is the canonical registry.
Keep durable records here; do not restate roadmap traceability prose or wave sequencing.

- `workstream_id`: <id>
  - status: <proposed|active|blocked|completed|dropped>
  - summary: <one line>

## Traceability

Use this section for source and reconciliation notes only.
Do not repeat the registry rows here.

- roadmap source: `docs/intent/master-workstream-roadmap.md`
- uncovered items: <item> | none
- merged or deferred items: <item> | none

## Completion Criteria

A workstream-list item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
