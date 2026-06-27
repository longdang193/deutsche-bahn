# Repo Governance

This document defines how a private project repo is organized for humans and agents.

## Repo Roles

- Private repo:
  - full development source of truth
  - internal docs, workflows, specs, plans, and tooling are allowed
- Public repo:
  - curated product-facing mirror
  - receives only intentionally published code and docs

Normal development happens only in the private repo.

## Structure Model

The repo uses four distinct internal layers:

1. `docs/operating_system/`
- human-readable repo rules and workflows
- publication policy
- doc-system and planning rules
- internal tooling pilots
- agent memory under `docs/operating_system/agent_memory/`

2. `.agents/skills/`
- canonical reusable skill/workflow surface
- focused execution workflows

3. `.agents/agents/`
- optional lightweight repo-local playbooks for task-specialized subagent roles
- subordinate to `AGENTS.md`, `docs/operating_system/`, and `.agents/skills/`

4. shipped root instruction docs
- `AGENTS.md`
- `GEMINI.md`
- `CLAUDE.md`
- final consume-only entry artifacts for downstream starter clones

For copyable user-facing prompts that help invoke the lifecycle cleanly, use
`docs/operating_system/prompt_templates/`. That folder is the practical
invocation layer for humans; the surrounding operating-system docs remain the
governing method layer.
It now covers both:

- upstream roadmap/workstream routing prompts
- upstream construction prompts for building the planning structure itself
- downstream spec/plan/execution prompts
- managed-mode update/fix prompts for already-managed repos
- planning-alignment review prompts for roadmap/workstream vs execution drift

The repo uses shipped root instruction docs as final downstream entry surfaces,
while still splitting ownership by role:

- `AGENTS.md` for repo-wide agent instructions
- `.agents/skills/` for canonical reusable skills
- `.agents/agents/` for optional repo-local playbooks
- `docs/operating_system/` for human governance

Execution context-pack governance for long-running session handoff is defined in:
- `docs/operating_system/governance/execution-context-pack-governance.md`

The repo also splits configuration ownership by purpose:

- `repo_config/`
  - repo/system configuration such as publication boundaries and adapter generation mappings
- `configs/`
  - runtime/workflow configuration such as training, monitoring, assets, and smoke profiles
- `docs/features/*/feature.source.yaml` and `docs/stages/*.source.yaml`
  - human-owned feature and stage lifecycle sources, not generic runtime config buckets
- `docs/features/*/*.yaml`, `docs/features/*/lineage.generated.yaml`, and `docs/stages/*.yaml`
  - generated lifecycle outputs assembled from the human-owned sources plus metadata

The architecture-lineage system is now steady-state repo policy:

- edit `docs/features/<feature_id>/feature.source.yaml` for human semantic changes
- edit `docs/stages/<stage_id>.source.yaml` for human stage-boundary changes
- treat generated feature contracts, generated stage contracts,
  `lineage.generated.yaml`, generated history blocks, and current managed
  generated discovery indexes as standard generated outputs
- use `scripts/sync_architecture_docs.py` as the canonical sync/check workflow
- use `scripts/validate_repo_contracts.py` as the canonical repo-wide contract validation workflow
- use the canonical sync/check workflow to catch malformed metadata, missing required `@meta`, and disallowed manual reference bridges before commit/push
- keep shared validator contract policy in `scripts/validator_policy.py`,
  including repo-contract marker strings and adoption-shape marker policy; it
  is internal starter validation policy, not downstream runtime config
- treat lineage completeness enforcement as a standing requirement, not a rollout-only concern
- treat feature-history generation as part of the same sync/check workflow; completed
  plans update the generated history block automatically
- keep feature refs metadata-derived; `manual_refs` is not accepted in
  `feature.source.yaml`, and that prohibition is part of shared internal policy
  rather than a generator-only convention
- treat the managed-mode contract shapes validated by
  `scripts/validate_adoption_shape.py` as migration targets rather than loose
  generated suggestions
- treat canonical style on required managed metadata surfaces as validator-owned
  contract behavior rather than optional polish
- treat canonical ordering the same way for unordered managed metadata lists,
  while leaving chronology and workflow-sequence fields unsorted

The repo also expects a small standard root documentation surface for projects
beneath `docs/`:

- required:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- optional:
  - `docs/dataset.md`
  - `docs/api.md`
  - `docs/observability.md`
  - `docs/testing.md`

These root docs are cross-cutting project docs, not replacements for
`docs/intent/`, `docs/operating_system/`, feature-local docs, stage docs, or
generated discovery. The normal validation and hook path should fail when the
required set is missing.

When those required root docs drift from current repo reality, use the prompt
pack entry at
`docs/operating_system/prompt_templates/required-root-doc-update-prompt.md`
rather than improvising a root-doc rewrite from scratch.

Required root-doc validation is intentionally light but real. That contract is
owned by `scripts/validate_adoption_shape.py`, and the normal repo-contract
gate runs that validator directly. The normal validation path now checks:

- required paths exist
- each required doc has a top-level heading
- each required doc has more than heading-only stub content
- each required doc covers its intended subject at a lightweight semantic level
- obvious placeholder-only text does not pass

In `managed_architecture_metadata` mode, those required root docs also become
validator-enforced metadata-linked docs through the same adoption-shape
validator. They must carry frontmatter with a canonical `doc_id`, a non-empty
`doc_type`, and an `explains` mapping that links the doc back to the relevant
managed feature, stage, config, or component surface. `docs/pipeline.md` in
particular must keep `explains.stages`.

Optional root docs remain optional when absent. When a managed repo creates
`docs/dataset.md`, `docs/api.md`, `docs/observability.md`, or `docs/testing.md`,
that file also becomes a validator-enforced metadata-linked doc with canonical
`doc_id`, non-empty `doc_type`, and doc-appropriate `explains.*` links.

The dedicated required-root-doc update prompt should keep that distinction
explicit: required root docs must be refreshed as contract surfaces, while
optional root docs should only be recommended or updated when the repo shape
actually needs them.

Outside managed mode, required root docs still do not need frontmatter by
default. Frontmatter remains optional for other Markdown docs unless they are
meant to participate in architecture linkage.

For managed required and optional root docs, canonical metadata style is part of
the contract as well:

- concise frontmatter fields such as `doc_id` and `doc_type` must stay
  single-line and trimmed
- unordered `explains.*` lists must not contain duplicate or empty items
- unordered `explains.*` lists must use canonical lexical order when they are
  set-like membership fields
- path-like metadata values must use canonical repo-relative paths

The repo also expects a lean required folder surface:

- `docs/intent/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `repo_config/`
- `scripts/`
- `tests/`

Minimum file expectations for those required folders:

- `docs/intent/`
  - at least one Markdown file
  - `README.md` is the recommended anchor overview
  - `master-workstream-roadmap.md` is the recommended top-down planning bridge
    from intent into durable workstreams and the parallel operating-system
    branch
- `docs/operating_system/`
  - governing repo-method docs such as `repo-governance.md` and `skill-doc-system-lifecycle.md`
- `docs/superpowers/specs/`
  - bounded design artifacts when needed
- `docs/superpowers/plans/`
  - bounded execution artifacts when needed
- `repo_config/`
  - repo/system config, with `adoption-mode.yaml` as the required anchor file
- `scripts/`
  - repo workflow executables such as validation, sync, and setup helpers
- `tests/`
  - executable verification surfaces

Conditional folders remain conditional:

- `docs/features/`
- `docs/stages/`
- `docs/generated/`
- `configs/`
- `aml/components/`
- `docs/architecture_templates/`
- `.agents/skills/`
- `.codex/`
- `setup/`

The normal validation and hook path should fail when the required folder
surface is missing, while conditional folders should be required only when the
project shape or adopted workflow actually uses them.

For `starter_method_only`, the canonical validator path keeps starter scaffolding
requirements separate from managed architecture surfaces.

Mode A keeps `docs/features/`, `docs/stages/`, and `docs/generated/` absent or
prose-only until the repo explicitly adopts managed metadata.

Once a repo adopts `managed_architecture_metadata`, managed surfaces become
strict contract requirements, and role split is expressed through
`repo_role: source_owner | consumer_derived` rather than by changing required
managed surface shape.

Planning classification should stay explicit:

- `docs/intent/` owns project purpose and the top-down roadmap from purpose
  into durable work
- `docs/operating_system/` owns repo method and governance
- `workstream` remains a product-direction execution-facing layer
- `operating_system` remains a first-class planning branch rather than a fake
  workstream

The precise execution ladder is:

`intent -> master workstream roadmap -> registered workstreams -> bounded change thread files -> complete spec set -> spec-authoring map -> detailed specs -> implementation execution map -> implementation plans -> execution passes with thread checkpoint result packs`

Use that model to keep responsibilities separate:

- roadmap = coverage of the major threads needed to reach the end goal
- registered workstreams = durable thread ownership plus progress roll-up
- bounded change thread files = the safe parallel execution unit
- complete spec set = the inventory of required specs before detailed design writing
- spec-authoring maps = orchestration artifacts for detailed-spec authoring
- detailed specs = bounded design artifacts
- implementation execution maps = orchestration artifacts across approved detailed specs
- plans = bounded execution artifacts

Checkpoint policy for this ladder:

- the checkpoint unit is the bounded change thread (not the full workstream and
  not each downstream artifact)
- each execution pass for a bounded change thread should publish a visible
  result pack
- result packs should use
  `docs/operating_system/templates/checkpoint-result-pack.md` as the canonical
  shape
- store thread checkpoint packs under
  `docs/intent/workstreams/checkpoints/<workstream-id>/<thread-slug>/`
- at minimum, active and completed bounded change threads should always have a
  latest checkpoint result pack

Lineage should stay minimal:

- workstreams carry their own identity and status
- thread files carry their own identity and status, with workstream parent
  derived from path
- change-layer specs should point to `parent_thread`
- change-layer plans should point to `parent_thread` and `parent_spec`
- downstream artifacts should not restate full ancestry when it can be derived
- thread files should not store `linked_spec` or `linked_plan`; use
  `docs/generated/planning_lineage.yaml` for the assembled linkage view instead

When humans want help deciding which bounded change threads can safely run in
parallel, use the prompt-pack entry at
`docs/operating_system/prompt_templates/parallel-bounded-change-planning-prompt.md`.

The master roadmap may include a lightweight completion checklist for strategic
coverage review, but it should not become a progress tracker for downstream
execution.

Downstream artifacts should also make that alignment explicit:

- if the work follows a roadmap thread, name it rather than assuming readers
  will infer it later
- use a real workstream ID from `docs/intent/workstreams/` when
  `parent_workstream` is not `none`
- if the work belongs to the operating-system branch, use
  `parent_workstream: none` intentionally and explain why
- specs and plans under `docs/superpowers/` now validator-check
  `parent_workstream` presence/canonical shape, and intent/operating-system
  artifacts must use `parent_workstream: none`
- parallel work should be organized around bounded change threads with clear
  ownership rather than around vague broad workstreams

When a task touches a feature folder, agents should read minimally rather than
loading every file by default:

- start with `feature.source.yaml`
- open the generated `<feature_id>.yaml` only when the assembled current-state contract is needed
- open `lineage.generated.yaml` for ownership, evidence, drift, or traceability work
- open `history.md` only when narrative context or chronology is needed

`history.md` manual edits are required only when a change needs explanation that
generated plan metadata cannot provide on its own, such as operator meaning,
rollout nuance, or cloud-proof interpretation. Do not hand-edit the generated
history block.

## Ownership Rules

### `docs/operating_system/`

Owns:

- repo operating rules
- workflow governance
- publication workflow
- tool adoption policy
- operational agent memory

Does not own:

- product behavior
- runtime code contracts
- task playbooks

`docs/operating_system/agent_memory/` stores compact operational memory for agents. It does not replace feature docs, specs, plans, or generated rules.

### `.agents/skills/`

Owns:

- reusable execution workflows
- canonical reusable skill discovery surface

Does not own:

- publication policy
- repo-wide governance
- playbook-specific local overrides

Formal shape is governed by `docs/operating_system/governance/skills-governance.md`.

### `.agents/agents/`

Owns:

- optional lightweight repo-local playbooks for task-specialized subagent roles

Does not own:

- repo-wide governance
- canonical instructions
- reusable workflow skills

Rules:

- this layer is optional, not required
- if adopted, `.agents/agents/` is the only repo-local playbook surface
- do not introduce both `agents/` and `.agents/agents/`
- playbooks must stay smaller and lighter than skills
- playbooks must remain subordinate to `AGENTS.md`, `docs/operating_system/`, and `.agents/skills/`
- this repo does not need repo-local playbooks until a real repeated specialization gap is proven

### `.codex/rules/`

Owns:

- generated Codex rules outputs
- adapter-rendered rule files consumed by Codex tooling

Does not own:

- canonical skill definitions
- agent memory
- repo governance

`.codex/rules/` is a generated surface created by source-owned tooling. It does
not replace `.agents/skills/` as the canonical skill surface, and consume-only
starter kits must not ship the surrounding `.codex/` root.

### `repo_config/`

Owns:

- repo/system configuration
- publication boundary configuration
- adapter generation mappings
- starter-kit assembly manifest and generated-kit contract inputs

Does not own:

- runtime workflow defaults
- feature or stage contracts
- generated outputs

### `configs/`

Owns:

- runtime and workflow configuration
- smoke profiles
- training, monitoring, release, and asset settings used by repo workflows

Does not own:

- repo governance
- publication boundaries
- generated outputs
- feature or stage lifecycle contracts

## Private / Public Boundary

The following are private-only by default:

- `docs/operating_system/`
- source-only generation machinery and private build inputs
- `.codex/`
- root and nested `AGENTS.md`
- `.agents/`
- `.cursor/`
- `docs/superpowers/`
- `logs/`
- `sample/`

Feature-local generated lineage is also private by default when it references
`docs/superpowers/`, `docs/operating_system/`, agent metadata, or other internal
development paths. Public publication can include generated feature contracts or
aggregate discovery only when those files stand alone without private-only
dependencies.

The public repo must not depend on these files to understand or use the product.

Mode A templates under `docs/project_templates/mode-a/` are public-safe starting
points for new project docs and config. A downstream project may copy and fill
them, but the starter's private operating-system docs, specs, plans,
source-only generation machinery, agent memory, and generated instruction
surfaces still require an explicit curated publication decision before entering
a public mirror.

## Starter-Kit Boundary

`project-OS-starter-kit` is a generated clone-ready starter derived from
`project-OS-starter`. It is not an independently edited source repo.

Hard ownership rules:

- `project-OS-starter` is sole development source of truth
- adapter regeneration happens only in `project-OS-starter`
- kit publication happens only from `project-OS-starter`
- direct edits to generated `project-OS-starter-kit` outputs are not allowed
- downstream kit repos consume shipped `AGENTS.md`, `GEMINI.md`, and
  `CLAUDE.md` as final artifacts and must not keep adapter sync/regeneration
  machinery

Source-owned starter-kit assembly inputs live under `repo_config/`:

- `starter-kit-manifest.json` defines shipped paths and forbidden paths
- `starter-kit-closure.json` records kept skill/workflow closure and
  source-only conditional references that must not leak into the consume-only
  kit

Required starter-kit surfaces currently include:

- root agent entry docs: `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`
- `.agents/skills/` and `.agents/workflows/` that remain valid downstream
- `docs/operating_system/` governance, lifecycle, procedures, templates,
  prompt templates, and adoption docs needed by shipped skills/workflows
- `docs/superpowers/` planning/spec execution surfaces needed for normal
  starter use
- `repo_config/planning_artifact_schema.yaml`
- other `repo_config/` inputs explicitly required by shipped starter workflow,
  including the starter-kit manifest itself when maintainers rebuild the kit
- validation scripts, repo-contract hooks, and tests needed to keep shipped
  starter instructions truthful

Forbidden starter-kit surfaces include:

- `.codex/`
- `adapters/`
- source-only generation machinery and private build inputs
- `generated_agents/`
- `repo_config/agent-adapter-mappings.json`
- `repo_config/publication-config.json`
- adapter sync/verify scripts and downstream adapter-regeneration machinery
- runtime-bundle deploy/validate/test surfaces that exist only for source-repo
  runtime publication
- factory-only docs, configs, and tests whose instructions would be false in a
  consume-only cloned starter

When a skill, workflow, prompt, or doc is shipped in the starter kit, every
script, template, prompt, governance doc, and validator path it directly names
must also ship unless that instruction is first rewritten at the source layer.
The kit must be assembled from this closure, not from broad folder copying by
default.

## GitNexus Freshness Policy

GitNexus is an optional private-only analysis layer for repo navigation,
cross-file tracing, and impact analysis. It is useful, but it is never stronger
than the current source code, tests, and active docs.

Before higher-trust GitNexus use, check freshness with:

```powershell
.\scripts\get_gitnexus_freshness.ps1
```

Working rules:

- if GitNexus is `fresh`, it may be used normally for exploration and as a
  higher-trust aid for impact analysis
- if GitNexus is `stale`, exploration may still use it as advisory lookup only
- if GitNexus is `stale`, debugging may still use it as advisory only and any
  conclusions should be labeled accordingly
- if GitNexus is `stale`, higher-risk refactor or impact work should refresh
  first when possible
- if refresh fails, continue source-first with code, tests, and active docs
  rather than blocking safe work
- if GitNexus output conflicts with current source or tests, trust the source
  and tests

This repo treats stale GitNexus as an advisory tool state, not as a reason to
stop normal source-first engineering work.

When a human wants help refreshing or repairing GitNexus itself, use the prompt
pack entry at
`docs/operating_system/prompt_templates/gitnexus-refresh-prompt.md`.

## Current Phase

Current starter-kit governance keeps `.agents/skills/` as the canonical skill
source.

Optional repo-local playbooks, when used, live under `.agents/agents/` and stay
subordinate to the skill layer rather than replacing it.

Source-only generation machinery may evolve over time, but consume-only starter
kit output must keep shipping final root instruction docs instead of generation
inputs.

## Source-Only Generation Workflow

When source-owned generation machinery changes, update it only in
`project-OS-starter` and then rebuild the generated starter kit. Do not add
those source-only generation commands or paths to consume-only starter
instructions.

## Hook Workflow

The repo hook workflow is part of normal enforcement.

Installed local hooks should call the repo-contract validator in its hook-facing
subset mode:

```powershell
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
```

Use `scripts/sync_architecture_docs.py` separately when you need to regenerate
feature, stage, or discovery outputs before rerunning the validator.

The `--fast` flag is not a no-op quick check. It still runs the architecture
sync check path and skips only the extra validator-specific pytest pass.

CI is expected to run adapter verification, baseline checks, and publication-boundary validation on push and pull request events so drift and broken changes are caught before merge.

When hooks expose repeated or important failures:

- summarize the reusable lesson in `docs/operating_system/agent_memory/`
- then promote important recurring failures into stronger guardrails when appropriate:
  - a repo rule
  - a script check
  - a test
  - or an explicit follow-up plan

