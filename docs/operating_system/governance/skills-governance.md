# Skills Governance

This document defines how skills are formalized in the private repo.

## Canonical Surface In Phase 2

The canonical Codex skill surface remains:

```text
.agents/skills/
```

This repo does not currently use a hidden `.codex/` directory as the
canonical Codex skill root. The active ownership model is:

- `AGENTS.md` for repo-wide agent instructions
- `.agents/skills/` for canonical reusable skills
- `.agents/agents/` for optional lightweight repo-local playbooks
- `docs/operating_system/` for human governance
- `.codex/rules/` for generated rules output

Current starter-kit governance keeps canonical skill ownership in
`.agents/skills/`.

Any future migration stays deferred until a source-owned generation model is
stable and consume-only starter-kit output remains truthful.

## Codex Skills Model

This repo follows the Codex Skills model for formal skill shape:

- one skill folder per focused workflow
- `SKILL.md` as the required entrypoint
- optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml` only when they materially help the workflow
- strong `description` fields so Codex can trigger the right skill reliably

## Canonical Identity Rule

Path identity is canonical for skills.

- canonical skill identity = folder name under `.agents/skills/`
- metadata `name` must exactly match that folder name
- generated runtime skill paths should preserve that same identity
- deploy and drift checks should rely on this structural identity instead of a separate naming translation layer

This keeps validation and runtime deployment deterministic:

- validators only need to confirm path-to-metadata alignment
- generated runtime outputs can reuse canonical names directly
- deploy reconciliation stays simpler during renames

## What Skills Are For

Skills are for:

- reusable execution workflows
- debugging methods
- planning methods
- review workflows
- focused task workflows

Skills are not for:

- repo governance
- publication policy
- broad operating-system rules
- vendor-specific execution-policy syntax

Those belong in:

- `docs/operating_system/`
- `.codex/rules/`

`.codex/rules/` is a generated rules surface. It is not the canonical home for
skills, agent memory, or repo governance.

## Relationship To Playbooks

If `.agents/agents/` exists in this repo:

- it is an optional specialist executor layer
- it does not replace `.agents/skills/`
- it must stay narrower and more role-specific than the skill layer
- it must not become a second governance surface

## Quality Rules

Each skill should:

- solve one focused job
- keep `SKILL.md` readable and trigger-oriented
- use helper files only when they add real value
- avoid turning into a general project manual


## Validation Rule

New skills are not considered trustworthy just because they were written down.

Before a new skill is treated as landed:

- validate it with the `skill-skill-writing-skills` workflow
- define a baseline failure scenario
- define the expected post-skill success behavior
- tighten loopholes when the first version still leaves room for bad shortcuts
- capture a short reusable validation summary in
  `docs/operating_system/skills-validation-report.md` when the change affects
  repo-wide routing or governance behavior

In this repo, skill additions should be treated as process TDD rather than
plain documentation edits.
## Migration Rule

If future work introduces a new source-owned generation layer for skills, that
layer must not become canonical until:

- sync behavior is defined
- verification proves outputs are trustworthy
- Codex discovery still works cleanly through `.agents/skills/`
