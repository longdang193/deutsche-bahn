---
name: doc-contracts
description: Enforce document contract consistency for templates, lifecycle metadata,
  and generated surfaces.
alwaysApply: true
required_reads:
- docs/operating_system/governance/repo-governance.md
- docs/operating_system/runtime/agent-runtime-metadata-schema.md
tags:
- rule
- docs
- contracts
distribution_tier: starter_kit
---

# Document Contracts Rule

Maintain template/lifecycle metadata integrity, avoid manual edits to generated
surfaces, and preserve source-of-truth document boundaries.

## Required

- README must remain a synthesized orientation layer rather than a parallel source of truth.
- Semantic feature changes must be made in `docs/features/<feature_id>/feature.source.yaml`, not in generated feature contracts.
- Semantic stage changes must be made in `docs/stages/<stage_id>.source.yaml`, not in generated stage contracts.

## Forbidden

- Manually edit generated feature contracts, generated stage contracts, `lineage.generated.yaml` files, `docs/generated/*` discovery outputs, or generated history blocks.
- Add `manual_refs` to `feature.source.yaml`.
- Force a new spec when a bounded change is already design-clear after triage and the user explicitly asked for an implementation plan.

## Guidance

- Canonical truth should flow downward from upstream owning layers; lower layers should derive or reference that truth rather than restating the same semantic fact manually.
- If generated refs are missing, patch metadata at the owning source instead of hand-editing generated outputs.
