# Stage Lifecycle

This document defines how stages are used as architectural boundaries.

## Core Principle

Stages are navigation and workflow-boundary maps.

Features remain the primary lifecycle and capability owners.

## What A Stage Is

A stage is a stable workflow boundary with:

- a clear purpose
- clear inputs and outputs
- meaningful transition points
- a relationship to one or more features

The current stage map is:

- `data_validate`
- `data_prep`
- `fixed_train`
- `model_sweep`
- `model_promote`
- `online_deploy`
- `monitor`

## Stage / Feature Relationship

- one stage can involve many features
- one feature can span multiple stages
- stages explain where work happens
- features explain what capability exists and how it evolves
- generated stage refs point back to canonical feature, code, test, doc, config, and component surfaces

## Stage Contract Shape

Human-owned stage source files live at:

```text
docs/stages/<stage_id>.source.yaml
```

Generated current stage contracts live at:

```text
docs/stages/<stage_id>.yaml
```

Humans edit the source files. The generator owns the concrete stage YAML files.
In managed repos, the adoption validator now treats generated stage contracts as
schema-enforced artifacts rather than loose generated suggestions.

Stage source files may contain:

- `stage_id`
- `name`
- `status`
- `purpose`
- `workflow_position`
- `primary_features`
- `supporting_features`
- `depends_on`
- `hands_off_to`
- `inputs`
- `outputs`
- `invariants`
- `human_notes`

Stage source files must not contain generated refs:

- `feature_refs`
- `capability_refs`
- `code_refs`
- `test_refs`
- `doc_refs`
- `config_refs`
- `component_refs`

If a generated ref is missing, patch metadata at the owning source instead of hand-editing the generated stage file.

Generated stage contracts should stay in the flat canonical shape produced by
the generator, with top-level keys such as:

- `stage_id`
- `name`
- `status`
- `purpose`
- `feature_refs`
- `capability_refs`
- `code_refs`
- `test_refs`
- `doc_refs`
- `config_refs`
- `component_refs`

Older nested stage-contract shapes like:

```yaml
enrich:
  name: Enrich
  refs:
    docs: []
```

are migration debt, not valid current managed output.

## Metadata Inputs

Generated stage contracts use:

- feature source metadata from `docs/features/*/feature.source.yaml`
- feature-side `stage_participation` blocks as the canonical capability filter
- canonical code evidence from `@capability` and entrypoint metadata
- test proof evidence from `@proves`
- root and feature doc frontmatter with `explains.stages`
- YAML `# @architecture` metadata in `configs/*.yaml`
- YAML `# @architecture` metadata in `aml/components/*.yaml`

Stage-to-feature linkage is bidirectional:

- stage sources declare workflow participation intent through
  `primary_features` and `supporting_features`
- feature sources declare stage participation through `stage_participation`
- generated `feature_refs` are assembled only after those two sides agree
- generated `capability_refs` come from the feature-side
  `stage_participation[].capability_ids` subset rather than every capability on
  each referenced feature

Primary `code_refs` should stay canonical and readable. Supporting helper awareness belongs in `docs/generated/architecture_dag.yaml`, not in every stage contract.

## When To Use Stage Classification

Use stage classification when work is:

- pipeline-heavy
- boundary-heavy
- transition-heavy
- cross-feature within one architectural flow

Stage-heavy triage should name:

- affected stages
- affected features
- whether the primary lens is stage, feature, or mixed

## Validation

Use the canonical architecture sync/check path after stage source or architecture metadata changes:

```powershell
.\.venv\Scripts\python.exe scripts\sync_architecture_docs.py
.\.venv\Scripts\python.exe scripts\sync_architecture_docs.py --check
```

The check path must fail for stale generated stage contracts or generated-only fields in stage source files.
It must also fail when stage sources and feature sources disagree about stage
membership or feature role.

For the broader repo gate, use:

```powershell
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py
```

That validator keeps stage-contract checks in the same pass as adoption-shape
validation, repo-config validation, metadata coverage enforcement, and
partial-generated feature-history boundary rules.

Here `--fast` still includes the architecture sync check path. It skips only
the extra validator-specific pytest pass.
