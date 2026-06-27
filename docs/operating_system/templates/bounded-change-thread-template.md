---
template_id: bounded-change-thread
document_type: bounded_change_thread
target_globs:
- docs/intent/workstreams/threads/*/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Scope
- Dependencies
- Completion Criteria
distribution_tier: starter_kit
---

# Bounded Change Thread Template

## Goal

<what this bounded thread must achieve>

## Key Deliverables

Use this section for thread-level outcomes only.
Do not repeat in-scope/out-of-scope boundaries or dependency lists here.

### <deliverable 1>

Describe one concrete bounded-thread outcome this document must deliver, including the intended change, the owned slice, and the observable end state.

### <deliverable 2>

Describe another concrete bounded-thread outcome, such as a completed dependency, risk reduction, or closeout gate for the thread.

## Task/Wave Breakdown

Use this section for progression from boundary confirmation into handoff readiness.
Do not duplicate canonical scope or dependency records here unless a step explicitly changes them.

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [ ] confirm in-scope surfaces
- [ ] confirm out-of-scope surfaces
- [ ] identify required upstream dependencies
- [ ] identify explicit downstream handoff target

**Verification:**
- [ ] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [ ] record dependency closures or remaining blockers
- [ ] identify next required artifact or execution lane
- [ ] capture follow-up work that is intentionally deferred

**Verification:**
- [ ] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to spec, execution map, or implementation plan work

## Scope

This section is the canonical boundary record.
Keep only scope facts here.

- in scope:
  - <item>
- out of scope:
  - <item>
- deferred:
  - <item> | none

## Dependencies

This section is the canonical dependency record.
Keep prerequisites, blockers, and downstream handoffs here.

- upstream:
  - <dependency> | none
- blockers:
  - <dependency> | none
- downstream handoff:
  - <artifact or lane>

## Completion Criteria

A thread item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
