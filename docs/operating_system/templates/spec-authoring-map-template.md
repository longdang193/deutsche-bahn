---
template_id: spec-authoring-map
document_type: spec_authoring_map
target_globs:
- docs/superpowers/execution_maps/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Parallel Lanes
- Completion Criteria
required_frontmatter:
  artifact_type: execution_map
  map_type: spec_authoring
distribution_tier: starter_kit
---

# Spec-Authoring Map Template

## Goal

<what this authoring map must orchestrate>

## Key Deliverables

Use this section for artifact-level authoring outcomes only.
Do not restate canonical lane membership or wave sequencing details here.

### <deliverable 1>

Describe one concrete authoring outcome this map must deliver, such as a completed spec subset, sequencing decision, or dependency-resolved drafting lane.

### <deliverable 2>

Describe another concrete authoring result this map must deliver, such as clearer lane ownership, reduced drafting risk, or resolved sequencing.

## Task/Wave Breakdown

Use this section for wave ordering, merge points, and dependency rationale.
Do not duplicate the canonical lane registry here.

### Wave 1: Foundational authoring lanes

**Purpose:**
- start with specs that unblock later design work

**Starts First Because:**
- <dependency reason>

**Lane Goals:**
- <goal 1>
- <goal 2>

**Verification:**
- [ ] foundational specs are sufficient to unblock dependent lanes

**Exit Criteria:**
- dependent spec lanes can start without guessing

### Wave 2: Parallel authoring and dependency handling

**Purpose:**
- author follow-on specs in safe parallel or staged lanes

**Steps:**
- [ ] assign specs to lanes
- [ ] confirm lane dependencies
- [ ] identify merge or review points
- [ ] record any unresolved drafting risks

**Verification:**
- [ ] lane ordering and dependencies are explicit

**Exit Criteria:**
- parallel spec work can proceed without boundary confusion

### Wave 3: Reconciliation and approval readiness

**Purpose:**
- consolidate authored specs into one coherent design set

**Steps:**
- [ ] reconcile overlapping decisions
- [ ] confirm missing coverage is closed or deferred explicitly
- [ ] prepare handoff to implementation execution map

**Verification:**
- [ ] authored spec set is coherent and handoff-ready

**Exit Criteria:**
- approved design can move into implementation orchestration

## Parallel Lanes

This section is the canonical lane registry.
Keep lane membership and dependencies here; do not restate wave rationale here.

- lane A:
  - specs:
    - <spec>
  - depends_on:
    - <lane> | none
  - unblock_targets:
    - <lane or decision>
- lane B:
  - specs:
    - <spec>
  - depends_on:
    - <lane> | none
  - unblock_targets:
    - <lane or decision>

## Completion Criteria

A spec-authoring-map item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
