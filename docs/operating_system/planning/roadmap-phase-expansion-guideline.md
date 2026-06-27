# Roadmap Phase Expansion Guideline

This guideline defines only how to construct roadmap documentation when adding
Phase 2 and Phase 3. It does not define or pre-commit actual Phase 2/3
execution work.

## Canonical File Policy

Use one canonical roadmap file only:

- `docs/intent/master-workstream-roadmap.md`

Do not create separate phase-specific master roadmap files such as:

- `master-workstream-roadmap-phase2.md`
- `master-workstream-roadmap-phase3.md`

## How To Add Phase 2 And Phase 3

When the roadmap expands:

1. append new sections inside the existing master roadmap
2. keep prior phase sections in place for continuity
3. add only high-level phase roadmap items, not detailed implementation content

Suggested structure in the same file:

- `## Phase 1`
- `## Phase 2`
- `## Phase 3`
- within each phase, keep a self-contained block:
  - `### Goal`
  - `### Key Deliverables`

Do not mix deliverables across phases. Each deliverable must belong to exactly
one phase block.

## What Belongs In The Master Roadmap

Include:

- phase-level goals
- phase-level key deliverables
- high-level workstream intent per phase
- cross-phase dependencies at summary level

Do not include:

- detailed specs
- implementation plans
- execution-task breakdown

Those belong in downstream artifacts.

## Traceability Construction Rule

After phase sections are appended in the master roadmap, route details through:

`master roadmap -> registered workstreams -> bounded change threads -> complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> implementation plans`

This preserves one roadmap source of truth while allowing phased downstream
detail growth.

## Scope Control For Phase Expansion

When adding Phase 2/3 roadmap items:

- each phase should include its own Goal and Key Deliverables
- do not reuse Phase 1 Goal/Key Deliverables as shared placeholders for later
  phases
- each item should map to a registered workstream, not directly to tasks
- avoid adding execution details directly to roadmap phase sections

Canonical lifecycle/closure enforcement remains in:

- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
