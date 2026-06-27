---
template_id: implementation-plan
document_type: implementation_plan
target_globs:
- docs/superpowers/plans/*.md
required_sections:
- Goal
- Key Deliverables
- Task/Wave Breakdown
- Verification
- Completion Criteria
required_frontmatter:
  artifact_type: plan
distribution_tier: starter_kit
---

# Implementation Plan Template

## Goal

<what this plan must deliver>

## Key Deliverables

Use this section for final implementation outcomes only.
Do not restate task-by-task execution details or local verification steps here.

### <deliverable 1>

Describe one concrete implementation outcome this plan must deliver, including changed surfaces, expected behavior, and verification intent.

### <deliverable 2>

Describe another concrete implementation result this plan must deliver, such as test coverage, documentation alignment, or downstream handoff readiness.

## Task/Wave Breakdown

Use `Task` for directly executable implementation slices.
Use `Wave` only when plan truly needs orchestration across multiple related tasks.

Within each task:
- `Purpose` owns bounded outcome
- `Files` owns touched-surface inventory
- `Preconditions` owns prerequisites
- `Steps` owns execution sequence
- `Verification` owns task-local proof
- `Exit Criteria` owns task completion gate

Do not duplicate final artifact verification commands here unless a command is truly both task-local and final.

### Task 1: <short task title>

**Purpose:**
- <bounded outcome this task delivers>

**Files:**
- Inspect: `<path>`
- Modify: `<path>`
- Verify: `<path>`

**Preconditions:**
- <upstream dependency, source-first fact, or prior task result>

**Steps:**
- [ ] Step 1: <first bounded action>
- [ ] Step 2: <second bounded action>
- [ ] Step 3: <verification-aligned follow-up>

**Verification:**
- [ ] <command, assertion, or inspection target>

**Exit Criteria:**
- <what makes this task done>

### Task 2: <short task title>

**Purpose:**
- <bounded outcome this task delivers>

**Files:**
- Inspect: `<path>`
- Modify: `<path>`
- Verify: `<path>`

**Preconditions:**
- Task 1 complete
- <any additional dependency>

**Steps:**
- [ ] Step 1: <first bounded action>
- [ ] Step 2: <second bounded action>
- [ ] Step 3: <verification-aligned follow-up>

**Verification:**
- [ ] <command, assertion, or inspection target>

**Exit Criteria:**
- <what makes this task done>

## Verification

Use this section for final artifact-level verification only.
Do not copy every task-local proof here.

- <final command>

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
