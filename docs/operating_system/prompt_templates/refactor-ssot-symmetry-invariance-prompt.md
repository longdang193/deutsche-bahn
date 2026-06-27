---
name: refactor-ssot-symmetry-invariance-prompt
description: Analyze codebase for refactoring opportunities using SSOT, symmetry, and invariance, then propose bounded, risk-aware actions.
type: prompt
stage: planning
entry_points:
- refactoring direction is needed across one or more modules with possible conceptual drift
- current implementation shows divergence, duplicated logic, or weak shared contracts
prerequisites:
- in-scope repo/module boundaries are identified
- target constraints and non-goals for refactoring are identified
next_steps:
- plan-prompt.md
- implementation-next-action-gate-prompt.md
- patch-and-pattern-detection-prompt.md
related_skills:
- skill-planning-dispatch
- skill-python-refactoring-expert
- skill-systematic-debugging
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/governance/repo-governance.md
tags:
- prompt
- planning
- refactoring
distribution_tier: starter_kit
---

# Refactor SSOT + Symmetry + Invariance Prompt

## Not For

direct implementation without analysis and bounded action plan

```text
Analyze the scoped codebase and propose refactoring actions using these principles:
- SSOT (single source of truth)
- symmetry (equivalent concepts should use equivalent structure)
- invariance (shared rules/defaults/contracts should stay consistent across surfaces)

Scope:
- repo/module boundaries:
- key files/folders:
- constraints:
- non-goals:

Please:
1. Map equivalent concepts and their current implementations across scope.
2. Detect and report:
   - drifts: equivalent concepts that diverged
   - contradictions: conflicting names/rules/defaults/schemas/behavior
   - unused or obsolete code: dead branches, stale helpers, deprecated assumptions, unused config/fields
   - hidden duplication: different-looking logic serving same purpose
   - missing contracts: behavior that should be enforced via shared type/schema/enum/fixture/test
   - risky edge cases: inconsistencies likely to cause bugs, invalid artifacts, or bad UX
3. Build a refactor action model:
   - normalization target (what SSOT should become)
   - symmetry model (how equivalent flows should align)
   - invariants to preserve (must not regress)
4. Propose prioritized actions with bounded scope:
   - action id
   - rationale
   - impacted files
   - risk level (low/medium/high)
   - required tests/contracts
   - dependency ordering
5. Provide migration and safety controls:
   - backward-compatibility needs
   - deprecation/removal path
   - rollback/containment strategy
6. Recommend execution path:
   - what can be patched now
   - what needs spec/plan first
   - one selected next action and why alternatives are not yet eligible

Output format:
- A) Executive refactor thesis (SSOT/symmetry/invariance target)
- B) Findings matrix by category (drift, contradiction, obsolete, hidden duplication, missing contract, edge case)
- C) Prioritized refactor action plan
- D) Validation plan (tests, schema checks, invariants)
- E) Selected next action
```

Expected output:
- structured refactor analysis plus prioritized, bounded next-action plan
