# Project Adoption Migration Guide

Use this guide when an existing project adopts `project-OS-starter`.

This guide is private-source onboarding material. It explains how to migrate a
private repo into the starter-compatible structure and should not be published
to a curated public mirror unless it has been intentionally rewritten as
product-facing documentation.

This guide is different from the feature routing guide:

- `feature-routing-guide.md` decides whether a candidate is a product feature, product stage, operating-system concern, spec, plan, generated output, or obsolete artifact.
- this guide decides how an existing project moves from legacy docs into the starter-compatible structure.

## Core Rule

Do not partially migrate architecture metadata.

Before changing feature, stage, generated discovery, or source metadata surfaces, choose one adoption mode and record it in `repo_config/adoption-mode.yaml`. The adoption spec or plan should reference that file instead of inventing a second mode source.

## Adoption Mode Source

`repo_config/adoption-mode.yaml` is the machine-checkable source of truth for adoption mode.

Validate it with:

```powershell
python scripts/validate_adoption_shape.py
```

## Adoption Modes

### Mode A: Consumer Starter Mode (alias: starter_method_only)

Use this mode when the project wants repo governance, intent docs, agent rules, adapter sync, publication workflow, and operating-system docs, but does not yet want managed product feature/stage lineage surfaces.

Rules:

- do not create or migrate `docs/features/`
- do not create generated architecture indexes
- do not add feature/capability metadata to code, config, or tests
- keep product architecture docs as ordinary prose
- use operating-system specs/plans for repo-method adoption work
- `scripts/validate_adoption_shape.py` should pass with starter scaffold files only

### Mode B: Source-of-Truth Owner (alias: managed_architecture_metadata)

Use this mode when the project wants feature/stage contracts, generated lineage, generated discovery, and code/config/test traceability.

Rules:

- migrate product features into folders
- create `feature.source.yaml` for each product feature
- generate or normalize `<feature_id>.yaml`
- generate `lineage.generated.yaml` when lineage generation is adopted
- update code/config/test/doc metadata to canonical feature IDs and feature-qualified capability IDs
- refresh generated discovery
- verify no flat authoritative feature contracts remain
- remove or relocate method-layer pseudo-features
- keep shared repo-control surfaces current by diffing them against newer starter versions when the project pulls starter updates
- record starter shared-surface review in `repo_config/adoption-mode.yaml`
- `scripts/validate_adoption_shape.py` should pass after generated discovery is refreshed

### Mode C: Legacy Compatibility Mode (alias: legacy_compatibility)

Use this mode when a project already has flat feature YAML and is not ready for managed architecture metadata.

Rules:

- keep flat `docs/features/*.yaml` temporarily
- do not create generated feature-folder contracts beside them
- do not claim the project has adopted managed architecture metadata
- record the legacy choice in the adoption spec, plan, or project notes
- create a follow-up migration plan before adding deeper traceability
- `scripts/validate_adoption_shape.py` should warn about missing follow-up migration when none is recorded

## Mode A Step-By-Step: Consumer Starter Mode (alias: starter_method_only)

Prompt shortcut: use
`docs/operating_system/prompt_templates/mode-migration-prompt.md` when you want
an agent to assess or plan a mode migration instead of improvising the ask.

Use this runbook when the project wants the starter's repo operating-system method without adopting product feature, stage, capability, generated architecture, or lineage metadata.

1. Start by copying `docs/project_templates/mode-a/` into the project root, then fill the placeholders instead of inventing file shapes by hand. The pack includes required root docs, `docs/intent/` anchors, `repo_config/`, `configs/`, `scripts/README.md`, and `tests/README.md`.
2. Keep the copied `repo_config/adoption-mode.yaml` set to `starter_method_only` with explicit `repo_role`.
3. Treat Mode A as strict starter governance without managed metadata surfaces:
   - validator enforces starter-method repo shape and adoption boundaries
   - managed feature/stage/discovery surfaces are absent by design unless repo explicitly adopts managed metadata mode
   - do not rely on lightweight-warning ladders as migration policy
4. Fill or update the intent layer for the project:
   - `docs/intent/project-charter.md`
   - `docs/intent/constraints-and-non-goals.md`
   - `docs/intent/stakeholders.md`
   - `docs/intent/success-outcomes.md`
5. Adopt the operating-system layer needed by the project:
   - repo governance docs under `docs/operating_system/`
   - agent instruction templates and generated instruction surfaces
   - generated rule surfaces
   - adapter sync and verification workflow
   - publication guidance
   - agent-memory guidance
6. Keep product architecture metadata absent:
   - do not create product feature folders
   - do not create stage contracts
   - do not create generated architecture indexes
   - do not add feature or capability metadata to code, config, or tests
7. Represent starter adoption, adapter work, rule updates, publication setup, and other method-layer changes as operating-system specs or plans with explicit `targets`.
8. If adapter sources, agent instructions, or generated rule surfaces changed, run:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

9. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

10. Commit only after the repo has no accidental product architecture metadata.

Stop and create a Mode B migration plan instead of adding one-off feature files if the project needs product feature lineage, stage ownership, or generated feature contracts.

## Mode B Step-By-Step: Source-of-Truth Owner (alias: managed_architecture_metadata)

Use this runbook when the project wants managed metadata for product features, stages, capabilities, generated contracts, generated discovery, and source traceability.

Do not switch to Mode B just because one feature folder exists. Mode B means project has adopted managed metadata contract across docs, generated outputs, and source metadata.

For a concrete one-feature migration, see [Mode B Example Migration](mode-b-example-migration.md).

For copy-safe source templates, see [Architecture Metadata Templates](../architecture_templates/README.md). Use them only for Mode B migration work, and do not copy generated contracts or generated lineage files as source.

1. Set `repo_config/adoption-mode.yaml` to `managed_architecture_metadata` and set `repo_role` (`source_owner` or `consumer_derived`).
2. Inventory existing product and architecture surfaces:
   - product docs
   - flat `docs/features/*.yaml` files
   - `docs/features/*/` folders
   - stage docs and contracts
   - generated files under `docs/generated/`
   - code metadata
   - config metadata
   - test metadata
   - pipeline, component, workflow, and asset metadata
   - shared repo-control surfaces such as `repo_config/`, `docs/operating_system/`, `.agents/skills/`, adapter templates, generated rules, and validation scripts
3. Classify each candidate as one of:
   - product feature
   - product stage
   - product capability
   - cross-cutting product doc
   - operating-system method material
4. Diff shared repo-control surfaces against the newer starter version before or alongside the Mode B migration. Bring forward newer versions intentionally for files such as:
   - `repo_config/*.json`
   - `repo_config/*.yaml`
   - `docs/operating_system/*.md`
   - `.agents/skills/*`
   - `docs/operating_system/templates/agents/*`
   - generated `AGENTS.md` and provider runtime rules after adapter sync
   - validation and sync scripts when the starter has stronger checks or generators
5. Record the shared-surface sync review in `repo_config/adoption-mode.yaml` using a `starter_sync` block that captures:
   - `starter_baseline_ref`
   - `last_shared_surface_review_at`
   - `reviewed_surface_classes`
   - optional `divergences` with `path`, `class`, `status`, and `rationale`
6. Remove or re-home method-layer pseudo-features. Starter adoption, repo governance, adapter work, generated rule work, publication setup, and agent-memory guidance belong in `docs/operating_system/` or operating-system specs/plans, not `docs/features/`.
7. Create one folder per real product feature:

```text
docs/features/<feature_id>/
```

8. Move human-owned feature meaning into:

```text
docs/features/<feature_id>/feature.source.yaml
```

9. Ensure generated feature outputs use:

```text
docs/features/<feature_id>/<feature_id>.yaml
docs/features/<feature_id>/lineage.generated.yaml
```

10. Normalize capability IDs to feature-qualified stable identifiers, such as `<feature_id>.<capability_slug>`. Do not use prose sentences or unscoped capability slugs as capability IDs.
11. Normalize managed metadata into canonical style before validation:
    - keep concise fields such as `summary`, `statement`, `doc_id`, and `doc_type` as single-line trimmed strings
    - remove leading/trailing whitespace and blank-line padding from concise fields
    - remove duplicate or empty items from unordered metadata lists
    - reorder non-semantic membership lists into canonical lexical order
    - keep repo-relative metadata paths canonical with forward slashes and no surrounding whitespace
    - do not sort chronology or workflow-sequence fields whose order carries meaning
12. Update stage source files so `primary_features` and `supporting_features` describe stage ownership.
13. Update source metadata that feeds lineage so it references canonical feature IDs and feature-qualified capability IDs:
    - code
    - config
    - tests
    - AML components
    - scripts
    - docs
    - pipeline and workflow manifests
14. Re-run starter-controlled generators and sync steps after shared repo-control files change. At minimum, run adapter sync if adapter sources or mappings changed:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

15. Refresh generated architecture surfaces from source using the project generator when one exists. If no generator exists, do not hand-invent generated files; add the generator first or stay in legacy compatibility.
16. Verify no authoritative flat `docs/features/*.yaml` files remain outside feature folders.
17. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

18. Run the relevant test suite for the surfaces changed.
19. Run whitespace validation:

```powershell
git diff --check
```

20. Commit only after managed metadata, shared repo-control files, the `starter_sync` review record, generated files, source metadata, validation, and tests agree.

## Mode C Step-By-Step: Legacy Compatibility Mode (alias: legacy_compatibility)

Use this runbook when project already has legacy flat feature contracts and needs temporary holding pattern before moving to Mode A or Mode B.

Legacy compatibility is temporary. It should make the follow-up migration discoverable instead of letting legacy metadata become an accidental permanent contract.

1. Set `repo_config/adoption-mode.yaml` to `legacy_compatibility`.
2. Record `migration_follow_up.required: true` and point it at the plan or issue that will migrate the project to Mode A or Mode B.
3. Inventory existing flat feature contracts.
4. Classify which flat contracts are real product features and which are method-layer material.
5. Keep legacy flat feature contracts as the temporary current truth.
6. Do not create managed feature folders, generated feature contracts, or generated lineage files until a Mode B migration plan is executed.
7. Re-home obvious method-layer pseudo-features into operating-system docs/specs/plans when safe.
8. Validate the selected mode:

```powershell
python scripts/validate_adoption_shape.py
```

9. Treat validator warnings as migration debt unless the guide documents why they are intentionally allowed in Mode C.
10. Commit only after the legacy state is explicit and the migration follow-up is discoverable.

Stop extending Mode C and move to a Mode B migration plan if the work requires generated lineage or capability-level code tracing.

## Canonical Managed Feature Shape

In managed architecture metadata mode, each product feature should use this shape:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml
  lineage.generated.yaml
  history.md
```

Ownership:

- `feature.source.yaml` is the human-owned semantic source.
- `<feature_id>.yaml` is the generated or normalized assembled current-state contract.
- `lineage.generated.yaml` is canonical generated feature-local lineage evidence and must not be edited manually.
- `history.md` contains feature-local context and human notes, plus generated blocks if the project adopts partial-generated history.

`lineage.generated.yaml` must use the canonical evidence-oriented starter
schema. It is not a generic refs summary or contract-adjacent inventory. If a
repo-local sync script still emits top-level fields such as
`generated_contract`, `naming_policy`, `capability_shape`, `capability_ids`,
`refs`, or `refs_by_type`, that script must be updated before the repo can
truthfully claim managed architecture metadata alignment.

Desired migration target:

- the newer customer-style feature-folder shape where `feature.source.yaml`
  stays minimal and human-owned
- the generated contract carries refs plus generated freshness metadata such as
  `revision`, `latest_change_id`, and `last_updated_at`
- `lineage.generated.yaml` stays evidence-oriented
- `history.md` uses the partial-generated history pattern

Do not treat older folder shapes as equally valid just because they already use
the same filenames. A repo can have the right file names and still carry the
wrong contract in those files.

Likewise, do not treat older generated contracts that omit freshness metadata as
equally valid steady-state outputs once the repo is using the current managed
generator contract. An empty `timeline: []` does not exempt a generated feature
contract from the freshness schema.

Flat files such as `docs/features/data-pipeline.yaml` are legacy compatibility only once managed architecture metadata is adopted.

## Required Migration Sequence For Managed Mode

### 1. Inventory existing surfaces

Before editing, inventory:

```text
docs/features/*.yaml
docs/features/*/
docs/stages/*
docs/generated/*
docs/superpowers/specs/*
docs/superpowers/plans/*
code/config/test metadata markers
workflow/config manifests
cross-cutting docs
shared repo-control files
```

### 2. Classify every candidate

Classify each candidate as one of:

- product feature
- product stage
- operating-system method
- one-time spec/plan
- generated output
- obsolete artifact

Use `docs/operating_system/governance/feature-routing-guide.md` for this classification.

### 3. Remove method-layer pseudo-features

Operating-system work must not remain under `docs/features/`.

Example cleanup:

```text
docs/features/repo-operating-system.yaml -> remove
docs/features/repo-operating-system/* -> move useful prose into docs/operating_system/
```

Durable method guidance belongs in `docs/operating_system/`.

Bounded design or implementation history belongs in specs/plans with `layer: operating_system`.

### 4. Pack product features into folders

Example migration:

```text
docs/features/data-pipeline.yaml
docs/features/data-pipeline/history.md
```

becomes:

```text
docs/features/data-pipeline/feature.source.yaml
docs/features/data-pipeline/data-pipeline.yaml
docs/features/data-pipeline/lineage.generated.yaml
docs/features/data-pipeline/history.md
```

Move human-authored semantic content into `feature.source.yaml`.

Generate or normalize the assembled contract into `<feature_id>.yaml`.

When migrating from an older managed folder shape, do not simply copy all old
source fields into the new source file. The target source should keep only
human-owned semantic fields such as:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `invariants`
- `domains`
- `depends_on`
- `capabilities`
- `stage_participation`
- `lineage_exceptions` when needed

Remove or relocate older contract-adjacent source fields such as:

- `owner`
- `primary_stage`
- `stages`
- `refs`
- `keywords`

If some of that information is still useful, derive it into generated outputs,
move it into prose docs, or map it into the current canonical source fields
instead of preserving the old field names.

### 5. Normalize capability IDs

Capability IDs must be feature-qualified stable identifiers, not prose capability descriptions or unscoped slugs.

Bad legacy shape:

```yaml
capabilities:
  - "Staging: flatten nested GA4 event_params, geo, device, traffic_source, ecommerce fields"
```

Preferred managed shape:

```yaml
capabilities:
  - capability_id: data-pipeline.staging-ga4-events
    statement: Flatten nested GA4 event fields into staging tables.
    state: active
```

If a project schema initially supports only capability strings, label those strings as a legacy bridge and do not treat them as stable IDs.

### 6. Update code, config, test, and doc metadata

Feature migration is incomplete until source references are aligned.

Inspect project-relevant files such as:

```text
*.py
*.sql
*.yml
*.yaml
.github/workflows/*.yml
pipeline.yml
agent_config.yaml
semantic model files
pipeline asset manifests
tests/*
docs/*.md frontmatter
```

Metadata should reference canonical feature IDs and feature-qualified capability IDs, not old prose labels, unscoped capability slugs, or flat YAML paths.

For managed root docs, migrate `docs/setup.md`, `docs/configuration.md`,
`docs/usage.md`, `docs/pipeline.md`, and `docs/architecture.md` to the same
frontmatter-linked shape used by the starter target. They remain cross-cutting
docs, but in managed mode they are no longer free-form prose-only files.
Keep canonical `doc_id` values that match the filename stem, add a non-empty
`doc_type`, and use `explains.*` lists to link the doc back to managed
features, stages, configs, or components. `docs/pipeline.md` must include
`explains.stages`.

Optional root docs remain optional. If the project has `docs/dataset.md`,
`docs/api.md`, `docs/observability.md`, or `docs/testing.md`, migrate those to
the same frontmatter-linked managed shape instead of leaving them as unlinked
prose. Frontmatter must start at the first byte of the Markdown file, except
for a UTF-8 BOM.

### 6b. Diff shared repo-control files forward from the starter

Mode B projects still rely on starter-owned repo method surfaces. When the
starter evolves, do not update only the product metadata and leave repo-control
files stale.

Diff and review shared files such as:

```text
repo_config/*
docs/operating_system/*
.agents/skills/*
docs/operating_system/templates/agents/*
AGENTS.md
 generated provider runtime rules
scripts/validate_*.py
scripts/sync_*.py
```

Bring over newer versions intentionally, then re-apply project-local
customization where needed. The goal is to inherit stronger governance,
validation, sync, and instruction behavior without re-entering starter truth by
hand in multiple downstream places.

Record that review in `repo_config/adoption-mode.yaml` so the project can say
which starter baseline it reviewed and which divergences are intentional.

### 7. Refresh generated discovery

After source migration, run the project's canonical architecture sync/check workflow.

If the project has no generator yet, do not hand-invent generated files. Either add the generator first or keep the project in legacy compatibility mode.

For the current starter-style managed target, `docs/generated/` should converge
to the same shape used by
`customer-churn-prediction-azureml/docs/generated/`:

```text
docs/generated/
  architecture_dag.yaml
  capability_lineage.yaml
```

Treat older generated-discovery families such as:

- `feature_capabilities_index.yaml`
- `feature_dependency_graph.yaml`
- `feature_overview.md`
- `features_by_status.yaml`
- `features_index.yaml`
- `stage_overview.md`
- `stages_index.yaml`

as superseded migration debt once the current managed target is adopted. Do not
keep the older summary-index family beside the newer discovery pair as if both
were canonical steady-state outputs.

For `history.md`, the migration target is the starter partial-generated history
pattern:

- `# History`
- generated block between `<!-- GENERATED HISTORY START -->` and
  `<!-- GENERATED HISTORY END -->`
- `## Human Notes` for preserved manual commentary

Do not keep a version-number changelog as the primary managed feature-history
contract once the starter history model is adopted. Preserve useful historical
notes by moving them under `## Human Notes`.

For `docs/features/<feature_id>/lineage.generated.yaml > timeline`, the current
starter-style managed target is the richer completed-change record shape used by
`customer-churn-prediction-azureml/docs/features/model-training-pipeline/lineage.generated.yaml`.
Regenerated timeline entries should expose fields such as:

- `completed_at`
- `source_plan`
- `change_id`
- `summary`
- `capabilities`
- `verification`
- `outcome`

Do not preserve the older timeline shape:

```yaml
timeline:
  - kind: spec
    path: docs/superpowers/specs/...
  - kind: plan
    path: docs/superpowers/plans/...
```

once the repo is migrating to the current managed target. That shape indicates a
superseded generator contract and should be replaced by regenerated richer
timeline entries.

### 8. Validate the result

Managed mode validation should confirm:

- no authoritative `docs/features/*.yaml` files remain outside feature folders
- no `repo-operating-system` or method-layer pseudo-feature exists
- every feature folder has required files
- feature IDs are kebab-case
- capability IDs are feature-qualified stable IDs
- generated indexes exclude operating-system artifacts
- code/config/test metadata references existing feature IDs and feature-qualified capability IDs
- `docs/features/<feature_id>/lineage.generated.yaml` uses the canonical evidence-oriented schema rather than a legacy summary-style shape
- `docs/features/<feature_id>/<feature_id>.yaml` keeps the canonical generated feature-contract shape, including `revision`, `latest_change_id`, and `last_updated_at`
- `docs/features/<feature_id>/history.md` keeps the generated-history boundary markers plus `## Human Notes`
- `docs/stages/<stage_id>.yaml` uses the canonical flat generated stage contract shape rather than an older nested stage wrapper
- `docs/generated/architecture_dag.yaml` and `docs/generated/capability_lineage.yaml` keep the canonical generated discovery schemas
- generated files were refreshed, not edited manually

## Half-Migration Anti-Pattern

Bad partial migration:

```text
docs/features/data-pipeline.yaml
docs/features/data-pipeline/history.md
docs/generated/features_index.yaml
```

Problems:

- feature truth is split between a flat contract and a folder
- `feature.source.yaml` is missing
- generated discovery may be based on legacy shape
- code/config/test metadata may still be absent or stale

Correct managed shape:

```text
docs/features/data-pipeline/feature.source.yaml
docs/features/data-pipeline/data-pipeline.yaml
docs/features/data-pipeline/lineage.generated.yaml
docs/features/data-pipeline/history.md
docs/generated/architecture_dag.yaml
docs/generated/capability_lineage.yaml
```

Correct legacy compatibility shape:

```text
docs/features/data-pipeline.yaml
```

with a recorded decision that managed architecture metadata is not adopted yet.

## Pre-Commit Checklist

Before committing a managed architecture metadata migration, confirm:

- the adoption mode is recorded
- feature routing was reviewed before creating feature or stage metadata
- no method-layer pseudo-feature remains under `docs/features/`
- every managed feature has the required folder shape
- flat feature YAML is removed or explicitly documented as legacy compatibility
- source metadata points to canonical feature IDs and feature-qualified capability IDs
- shared repo-control surfaces were diffed against the newer starter version when starter updates are being adopted
- `repo_config/adoption-mode.yaml` records the shared-surface review baseline, review timing, and reviewed surface classes for Mode B
- generated discovery was refreshed from source
- generated files were not edited manually
