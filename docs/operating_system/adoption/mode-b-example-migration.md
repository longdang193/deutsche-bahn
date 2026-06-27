# Mode B Example Migration

Use this example when a project has one legacy product feature contract and wants to migrate it into managed architecture metadata.

This example is private-source onboarding material. It explains how to migrate
a private repo into the starter's managed metadata shape and should not be
published to a curated public mirror unless it has been intentionally rewritten
as product-facing documentation.

This is an example only. Replace `billing-insights` with the real product feature ID and keep operating-system adoption work out of `docs/features/`.

## Starting Point

The project has selected Mode B:

```yaml
adoption_mode: source_of_truth_owner (alias: managed_architecture_metadata)
source_of_truth_owner (alias: managed_architecture_metadata): true
legacy_feature_contracts: false
architecture_generator: scripts/sync_architecture_docs.py
starter_sync:
  starter_baseline_ref: starter@2026-04-21
  last_shared_surface_review_at: 2026-04-21
  reviewed_surface_classes:
    - repo_config
    - operating_system_docs
    - skills
    - adapters
    - generated_instruction_surfaces
    - validation_and_sync_scripts
  divergences:
    - path: docs/operating_system/procedures/publication-workflow.md
      class: operating_system_docs
      status: customized
      rationale: Keep project-specific publication notes while inheriting newer starter boundaries.
```

The legacy feature currently lives as a flat YAML file:

```text
docs/features/billing-insights.yaml
docs/stages/analytics.source.yaml
src/billing/reporting.py
tests/test_billing_reporting.py
```

## Target Shape

The feature should move to a managed folder:

```text
docs/features/billing-insights/
  feature.source.yaml
  billing-insights.yaml
  lineage.generated.yaml
  history.md
docs/generated/architecture_dag.yaml
docs/generated/capability_lineage.yaml
docs/stages/analytics.source.yaml
src/billing/reporting.py
tests/test_billing_reporting.py
```

Ownership:

- `feature.source.yaml` holds the human-owned feature meaning.
- `billing-insights.yaml` is generated or normalized current-state output.
- `lineage.generated.yaml` is generated evidence.
- `history.md` holds feature-local notes outside generated blocks and should use the starter partial-generated history pattern.
- `docs/generated/architecture_dag.yaml` and `docs/generated/capability_lineage.yaml` are the canonical aggregate generated-discovery outputs for the current managed target.
- in managed mode, those generated surfaces are not just present-by-name; they
  should match the validator-enforced starter target shape

## Example Sequence

1. Confirm `repo_config/adoption-mode.yaml` is set to `source_of_truth_owner (alias: managed_architecture_metadata)`.
2. Classify `billing-insights` as a real product feature, not starter adoption or repo-method work.
3. Diff shared repo-control files from the newer starter version and bring forward stronger repo-method changes before or alongside the feature migration. At minimum, review:

```text
repo_config/*
docs/operating_system/*
.agents/skills/*
docs/operating_system/templates/agents/*
scripts/validate_*.py
scripts/sync_*.py
```

4. Record the review in `repo_config/adoption-mode.yaml` with the starter baseline reviewed, the shared surface classes reviewed, and any intentional divergences.
5. Create `docs/features/billing-insights/`.
6. Move semantic content from `docs/features/billing-insights.yaml` into `docs/features/billing-insights/feature.source.yaml`.
7. Normalize capabilities to feature-qualified stable IDs:

```yaml
capabilities:
  - capability_id: billing-insights.billing-revenue-summary
    statement: Summarize billed revenue by account and reporting period.
    state: active
```

Do not carry forward older source-level fields such as `owner`,
`primary_stage`, `stages`, `refs`, or `keywords` unless they are first mapped
into the current source/generated/history boundary.

8. Update `docs/stages/analytics.source.yaml` so stage ownership references the feature:

```yaml
primary_features:
  - billing-insights
```

9. Update code and tests that feed lineage to reference canonical feature IDs and feature-qualified capability IDs:

```python
# @feature billing-insights
# @capability billing-insights.billing-revenue-summary
```

```python
# @proves billing-insights.billing-revenue-summary
```

10. Re-run adapter sync as well if the starter diff changed adapter sources, mappings, or generated instruction surfaces:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

11. Run the project architecture generator or sync workflow so generated feature contracts, lineage, and discovery come from source.
12. Retire older generated-discovery files such as `features_index.yaml`,
    `feature_overview.md`, `stages_index.yaml`, or similar summary-index sets if
    the repo is moving onto the current starter-style managed target.
13. Remove the flat `docs/features/billing-insights.yaml` after the generated folder contract exists.
14. Validate:

```powershell
python scripts/validate_adoption_shape.py
git diff --check
```

15. Run the project test suite for the changed feature.
16. Commit only after source metadata, shared repo-control updates, the recorded starter sync review, generated outputs, validation, and tests agree.

History target after migration:

- keep `history.md`
- use the starter partial-generated history structure
- move any useful manual changelog notes into `## Human Notes`
- do not keep version-number changelog sections as the primary history contract

## What Not To Do

Do not leave both of these as authoritative current truth:

```text
docs/features/billing-insights.yaml
docs/features/billing-insights/feature.source.yaml
```

Do not create this feature for starter adoption, adapter work, publication setup, or agent rules. Those are operating-system concerns and belong in `docs/operating_system/` or operating-system specs/plans with explicit `targets`.
