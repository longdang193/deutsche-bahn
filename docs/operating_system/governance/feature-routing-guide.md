# Feature Routing Guide

Use this guide before creating or changing feature and stage metadata.

For existing-project migrations, use this guide to classify candidates, then follow `docs/operating_system/adoption/project-adoption-migration-guide.md` to migrate feature folders, generated outputs, and source metadata without creating a half-migrated project.

The goal is to keep product/domain architecture separate from the repo operating-system layer. Future projects should not create product features for starter adoption, agent behavior, adapter generation, publication governance, or docs-system management.

## Core Rule

`docs/features/` is for product/domain capabilities.

`docs/operating_system/` is for how the repo plans, validates, publishes, documents, and instructs agents.

If the work is about how the repo operates rather than what the project delivers, route it to the operating-system layer.

## Decision Tree

```text
Is this about product/domain behavior delivered by the project?
  yes -> candidate feature
  no -> continue

Is this about a product/domain workflow boundary or lifecycle stage?
  yes -> candidate stage
  no -> continue

Is this about how the repo plans, validates, publishes, documents, or instructs agents?
  yes -> operating_system layer
  no -> continue

Is this a bounded design or implementation artifact?
  yes -> spec or plan with layer metadata
  no -> keep as prose or project notes until ownership is clear
```

## Feature Eligibility Gate

Create a feature only when it describes product-specific behavior, a domain capability, an operator/user-facing capability, or runtime capability that belongs in the project architecture.

A feature candidate should usually satisfy most of these checks:

- it describes something the project delivers to users, operators, or downstream systems
- it can be linked to product code, runtime config, tests, docs, stages, deployment behavior, or validation evidence
- it belongs in the product architecture, not only the repo workflow
- it may need status, dependencies, capabilities, evidence, and history over time

Do not create features for:

- starter adoption
- repo operating-system setup
- intent-layer setup
- planning method changes
- docs governance
- adapter generation
- generated `AGENTS.md` or generated rule sync
- agent skills, rules, or instructions
- publication allowlists and private/public repo policy
- GitNexus or private analysis-tool setup
- validation tooling for repo governance

Those concerns belong in operating-system docs, adapter sources, skills, rules, repo config, scripts, or operating-system specs/plans.

## Stage Eligibility Gate

Create a stage only when it represents a product/domain workflow boundary or lifecycle position.

Good stage candidates describe durable workflow positions such as ingestion, validation, preparation, training, promotion, deployment, serving, monitoring, or reporting when those concepts are real for the project.

Do not create stages only to organize repo-method work. For example, adapter sync, publication config review, and agent-rule updates are operating-system tasks, not product stages.

## Correct Destination Table

| Work Type | Correct Home | Avoid |
| --- | --- | --- |
| Product/domain capability | `docs/features/<feature_id>/feature.source.yaml` | `docs/operating_system/` |
| Product workflow stage | `docs/stages/<stage_id>.source.yaml` | feature dependency workaround |
| Repo governance | `docs/operating_system/*.md` | `docs/features/repo-operating-system.yaml` |
| Agent workflow | `.agents/skills/` | product feature metadata |
| Hard agent invariant | shipped root agent docs and operating-system governance | feature capability |
| Source-only generation/publication machinery | source-owned private repo config and source workflows | product feature or consume-only starter docs |
| One-time design | `docs/superpowers/specs/*.md` | permanent feature |
| One-time execution | `docs/superpowers/plans/*.md` | permanent feature |
| Private analysis tooling | operating-system docs or private tool config | public/product feature |

## Capability ID Rules

Capability IDs are feature-qualified stable identifiers, not prose.

Use `<feature_id>.<capability_slug>` when a schema expects managed capability
IDs. The capability slug should be kebab-case.

Good:

```yaml
capability_ids:
  - data-pipeline.data-ingestion
  - semantic-layer.semantic-layer-modeling
  - analytics-serving.pipeline-observability
```

Bad:

```yaml
capability_ids:
  - "Intent layer: project purpose and stakeholders under docs/intent/."
  - "Adapter generation: scripts render AGENTS.md and rules."
```

If a sentence is needed, put it in `summary`, docs prose, a spec, or a plan. Do not use it as a capability ID.

## Feature Dependency Rules

Feature `depends_on` is only for product/domain feature dependencies.

Do not use feature dependencies to express that repo governance, adapter generation, publication config, planning methods, or documentation-system work touches product files.

For operating-system specs and plans, use metadata `targets` to identify affected files and folders:

```yaml
---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/intent/
  - docs/operating_system/
  - .agents/skills/
  - repo_config/
  - scripts/
related_features: []
related_stages: []
---
```

If operating-system work affects a product feature indirectly, describe the impact in the spec or plan body. Do not encode it as a product feature dependency.
## Candidate Classification Metadata

Specs and plans that create or change feature, stage, generated, or source metadata should include a routing block:

```yaml
candidate_type: product_feature | product_stage | operating_system | spec_only | plan_only | generated | obsolete
adoption_mode: starter_method_only | managed_architecture_metadata | legacy_compatibility
creates_feature_metadata: true | false
creates_stage_metadata: true | false
updates_code_metadata: true | false
updates_generated_discovery: true | false
```

Rules:

- if `candidate_type: operating_system`, use `targets` and usually `related_features: []`
- if `creates_feature_metadata: true`, the selected adoption mode must allow feature metadata changes
- if `updates_generated_discovery: true`, the plan must name the generator/check command
- run `python scripts/validate_adoption_shape.py` before committing adoption-shape changes

## Bad vs Corrected Example

Bad feature contract:

```yaml
repo-operating-system:
  feature_id: repo-operating-system
  depends_on:
    - deployment-cicd
  capabilities:
    - "Adapter generation: scripts render AGENTS.md and rules."
```

Problems:

- `repo-operating-system` is method-layer work, not a product feature.
- `deployment-cicd` becomes incorrectly coupled to repo governance.
- The capability entry is prose, not a stable ID.

Correct operating-system plan metadata:

```yaml
---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/intent/
  - docs/operating_system/
  - .agents/skills/
  - repo_config/
  - scripts/
related_features: []
related_stages: []
---
```

Correct operating-system prose destination:

```text
docs/operating_system/project-os-adoption.md
```

## Cleanup Guidance For Misrouted Features

When a project already has a method-layer feature such as `repo-operating-system`:

1. Move durable method guidance into `docs/operating_system/`.
2. Move bounded design or execution history into specs/plans with `layer: operating_system`.
3. Remove the misrouted feature contract from `docs/features/`.
4. Remove feature dependency edges that point from method work to product features.
5. Regenerate feature discovery if the project has architecture sync tooling.
6. Confirm product feature indexes no longer include the operating-system artifact.

## Future Validator Guardrails

A future validator may warn or fail on these patterns:

- feature IDs such as `repo-operating-system`, `agent-rules`, `docs-governance`, or `publication-workflow`
- feature contracts whose refs mostly point to `docs/operating_system/`,
  source-only generation machinery, `.agents/`, `.codex/`, `repo_config/`, or
  scripts
- `depends_on` edges from product features to repo-method concepts
- capability IDs containing spaces, colons, backticks, or sentence punctuation
- generated feature contracts created by hand when the adopted convention expects `feature.source.yaml`

The validator should be advisory at first unless the project has explicitly adopted managed architecture metadata.
