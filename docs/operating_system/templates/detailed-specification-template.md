---
template_id: detailed-specification
document_type: detailed_specification
target_globs:
- docs/superpowers/specs/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Design Decisions
- Invariants
- Validation Plan
- Completion Criteria
required_frontmatter:
  artifact_type: spec
distribution_tier: starter_kit
---

# Detailed Specification Template

## Goal

<what this specification must define>

## Key Deliverables

Use this section for artifact-level design outcomes only.
Do not restate detailed decisions, invariants, or proof methods here.

### <deliverable 1>

Describe one concrete specification outcome this document must deliver, such as a resolved design boundary, contract decision, or validated implementation constraint.

### <deliverable 2>

Describe another concrete specification result this document must deliver, such as clarified invariants, interface shape, or validation confidence.

## Task/Wave Breakdown

Use this section for progression from source-first analysis into decision closure and validation readiness.
Do not duplicate the canonical decision, invariant, or validation records here.

### Wave 1: Source-first analysis

**Purpose:**
- define current behavior, boundaries, and design constraints before proposing decisions

**Steps:**
- [ ] inspect current source-of-truth surfaces
- [ ] identify unresolved contract edges
- [ ] record affected invariants, interfaces, and dependency boundaries

**Verification:**
- [ ] current-state understanding is explicit enough to support concrete design decisions

**Exit Criteria:**
- no core design decision depends on unstated assumptions

### Wave 2: Decision closure

**Purpose:**
- resolve design choices and document why chosen shape is preferred

**Steps:**
- [ ] define major design decisions
- [ ] compare alternatives where non-obvious
- [ ] record impact on interfaces, invariants, and downstream implementation

**Verification:**
- [ ] each major design question has a documented decision or explicit deferral

**Exit Criteria:**
- design is internally coherent and bounded

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare the spec for implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define validation plan
- [ ] confirm invariant preservation strategy
- [ ] identify any open approval questions or follow-up notes

**Verification:**
- [ ] validation plan proves intended behavior and contract preservation

**Exit Criteria:**
- spec is ready for approval or implementation planning

## Design Decisions

This section is the canonical design-choice record.
Keep chosen approach, alternatives, and impact here.
Do not restate invariants or full validation procedure here.

### Decision: <short title>

- context: <why decision exists>
- choice: <selected approach>
- alternatives considered:
  - <alternative>
- impact:
  - <affected interface, boundary, or downstream implication>

## Invariants

This section is the canonical constraint record.
Keep only what must remain true.

- <must remain true>

## Validation Plan

This section is the canonical proof record.
Keep how claims will be verified here.

- proof target: <claim>
  - method: <test, inspection, comparison, or run>
  - evidence: <expected proof>

## Completion Criteria

A specification item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
