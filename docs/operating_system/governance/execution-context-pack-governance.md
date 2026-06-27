# Execution Context Pack Governance

## Purpose

Define low-admin, source-first governance for execution context-pack storage and session handoff continuity.

## Canonical Storage (Option B)

Execution context packs use one canonical durable location:

- `docs/superpowers/execution_context_packs/<lane-id>/latest.md`

Optional historical snapshots may live beside `latest.md`:

- `docs/superpowers/execution_context_packs/<lane-id>/snapshots/<YYYY-MM-DD-HHMM>.md`

`<lane-id>` must be stable, filesystem-safe, and derived from the active plan/thread/worktree identity.

## Template Contract

All context packs must follow:

- `docs/operating_system/templates/execution-context-pack-template.md`

That template is the schema source. Skills/prompts should reference it, not duplicate its field schema.

## Mirror Semantics

Worktree-local context-pack files are optional mirrors for active execution convenience:

- `artifacts/execution_context_pack.md`

Mirror files are not canonical durable storage.
Canonical repo path remains the long-lived handoff source.

## Update Triggers

Refresh canonical `latest.md` whenever any of these change:

- task state
- verification state
- blocker/risk state
- next exact action
- imminent cross-session handoff

Do not defer all updates until closeout.

## Source-Truth Precedence

If sources disagree, apply this order:

1. current source files + current tests/checks
2. canonical context pack (`latest.md`)
3. optional raw session log reference (`overview.txt`) as fallback evidence only

## Optional Deep Context

Raw session logs are optional and consult-only. If used, store references only:

- `conversation_id`
- `.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/overview.txt`
- concise reason for consultation

Do not embed large raw logs into canonical context packs.

## Minimal Operations Model

Preferred automation command shape:

- sync mirror -> canonical latest
- sync canonical latest -> mirror
- optional snapshot write

Expected script path:

- `scripts/sync_execution_context_pack.py`

## Validation Expectations

Fast validation should enforce that:

- template metadata remains valid
- execution surfaces reference canonical template/path policy
- governance references remain resolvable
