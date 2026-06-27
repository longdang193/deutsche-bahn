---
template_id: implementation-execution-map
document_type: implementation_execution_map
target_globs:
- docs/superpowers/execution_maps/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Dependencies And Risks
- Completion Criteria
required_frontmatter:
  artifact_type: execution_map
  map_type: implementation_execution
distribution_tier: starter_kit
---

# Implementation Execution Map Template

## Goal

<what this execution map must orchestrate>

## Key Deliverables

Use this section for orchestration outcomes only.
Do not restate lane ordering or dependency/risk inventories here.

### <deliverable 1>

Describe one concrete execution-map outcome this document must deliver, such as lane coordination, dependency sequencing, or rollout readiness across downstream plans.

### <deliverable 2>

Describe another concrete execution-map result this document must deliver, such as reduced cross-lane uncertainty, explicit handoffs, or readiness for parallel execution.

## Task/Wave Breakdown

Use this section for implementation wave order and lane handoffs.
Do not repeat the stable dependency/risk inventory here unless a wave changes it.

### Wave 1: Foundational implementation lanes

**Purpose:**
- start implementation lanes that unblock all downstream work

**Starts First:**
- <plan or lane>

**Unlocks:**
- <downstream lane or plan>

**Shared Surfaces:**
- <path>
- <path>

**Verification:**
- [ ] first-wave lanes are truly foundational and unblock later execution

**Exit Criteria:**
- downstream lanes can start with reduced dependency risk

### Wave 2: Parallel or follow-on implementation lanes

**Purpose:**
- execute dependent or parallel implementation lanes in controlled order

**Steps:**
- [ ] confirm lane dependencies
- [ ] confirm shared-surface coordination
- [ ] identify handoff points between plans
- [ ] identify rollback or containment notes for risky surfaces

**Verification:**
- [ ] lane order and shared-surface risks are explicit

**Exit Criteria:**
- downstream implementation can proceed without hidden sequencing ambiguity

### Wave 3: Reconciliation and rollout readiness

**Purpose:**
- close cross-lane work and prepare final verification or rollout

**Steps:**
- [ ] reconcile cross-lane outputs
- [ ] confirm all critical dependencies are closed
- [ ] confirm downstream verification readiness

**Verification:**
- [ ] execution map supports final implementation closeout

**Exit Criteria:**
- implementation work is ready for final verification and completion

## Dependencies And Risks

This section is the canonical cross-lane dependency and risk record.
Keep stable dependency and shared-surface risk facts here.

- execution lanes:
  - <lane> - <owned plans or surfaces>
- dependencies:
  - <dependency>
- shared-surface risks:
  - <risk>
- merge or rollout checkpoints:
  - <checkpoint>

## Completion Criteria

An implementation-execution-map item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
