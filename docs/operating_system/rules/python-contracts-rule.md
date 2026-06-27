---
name: python-contracts
description: Enforce Python contract/style/type expectations for generated and edited
  Python files.
alwaysApply: false
required_reads:
- .agents/skills/skill-python-code-standards/SKILL.md
- docs/operating_system/governance/repo-governance.md
tags:
- rule
- python
- contracts
distribution_tier: starter_kit
---

# Python Contracts Rule

For Python changes, follow the Python standards workflow and keep contract,
typing, and verification expectations consistent.

## Required

- Python files with behavioral weight (entry points, orchestration/workflow files, test modules, migrations/cleanup scripts, and shared utilities) must declare a top-of-file `@meta` block.
- Governed Python `@meta` blocks must include `ownership` with value `feature` or `infrastructure`.
- Python metadata must be capability-first when stable capability IDs exist upstream.
- When `ownership: feature`, `@meta.capabilities` is required and every value must resolve to an upstream `capability_id` in `docs/features/<feature_id>/feature.source.yaml`.
- When `ownership: infrastructure`, `@meta.capabilities` may be omitted only under explicit infrastructure exception policy; if provided, each capability must still resolve upstream.
- Draft metadata only after reading lifecycle ownership surfaces in order: feature source first, generated feature contract only as needed, lineage evidence only as needed.
- Keep `lifecycle` as mapping shape with explicit `status` value.

## Forbidden

- Omit `ownership` in governed Python `@meta` blocks.
- Mark feature-owned modules as infrastructure to bypass capability requirements.
- Add a redundant Python `@meta` features list when capability linkage already determines stable feature ownership.
- Use generic or placeholder capability IDs that do not map to upstream feature capability definitions.
- Use placeholder responsibility text (`TODO`, `TBD`, `placeholder`, equivalent) in `@meta` blocks.
- Use function-level `@capability` on helpers, wrappers, tests, adapters, or incidental callers.
- Swallow errors with bare `except` blocks or unlogged exception handling.
- Use broad `type: ignore` comments without an error code and short reason.

## Guidance

- Prefer precise Python types and narrow structures over `Any` when editing or adding Python code.
- Use `@proves` in test-function docstrings for capability proof; reserve file-level capabilities for implementation ownership or materially lineage-relevant test modules.
- Do not invent capability IDs in code metadata. Define capability IDs upstream first, then reference them in `@meta.capabilities`.
