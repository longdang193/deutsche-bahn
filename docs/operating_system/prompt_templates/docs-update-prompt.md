---
name: docs-update-prompt
description: Reconcile docs folder content with implemented behavior and intended outcomes.
type: prompt
stage: closeout
entry_points:
- need to update docs/**/* after implementation changes
- need structured doc drift reconciliation before closure
prerequisites:
- current code, config, and test surfaces are available for verification
next_steps:
- readme-update-prompt.md
related_skills:
- skill-doc-system-lifecycle
- skill-verification-before-completion
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- documentation
- reconciliation
distribution_tier: starter_kit
---

Bring docs/ into alignment with current shipped implementation and intended outcomes, so docs are accurate, navigable, and maintainable.

Scope:
- In scope: docs/**/* (all documentation pages in docs folder)
- Out of scope: README.md (handled by separate prompt), unless explicitly requested

Inputs:
- Source code: src/** (or equivalent code directories)
- Runtime/config: configs/**, env docs, infra definitions
- Automation/scripts: scripts/**, tooling
- Tests/examples: tests/**, examples/**
- Product/intent docs: docs/intent/** or equivalent vision/spec sources

Principles:
1) Truth from implementation: if docs conflict with code/tests/config, update docs.
2) No feature invention: do not document behavior not present in implementation.
3) Explicit uncertainty: if behavior unclear, mark as Pending with blocker.
4) Separation of concerns:
   - intent docs = outcomes/constraints
   - architecture docs = structure/flows/decisions
   - api docs = contracts and examples
   - setup/usage docs = operational instructions
5) Keep terminology consistent across pages.

Execution steps:
1. Inventory docs pages
   - group by type: intent, architecture, API, setup, usage, operations, governance
2. Drift audit
   - extract major claims from each doc
   - verify against code/config/tests/scripts
   - classify claims: valid / stale / missing / ambiguous
3. Reconcile
   - update stale or ambiguous claims
   - add missing shipped behavior
   - remove obsolete/speculative sections
4. Consistency pass
   - align naming, section structure, and cross-links
   - remove duplication or contradictory guidance
5. Validation pass
   - verify command snippets, file paths, env vars, and examples
6. Closeout report
   - summarize edits and remaining gaps

Required output:
A) Changed files with short rationale per file
B) Evidence table:
   - documentation claim
   - implementation evidence (file path + symbol/section)
   - action (kept/updated/removed/pending)
C) Pending gaps:
   - issue
   - blocker
   - owner (if known)
   - next action
D) Risk notes (high-impact assumptions needing follow-up)

Definition of done:
- Docs reflect current implementation.
- Major intended outcomes are mapped to documented capabilities or explicit pending items.
- No known stale claims remain in scoped docs.
- Cross-doc navigation and terminology are consistent.
