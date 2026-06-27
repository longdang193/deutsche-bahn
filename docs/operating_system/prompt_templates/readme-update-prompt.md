---
name: readme-update-prompt
description: Update README with implementation-backed product summary and reproducible onboarding steps.
type: prompt
stage: closeout
entry_points:
- need to refresh README after feature delivery or release milestone
- need concise README structure with reproducible setup and run instructions
prerequisites:
- implementation and supporting docs are available for evidence validation
next_steps:
- docs-update-prompt.md
related_skills:
- skill-brainstorming
- skill-verification-before-completion
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- readme
- documentation
distribution_tier: starter_kit
---

Revise `README.md` so it accurately reflects the current project state and is easy for new contributors to follow and reproduce.

Use these sections in this exact order:
1. Who Uses It
2. Problem
3. Solution
4. Key Pipeline Stages
5. Major Features and Engineering Highlights
6. Architecture
7. Getting Started
   - Pre-requisites
   - Setup
   - Reproduce
8. Pending
9. Further Improvement

Scope:
- In scope: `README.md` only
- Out of scope: edits to `docs/**` (linking to existing docs is allowed)

Evidence sources:
- code (`src/**` or equivalent)
- scripts and automation (`scripts/**`, Makefile, task runners)
- configuration/runtime files (`configs/**`, env templates, infra manifests)
- tests/examples used for reproducibility
- existing docs in `docs/` that describe behavior, setup, architecture, API, operations, governance, or usage
- when standard docs exist, prioritize files matching patterns such as:
  - `docs/*api*.md`
  - `docs/*architecture*.md`
  - `docs/*component*boundar*.md`
  - `docs/*config*.md`
  - `docs/*setup*.md`
  - `docs/*usage*.md`
  - `docs/*pipeline*.md`
  - `docs/*observab*.md`
  - `docs/*publish*.md`
- if a pattern has no match, skip it (do not fail)

Writing rules:
- Treat implementation as source of truth.
- Remove or rephrase claims not supported by code, config, tests, scripts, or authoritative docs.
- Do not present unimplemented behavior as complete.
- Keep README concise; link to deep docs instead of duplicating them.
- Use terminology consistent with codebase.
- Ensure every command/path/link is valid and runnable.
- If details are uncertain, place them under “Pending” or “Further Improvement” as appropriate.

Rules for “Pending” and “Further Improvement”:
- Both sections must be product-specific.
- Do not include repo-control-layer, governance-process, or meta-documentation tasks.
- “Pending” = in-scope product capabilities expected soon or partially implemented gaps.
- “Further Improvement” = longer-horizon product enhancements, optimizations, or UX/quality upgrades.
- Each bullet should describe user/product impact, not internal documentation workflow.

Section intent:
- Who Uses It: primary user groups and usage context.
- Problem: concrete pain points or business/technical gap addressed.
- Solution: project approach and value in plain language.
- Key Pipeline Stages: ordered lifecycle/stages with brief purpose per stage.
- Major Features and Engineering Highlights: most important capabilities and engineering strengths.
- Architecture: concise system/component overview with links to deeper docs.
- Getting Started:
  - Pre-requisites: required tools, runtimes, access, credentials.
  - Setup: installation and configuration steps.
  - Reproduce: exact commands to run and how to confirm expected results.
- Pending: near-term product gaps or partially implemented product behavior.
- Further Improvement: longer-term product enhancements and optimizations.

Execution steps:
1) Audit current README against required structure.
2) Validate each major claim against evidence sources.
3) Rewrite for clarity, precision, and scannability.
4) Verify commands, paths, and links.
5) Move unresolved or not-yet-shipped items to “Pending” or “Further Improvement”.

Required output:
- final README heading outline
- summary of key changes (added/updated/removed)
- verification notes:
  - commands checked
  - links checked
  - items moved to Pending/Further Improvement
