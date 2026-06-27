---
name: required-root-doc-update-prompt
description: Update required root docs so they match current repo behavior and contracts.
type: prompt
stage: maintenance
entry_points:
- use this prompt when its title scope matches the current planning/execution need
prerequisites:
- relevant in-scope roadmap/workstream/thread/spec/plan context is available
next_steps:
- implementation-next-action-gate-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
tags:
- prompt
- maintenance
distribution_tier: starter_kit
---

# Required Root Doc Update Prompt

Use this when the validator-enforced required root docs under `docs/` are
stale, thin, missing subject coverage, or need to be refreshed after repo
changes.

```text
Update the required root docs so they match the current repo shape.

Context:
- project or repo type:
- recently changed areas:
- required root docs that look stale or weak:
- whether optional root docs are also expected:
- whether the repo is `starter_method_only` or `managed_architecture_metadata`:

Please:
1. inspect the current required root docs:
   - docs/setup.md
   - docs/configuration.md
   - docs/usage.md
   - docs/pipeline.md
   - docs/architecture.md
2. determine which required docs are stale, thin, or missing expected subject coverage
3. update them as cross-cutting summaries of the current repo reality
4. avoid duplicating lower-level source-of-truth content from:
   - docs/intent/
   - docs/operating_system/
   - docs/features/
   - docs/stages/
   - docs/generated/
5. call out optional root docs that are now worth adding, if any:
   - docs/api.md
   - docs/testing.md
   - docs/observability.md
   - docs/dataset.md
6. run the validator-facing checks after the update
7. report which required docs were refreshed and which optional docs are still only recommendations
```

Expected output:
- updated required root docs under `docs/`
- a short summary of which required docs were refreshed
- optional root-doc recommendations, if applicable
- validator follow-up result or recommended validation commands
