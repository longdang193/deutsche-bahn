---
template_id: complete-specification-set
document_type: complete_specification_set
target_globs:
- docs/superpowers/execution_maps/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Spec Inventory
- Coverage Check
- Completion Criteria
required_frontmatter:
  artifact_type: execution_map
  map_type: complete_spec_set
distribution_tier: starter_kit
---

# Complete Specification Set Template

## Goal

<what this full spec set enables>

## Key Deliverables

Use this section for artifact-level completeness outcomes only.
Do not repeat the canonical spec inventory or thread coverage matrix here.

### <deliverable 1>

Describe one concrete output this full specification set must provide, such as complete thread coverage, spec readiness, or removal of ambiguity before execution planning.

### <deliverable 2>

Describe another concrete output this spec set must provide, such as dependency completeness, sequencing clarity, or approval readiness.

## Task/Wave Breakdown

Use this section for the sequence of inventory, gap closure, and authoring readiness.
Do not duplicate canonical inventory rows or coverage lists here.

### Wave 1: Inventory existing specification coverage

**Purpose:**
- identify all existing or required specs relevant to covered threads

**Steps:**
- [ ] list current specs already covering in-scope threads
- [ ] map each spec to its primary purpose
- [ ] identify missing or partial coverage areas

**Verification:**
- [ ] every in-scope thread appears in inventory, partial-coverage list, or uncovered list

**Exit Criteria:**
- current specification landscape is fully visible

### Wave 2: Close coverage gaps

**Purpose:**
- determine what additional specifications are needed for complete coverage

**Steps:**
- [ ] define missing spec lanes
- [ ] record dependency relationships between specs
- [ ] classify which specs are ready, missing, or blocked

**Verification:**
- [ ] uncovered areas are reduced to explicit approved gaps only

**Exit Criteria:**
- complete required spec set is known

### Wave 3: Finalize authoring readiness

**Purpose:**
- prepare full specification set for downstream spec-authoring orchestration

**Steps:**
- [ ] confirm final inventory
- [ ] confirm dependency ordering
- [ ] confirm handoff to spec-authoring map

**Verification:**
- [ ] complete specification set is ready to drive authoring order

**Exit Criteria:**
- downstream spec-authoring orchestration can begin without re-inventory

## Spec Inventory

This section is the canonical specification registry.
Keep durable spec records here; do not restate thread coverage lists here.

- `docs/superpowers/specs/<spec-file>.md`
  - purpose: <one line>
  - status: <ready|missing|blocked>
  - depends_on:
    - <spec-path> | none

## Coverage Check

This section is the canonical thread-coverage view.
Do not repeat full spec inventory details here.

- covered threads:
  - <thread-id>
- partial coverage:
  - <thread-id> - <gap>
- uncovered threads:
  - <thread-id> | none

## Completion Criteria

A complete-spec-set item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
