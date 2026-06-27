# Planning Dispatch

This document defines the minimum planning gate for non-trivial changes.

Use it after starting from the owning source layer so the planning flow stays:

`intent -> workstream or operating_system -> change -> spec/plan`

More precisely, execution should pass through:

`intent -> master workstream roadmap -> registered workstreams -> bounded change thread files -> complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> plans -> execution passes with thread checkpoint result packs`

Checkpoint rule:

- treat each bounded change thread as the visible checkpoint unit
- for each meaningful execution pass on that thread, emit a standard result
  pack with visible outputs
- use `docs/operating_system/templates/checkpoint-result-pack.md` for that pack
  shape

## Purpose

Before writing a spec or plan, identify:

- which upstream source should be read first
- whether the work belongs to a product workstream or the operating-system branch
- which planning layer owns the request
- what kind of change this is
- which feature or operating-system area owns it
- whether stages are affected
- which docs must move with it

When a task touches a feature folder, read the minimum truthful set instead of
loading every file by default:

- `feature.source.yaml` first
- the generated `<feature_id>.yaml` only when the assembled contract view is needed
- `lineage.generated.yaml` only for ownership, evidence, drift, or traceability work
- `history.md` only for narrative context

For managed-mode migration or drift work, still name the generated contract and
discovery surfaces in triage when they are part of the validator-enforced
target, even though they are not the upstream source of truth.
For already-managed update/fix work, the prompt pack also includes a dedicated
managed-update prompt so users do not have to improvise through migration or
drift wording first.

Use the smallest truthful reading set for any affected feature folder:

- `feature.source.yaml` first
- generated `<feature_id>.yaml` only if the assembled current contract is needed
- `lineage.generated.yaml` only for ownership/evidence/drift work
- `history.md` only for narrative context
- do not load an entire feature folder by default

## Lifecycle Summary

Use this repo-level planning lifecycle:

1. start from the owning source:
   - `docs/intent/` for project what-and-why
   - `docs/operating_system/` for repo method and governance
   - feature or stage source only when the work is feature- or stage-owned
2. if starting from intent, check `docs/intent/master-workstream-roadmap.md`
3. decide whether the next branch is:
   - a product workstream
   - the `operating_system` branch
4. define or select the bounded change thread that should advance next
5. when helpful, make that slice explicit under
   `docs/intent/workstreams/threads/<workstream-id>/`
6. classify that bounded slice as a `change`
7. produce triage
8. route to a detailed spec, a spec-authoring map, an implementation execution map, or an implementation plan
9. execute only after the bounded artifact is approved or explicitly requested

`operating_system` remains a first-class branch in this model. It is not a
product workstream.

When the work is product-direction work, name the roadmap thread it follows.
When the work is true operating-system work, make it explicit why
`parent_workstream: none` is the right choice instead of leaving that field as
silent filler.

For a copyable user-facing entrypoint into this lifecycle, see
`docs/operating_system/prompt_templates/`.
That prompt pack now includes upstream prompts for:

- building the master roadmap from intent
- building the complete registered workstream set from the roadmap
- building bounded change threads under a workstream
- turning a thread set into a complete spec set
- turning a complete spec set into a spec-authoring map
- turning approved detailed specs into an implementation execution map
- translating roadmap threads into the right workstream or `operating_system`
  branch
- checking whether a proposed change really fits the named workstream
- identifying possible roadmap gaps before writing downstream specs or plans
- handling already-managed metadata update/fix work separately from migration
- reviewing divergence between roadmap/workstream intent and execution so far
- planning safe parallel lanes across bounded change threads

## Four Planning Layers

Use this repo-level layer model before deciding where a request belongs.

- `intent`
  - owns the project what and why
  - governs by purpose
  - stable source docs live under `docs/intent/`
- `operating_system`
  - owns how the repo builds, governs, and routes work
  - governs by method
  - stable source docs live under `docs/operating_system/`
- `workstream`
  - owns a major body of work derived from project intent
  - usually spans one meaningful capability theme, lifecycle theme, or
    cross-cutting improvement track
  - execution artifacts live under `docs/superpowers/`
- `change`
  - owns one bounded execution slice such as a patch, migration, refactor,
    remediation, release, runbook, or hotfix
  - execution artifacts live under `docs/superpowers/`

Intent and operating system are stable governing layers. Workstream and change
are execution-facing planning layers.

## First Routing Gate

Before filling in the rest of triage, ask:

1. is this changing project intent or project purpose?
2. is this changing repo method or operating-system behavior?
3. is this defining or reshaping a major workstream?
4. is this only a bounded change within an existing context?

Use the answer to choose the owning source layer first:

- intent work starts from `docs/intent/`
- operating-system work starts from `docs/operating_system/`
- workstream and change work still use feature/stage/source-of-truth checks and
  produce specs/plans under `docs/superpowers/`

If the work starts from intent, use
`docs/intent/master-workstream-roadmap.md` to decide whether the next branch is
a product workstream or the `operating_system` branch.
If the user needs help making that choice, route them to the roadmap-aware
prompt ladder under `docs/operating_system/prompt_templates/` before pushing
straight into spec or plan prompts.
Use the roadmap-level completion checklist there when the main question is
whether the current roadmap/workstream set is complete enough rather than what
the next bounded change should be.

Record the outcome downstream:

- product-direction specs and plans should name the bounded change thread they follow
- when naming a real workstream, use a valid ID from `docs/intent/workstreams/`
- when naming a real product thread, use a valid thread id from `docs/intent/workstreams/threads/`
- operating-system specs and plans should say why `parent_workstream: none` is
  intentional
- when humans need the assembled thread/spec/plan view, use
  `docs/generated/planning_lineage.yaml` rather than adding derived links back
  into thread files

Keep these distinctions explicit:

- a workstream is not the same thing as a spec
- a workstream is not the same thing as a bounded change thread
- a complete spec set is not the same thing as a detailed spec
- a spec-authoring map is not the same thing as an implementation execution map
- a change is not the same thing as a plan
- detailed specs describe design within a layer
- spec-authoring maps describe orchestration across detailed-spec authoring work
- implementation execution maps describe orchestration across a set of approved detailed specs
- plans describe implementation within a layer
- canonical ownership should stay upstream; downstream layers should derive
  linkage rather than re-entering the same semantic fact

For the full coverage/progress model, see
`docs/intent/workstream-coverage-and-progress-guide.md`.

## Triage Block

Use this block before specs or implementation plans:

```text
Layer: intent | operating_system | workstream | change
Feature type: ADD | MODIFY | REPLACE
Summary: <1 sentence>
Reasoning: <why this classification>
Invariants:
  - <must hold true>
Dependencies:
  - <if known>
Affected stages:
  - <stage_id> | none
Affected features:
  - <feature_id> | none
Primary lens: stage | feature | mixed | cross-cutting
Affected docs:
  feature_source: `docs/features/<feature_id>/feature.source.yaml` | none
  feature_yaml: `docs/features/<feature_id>/<feature_id>.yaml` | none
  feature_lineage: `docs/features/<feature_id>/lineage.generated.yaml` | none
  feature_history: `docs/features/<feature_id>/history.md` | none
  stage_source: `docs/stages/<stage_id>.source.yaml` | none
  stage_contract: `docs/stages/<stage_id>.yaml` | none
  feature_docs:
    - `docs/features/<feature_id>/<doc>.md`
  cross_cutting_docs:
    - `docs/<doc>.md`
    - `docs/operating_system/<doc>.md`
  readme: `README.md` | none
  generated:
    - `docs/generated/<file>` | none
Generated refresh required: yes | no
Capability IDs:
  - <capability_id> | none
Invariant IDs:
  - <invariant_id> | none
Spec needed: yes | no
Plan needed: yes | no
```

`<feature_id>` is placeholder notation in planning docs. The real generated
contract path uses the concrete feature id as the filename, for example
`docs/features/model-training-pipeline/model-training-pipeline.yaml`.

## Dispatch Rules

- unclear design -> write a spec first
- clear design, non-trivial execution -> write a plan
- explicit implementation-plan request for a bounded, design-clear change -> go
  straight to the plan after triage
- approved plan -> implement
- cross-cutting repo workflow changes may use `Affected features: none`
- layer classification happens before spec-vs-plan routing
- do not force an unnecessary spec hop when the user explicitly asked for a
  bounded implementation plan and the design is already clear enough to execute

## Operating-System Changes

When the change is about repo structure, publication workflow, agent instructions, or tooling policy:

- primary lens is usually `cross-cutting`
- affected features may be `none`
- the owning docs live under `docs/operating_system/`
- if the change is also stage-aware, still name both `stage_source` and
  `stage_contract` targets rather than only the generated stage path

Generated discovery note:

- use `docs/generated/architecture_dag.yaml` and
  `docs/generated/capability_lineage.yaml` when a change affects generated
  architecture metadata indexes
- in managed mode, treat those generated discovery files as validator-enforced
  outputs rather than optional side summaries
- use `docs/features/<feature_id>/lineage.generated.yaml` as the detailed
  generated evidence surface for opted-in feature changes
- record `generated: none` and `Generated refresh required: no` for unrelated
  work instead of inventing placeholder files

## Intent Changes

When the change is about the project's what, why, audience, desired outcomes,
constraints, or non-goals:

- layer is usually `intent`
- affected features may be `none`
- the owning docs live under `docs/intent/`
- use `docs/intent/master-workstream-roadmap.md` when the next question is how
  to translate intent into durable work
- do not force project-purpose changes into `docs/operating_system/` just
  because they are cross-cutting
- keep intent docs stable and source-like rather than turning them into dated
  execution logs

## Workstream vs Operating-System Routing

After starting from intent, ask:

1. is this a durable product-direction thread derived from project outcomes?
2. or is this about how the repo plans, validates, publishes, documents, or
   instructs agents?

Route to a **workstream** when the work is a durable product-delivery thread.

Route to **operating_system** when the work is repo-method work such as:

- planning and routing behavior
- validation and sync workflow
- publication boundaries
- instruction surfaces and skills
- repo governance and documentation method

Do not force operating-system work into fake product workstreams.

## Metadata-Aware Planning

When a change affects an opted-in feature, record the stable IDs that will move
with the change:

- feature ID in `affected.features`
- feature-qualified capability IDs in specs/plans and code `@capability` markers
- invariant IDs in specs/plans when an invariant is changed or tested
- test proof IDs with `@proves <feature_id>.<capability_slug>`
- generated refresh requirements for feature YAML, feature-local lineage, and
  DAG outputs
- validator-enforced managed surfaces such as generated feature contracts,
  generated stage contracts, generated history boundaries, and current
  generated discovery indexes when migration-target drift is in scope
- human history updates only when narrative context changes; do not add
  generated timeline blocks to `history.md`

When metadata semantics are being cleaned up or extended:

- prefer one human-owned source for ownership or role semantics
- prefer derived refs and generated views for downstream traceability
- avoid adding a second manual field that answers the same semantic question as
  an upstream field

Use `tools\docs\generate_architecture_metadata.py --validate-only` before
implementation if metadata shape is uncertain, and `--check` before completion
when metadata source files changed.

Prefer the canonical repo workflow when doing the full architecture sync/check pass:

```powershell
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py --check
```

If a narrower metadata command is used for a bounded purpose, document that it
is subordinate to the canonical sync/check workflow rather than a separate
default path.

If a narrower metadata command is used for a bounded reason, explain that it is
subordinate to the canonical architecture sync/check workflow rather than a
separate default path.

For specs and plans under `docs/superpowers/`, use a small layer-aware metadata
set:

```yaml
layer: intent | operating_system | workstream | change
artifact_type: spec | plan
status: proposed | active | completed | superseded
parent_workstream: <id> | none
targets:
  - <path>
related_features:
  - <feature_id>
related_stages:
  - <stage_id>
```

Rules:

- `layer`, `artifact_type`, and `status` are required
- `parent_workstream`, `related_features`, and `related_stages` are optional
- `targets` is required when the artifact is cross-cutting or otherwise
  ambiguous in scope
- `targets` may be omitted only when the scope is already obvious and narrowly
  local

## Hygiene And Drift Changes

When the change is a bounded cleanup or drift-audit pass rather than a managed
product feature:

- `Affected features: none` is valid
- `Primary lens` may remain `cross-cutting`
- still name the exact docs and rules that own the cleanup
- do not force a fake feature contract just to satisfy the planning format

## Explicit Plan Requests

When the user explicitly asks for an implementation plan:

- produce triage first
- if the requested change is already bounded and design-clear, route directly
  to the plan
- use a spec first only when design is still meaningfully unsettled,
  cross-cutting in an unresolved way, or missing key decisions
- treat the owning source docs as the first sources to read, not the first
  artifacts to create
