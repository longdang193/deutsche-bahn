# Project Agent Instructions

This file is the repo-wide instruction layer for Codex.

## Scope

Use this file for repo-wide behavior only. More specific directory instructions may override it.

## Repo Rules

- The private repo is the development source of truth.
- The public repo is updated only through the curated publish workflow.
- Repo governance lives in `docs/operating_system/`.
- Agent memory lives in `docs/operating_system/agent_memory/`.
- Skills live in `.agents/skills/`, which remains the canonical Codex skill surface.
- Runtime/workflow config lives in `configs/`, while repo/system config lives in `repo_config/`.
- `.codex/rules/` is a generated rules output surface, not the canonical home for skills or memory.
- Skills should follow the Codex Skills model: one focused workflow per skill, with `SKILL.md` as the primary entrypoint.

## Working Expectations

- Keep changes aligned with the owning code and doc layer.
- Consult relevant agent memory before planning when the task touches reusable repo workflows or known invariants.
- Consult `docs/operating_system/agent_memory/failure-ledger.md` during debugging, retries, or after important mistakes.
- Update the agent-memory layer when a significant reusable lesson emerges.
- Update tests and docs when behavior or contracts change.
- Do not expose private operating-system or agent-core material through the public mirror.
- If you change `docs/operating_system/templates/agents/*`, generated `AGENTS.md`, or generated provider runtime rules, run the sync and verify scripts before considering the change complete.

## GitNexus

GitNexus is an optional private-only analysis tool for this repo. Use it when it helps with cross-file tracing, impact analysis, or repo navigation, but do not treat it as a replacement for source code, tests, or repo governance docs.

- Check freshness before high-trust GitNexus use with `.\scripts\get_gitnexus_freshness.ps1`, especially for impact analysis, refactoring, or pre-commit scope checks.
- Use `gitnexus_impact` before higher-risk refactors, renames, or changes to shared orchestration code.
- Use `gitnexus_detect_changes()` as an extra safety check when graph-level confirmation is useful before committing.
- If GitNexus is stale:
  - exploration may still use it as an advisory lookup layer
  - debugging may still use it as advisory if conclusions are labeled accordingly
  - higher-risk impact/refactor work should refresh first when possible
- If GitNexus refresh fails, continue source-first with code, tests, and active docs rather than blocking safe work.
- If GitNexus output conflicts with the current source code or tests, trust the source code and tests.
- Keep GitNexus artifacts private-only; `.gitnexus/` and any GitNexus-specific notes must not leak into the public mirror.

Practical GitNexus workflow:

- for architecture lookup, start with `gitnexus_query()` and `gitnexus_context()`
- for debugging, use GitNexus as a tracing aid, but keep conclusions source-first if freshness is stale
- for higher-risk refactors, use `gitnexus_impact()` before edits when it materially improves safety
- for broader changes, `gitnexus_detect_changes()` is a useful pre-commit scope check, not a blanket requirement for every tiny edit

If GitNexus needs a refresh on this Windows machine, prefer:

```powershell
npx gitnexus analyze
```

If the local `npx` path fails, use this fallback:

```powershell
corepack pnpm --allow-build=@ladybugdb/core --allow-build=onnxruntime-node --allow-build=protobufjs --allow-build=sharp --allow-build=tree-sitter --allow-build=tree-sitter-c --allow-build=tree-sitter-c-sharp --allow-build=tree-sitter-cpp --allow-build=tree-sitter-go --allow-build=tree-sitter-java --allow-build=tree-sitter-javascript --allow-build=tree-sitter-kotlin --allow-build=tree-sitter-php --allow-build=tree-sitter-python --allow-build=tree-sitter-ruby --allow-build=tree-sitter-rust --allow-build=tree-sitter-swift --allow-build=tree-sitter-typescript dlx gitnexus analyze
```
