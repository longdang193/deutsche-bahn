# Task Start Routing Guide

Use this guide to choose the correct starting point before writing specs, plans,
or code.

## Canonical Template Ladder

Use these source templates when creating or revising the corresponding planning artifact:

- master roadmap -> `docs/operating_system/templates/master-workstream-roadmap-template.md`
- registered workstream list -> `docs/operating_system/templates/registered-workstream-list-template.md`
- bounded change thread -> `docs/operating_system/templates/bounded-change-thread-template.md`
- complete specification set -> `docs/operating_system/templates/complete-specification-set-template.md`
- spec-authoring map -> `docs/operating_system/templates/spec-authoring-map-template.md`
- detailed spec -> `docs/operating_system/templates/detailed-specification-template.md`
- implementation execution map -> `docs/operating_system/templates/implementation-execution-map-template.md`
- implementation plan -> `docs/operating_system/templates/implementation-plan-template.md`

## Canonical Section Semantics

Keep top-level section names aligned with the standardized templates.
Within those templates, keep subsection ownership distinct:

- roadmap -> `Phase` blocks own sequencing; `Workstream Index` owns registry data
- registered workstream list -> waves own reconciliation flow; `Registered Workstreams` owns canonical rows
- bounded change thread -> waves own progression; `Scope` owns boundaries; `Dependencies` owns prerequisites and handoff facts
- complete specification set -> waves own sequencing; `Spec Inventory` owns spec rows; `Coverage Check` owns thread coverage
- spec-authoring map -> waves own ordering and merge rationale; `Parallel Lanes` owns lane membership
- detailed spec -> waves own design progression; `Design Decisions` owns choices; `Invariants` owns constraints; `Validation Plan` owns proof
- implementation execution map -> waves own execution order; `Dependencies And Risks` owns stable cross-lane dependency and risk facts
- implementation plan -> `Task` blocks own executable slices; top-level `Verification` owns final artifact proof

Prefer one source of truth per fact. Do not restate the same outcome, inventory, or proof detail in multiple sections.

## Decision Order

Start at the lowest valid layer and move upward only when required evidence is
missing:

`implementation plan -> implementation execution map -> detailed spec -> spec-authoring map -> complete specification set -> bounded change thread -> registered workstream -> master roadmap`

## Safe To Start From Implementation Plan When

- an approved implementation plan already exists and is still valid
- execution-ready scope, dependencies, and verification are already defined
- no upstream design or orchestration artifact needs revision

## Safe To Start From Implementation Execution Map When

- multiple implementation plans or execution lanes need coordination
- downstream plans exist or should exist, but lane order is still unclear
- shared-surface dependency sequencing must be made explicit before plan execution

## Safe To Start From Detailed Spec When

- the detailed spec exists and is in scope
- lineage is valid for the task context
- dependencies are clear and bounded
- the task is implementation-level, not reprioritization

## Start From Spec-Authoring Map When

- multiple detailed specs must be authored in a controlled sequence
- drafting order, parallel lanes, or dependency staging is still unclear
- design work is approved at thread/workstream level but not yet decomposed into spec lanes

## Start From Complete Specification Set When

- thread coverage is incomplete across the required specs
- you need to confirm the full approved spec set before downstream design or execution
- the main question is specification completeness, not task execution

## Start From Master Roadmap When

- priorities, phases, or major outcomes may change
- no existing workstream clearly owns the request
- cross-workstream sequencing or ownership is unclear

## Start From Registered Workstream When

- the work is durable and spans multiple bounded threads
- roadmap intent exists but workstream-level ownership is missing or weak

## Start From Bounded Change Thread When

- workstream is known but next executable slice is unclear
- a safe parallelization boundary is needed before spec/plan execution

## Required Evidence Check Before Choosing Start Point

1. roadmap context exists
2. workstream fit exists
3. bounded thread exists or should be created
4. spec-set or authoring-map context exists when multiple specs are involved
5. actionable detailed spec exists when implementation-level start is chosen
6. implementation execution map exists when multi-plan coordination is required
7. implementation plan exists when direct execution is requested
8. dependency/blocker/shared-surface risks are known
9. status/evidence are coherent with current validator rules

## Ambiguity Handling

If ambiguous:

1. pause implementation
2. choose safer higher-level planning start (usually thread/workstream/spec-set)
3. record assumptions
4. request confirmation only for non-obvious tradeoffs

Canonical lifecycle enforcement remains in:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
