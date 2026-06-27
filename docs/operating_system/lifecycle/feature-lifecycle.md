# Feature Lifecycle

This document defines how managed features are classified and tracked.

## Core Principle

Feature lifecycle sits below the repo's intent and operating-system layers:

- `docs/intent/` owns the project what-and-why
- `docs/operating_system/` owns build method and governance
- `docs/features/` owns managed feature meaning and lifecycle state

Features remain the primary lifecycle units for product behavior, but they do
not replace project intent or repo method.

A real managed feature should have a current-state contract named after the
concrete feature id, for example
`docs/features/model-training-pipeline/model-training-pipeline.yaml`.

Stages help with architecture and planning, but features remain the primary lifecycle units.

Feature YAML is a contract layer, not a general runtime configuration store.
Workflow defaults and environment-tuned settings still belong under `configs/`.

For features that opt into architecture metadata generation, the human-owned
source lives at `docs/features/<feature_id>/feature.source.yaml` and the stable
concrete feature-id contract is generated. Generated contracts keep the same
reader-facing path while reducing manual drift. `<feature_id>` is a placeholder
in docs, not a literal filename to create.

Detailed generated evidence for opted-in features lives beside the feature at
`docs/features/<feature_id>/lineage.generated.yaml`. Feature history is now a
hybrid surface: the generator owns a bounded timeline section fed from
completed-plan metadata, while humans keep narrative notes below that block.
That timeline is not just a flat list of spec and plan paths. The current
managed target is a richer completed-change record list like the one used in
`customer-churn-prediction-azureml/docs/features/model-training-pipeline/lineage.generated.yaml`,
with entries such as:

- `completed_at`
- `source_plan`
- `change_id`
- `summary`
- `capabilities`
- `verification`
- `outcome`

Older timeline entries shaped only like `{kind, path}` are legacy migration
debt, not the current starter-aligned target.

Reading rule of thumb for agents and reviewers:

- start with `feature.source.yaml`
- read the generated contract only when the assembled current-state view is needed
- read `lineage.generated.yaml` only for evidence, ownership, or drift questions
- read `history.md` only when human narrative context is required
- do not read the full feature folder by default

## Classification

Use these classifications for meaningful feature work:

- `ADD`
  - new capability with no existing equivalent
- `MODIFY`
  - behavior change to an existing capability
- `REPLACE`
  - new capability that supersedes an older one

If a change is only a defect correction with no meaningful contract change, update code and docs as needed without inventing a new feature.

## Status Flow

```text
planned -> draft -> building -> rollout -> active -> deprecated
```

Use the feature YAML to track the current state.

## Required Feature Contract Shape

Each managed feature should define:

- `feature_id`
- `name`
- `status`
- `type`
- `summary`
- `invariants`
- `domains`
- `depends_on`
- `capabilities`
- `refs`

Opted-in generated features should also assign stable IDs inside
`feature.source.yaml`:

- `invariant_id` for each invariant
- `capability_id` for each capability
- optional `satisfies` links from capabilities to invariants

Capability IDs are downstream of features. Use feature-qualified IDs such as
`<feature_id>.<capability_slug>` so downstream metadata can derive feature
ownership from the capability ID instead of re-entering it.

Do not add `manual_refs` to `feature.source.yaml`. Feature refs are generated
from owning metadata on code, tests, docs, specs, plans, configs, and AML
components. If a generated ref is missing, patch the metadata at the owning
source instead of adding a feature-local manual list.

Generated `refs.code` should stay canonical and readable. Supporting files may
carry awareness metadata, but primary feature refs should point to entrypoints
or canonical `@capability` nodes.

Generated feature contracts should expose freshness metadata:

- `last_updated_at`
- `latest_change_id`
- `revision`

This is the current managed migration target, matching richer generated
contracts such as
`customer-churn-prediction-azureml/docs/features/notebook-hpo/notebook-hpo.yaml`.
An empty `timeline: []` does not exempt a managed generated contract from this
freshness schema.

Do not keep a manual `version` field in `feature.source.yaml`; feature
freshness belongs to generated metadata in `<feature_id>.yaml`, not the
human-owned semantic source.

When a feature participates in generated stage contracts, keep that linkage in
`feature.source.yaml` under `stage_participation`:

```yaml
stage_participation:
  - stage_id: data_validate
    role: supporting
    capability_ids:
      - fixed-train.share-validation-prep-contracts
```

Rules:

- `stage_id` must reference a real stage source under `docs/stages/*.source.yaml`
- `role` must match the role declared by the stage source
- `capability_ids` should contain only the feature-qualified capability IDs
  from this feature that are truly stage-relevant
- use an empty `capability_ids: []` list only when the feature is stage-aware as
  context or downstream consumer but has no canonical capability node to expose
  in the stage contract

The required opted-in feature folder shape is:

```text
docs/features/<feature_id>/
  feature.source.yaml
  <feature_id>.yaml          # replace with the concrete id, e.g. model-training-pipeline.yaml
  lineage.generated.yaml
  history.md
  README.md
```

`README.md` is optional and should explain current behavior only when prose adds
value; it should not repeat generated contracts or lineage.

Validation in `source_of_truth_owner (alias: managed_architecture_metadata)` mode enforces the required set:

- `feature.source.yaml`
- `<feature_id>.yaml`
- `lineage.generated.yaml`
- `history.md`

It also treats the generated artifacts as schema-enforced managed contracts:

- `<feature_id>.yaml` must keep the canonical generated feature-contract shape
- `lineage.generated.yaml` must keep the canonical evidence-oriented schema
- `history.md` must keep the generated history boundaries plus `## Human Notes`

`history.md` is required for opted-in features and should follow this steady-state
shape:

- one generated block between `<!-- GENERATED HISTORY START -->` and
  `<!-- GENERATED HISTORY END -->`
- one human-owned `## Human Notes` section below the generated block
- no manual edits inside the generated markers

Generated feature contracts should also keep the canonical contract structure:

- top-level feature fields such as `feature_id`, `name`, `status`, `type`,
  `summary`, `invariants`, `domains`, `depends_on`, `capabilities`, and `refs`
- `refs` grouped by canonical families like `code`, `tests`, `specs`, `plans`,
  `docs`, `configs`, and `components`
- freshness metadata such as `revision`, `latest_change_id`, and
  `last_updated_at`

## Feature And Stage YAML Formatting

Feature and stage contract YAML should follow one visible formatting rule:

- quote strings only when YAML requires it or literal preservation depends on it
- avoid unnecessary quotes on ordinary prose entries
- preserve field order and contract meaning during formatting cleanup
- keep formatting changes separate from semantic contract changes when practical
- never manually edit generated feature contracts; edit `feature.source.yaml`
  and rerun the generator instead

Canonical formatter/check path:

```powershell
.\scripts\format_contract_yaml.py --check
.\scripts\format_contract_yaml.py
```

The first command reports drift without rewriting. The second normalizes the
targeted contract YAML files.

Canonical architecture metadata generation/check path for opted-in features:

```powershell
.\tools\docs\generate_architecture_metadata.py --check
.\tools\docs\generate_architecture_metadata.py
```

YAML artifacts can participate in generated feature and stage refs through
comment metadata:

```yaml
# @architecture
# owner: model-training-pipeline
# features:
#   - model-training-pipeline
# stages:
#   - fixed_train
# role: config
# canonical: true
```

Use comment metadata for AML components and configs so runtime YAML schemas stay
unchanged.

Canonical full sync/check workflow:

```powershell
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py
.\.venv\Scripts\python.exe scripts/sync_architecture_docs.py --check
```

Canonical repo-wide validation workflow:

```powershell
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py
```

Use the sync command when feature/source/spec/plan/code/test/doc metadata has
changed and generated feature outputs need refresh. Use the repo-contract
validator when you need the broader gate across generated files, metadata
coverage, mixed-boundary feature histories, adoption-shape rules, and repo-config
surfaces.

In that command pair, `--fast` means the hook-facing subset. It still runs the
architecture sync check path and skips only the extra validator-specific pytest
pass.

Lineage completeness rule for opted-in generated features:

- active capabilities should resolve to `complete` whenever possible
- temporary rollout gaps must be declared in `feature.source.yaml` under
  `lineage_exceptions`
- generated lineage may show `excepted`, but `incomplete` active capabilities
  are treated as validation failures
- if a capability cannot be owned cleanly, narrow or split the capability
  instead of weakening the enforcement rule

## Planning Gate

Before writing a spec or plan, determine:

- whether an affected feature already exists
- whether the change is `ADD`, `MODIFY`, or `REPLACE`
- which feature docs and generated surfaces must be updated
- which capability IDs, invariant IDs, source metadata, code markers, and test
  proof markers are affected
- whether detailed evidence belongs in feature-local lineage or a human note
  belongs in history
- whether a completed plan should create or update generated history entries for
  the affected feature

Cross-cutting operating-system changes may use `Affected features: none`.

## Completion Rule

A managed feature is not truly complete until:

- code is updated
- the feature source and generated feature contract are updated when the feature
  has opted into generation
- supporting docs are updated as needed
- generated discovery is refreshed when source layers changed
- feature-local lineage is refreshed when capability evidence or plan metadata
  changes
- generated feature history is refreshed when completed implementation-plan
  metadata changes for the feature
- stage participation metadata stays in sync with any stage source that lists
  the feature
- active capability lineage is either complete or explicitly excepted in the
  feature source; silent unresolved gaps are not an acceptable finished state

Human authors should update `history.md` notes only when the generated section is
not enough on its own, for example:

- operator context matters
- rollout or migration nuance matters
- cloud-proof or validation meaning matters
- a manual explanation is needed to interpret the generated entries
