# Precedence

Runtime precedence is provider-native first. Canonical repo sources are compiled into the
runtime surfaces each provider actually loads.

## Rule Order

1. emergency deny/block rules
2. root runtime instructions (`AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`)
3. provider-native skills, including generated workflow-skills
4. provider-native rules files when the provider supports direct rule loading
5. canonical shared rules and workflow documents as source material
6. personal preferences

## Provider Notes

- Codex: `AGENTS.md` is authoritative; `rules/` mirrors are not a behavioral dependency
  unless the runtime explicitly supports them.
- Claude: `CLAUDE.md`, `rules/`, and `skills/` are provider-native runtime surfaces.
- Antigravity/Gemini: `GEMINI.md` and `antigravity/skills/*/SKILL.md` are the
  primary runtime surfaces; `rules/` mirrors are informational unless verified.

## Conflict Policy

- fail on duplicate rule/workflow/prompt names in the same layer
- fail on missing `required_reads` targets
- fail on broken prompt/workflow references in metadata `next_steps`
- fail when generated runtime manifests or workflow-skills drift from canonical sources
