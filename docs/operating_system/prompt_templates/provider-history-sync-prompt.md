---
name: provider-history-sync-prompt
description: Sync provider history records to current source-of-truth lifecycle evidence.
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

# Provider History Sync Prompt

Use this when switching Codex model providers causes previous chats to
disappear from history.

Codex history visibility depends on provider metadata in both rollout/session
files and SQLite state. After switching providers, missing history usually
means those two layers still point at the old provider or disagree with the
current provider.

```text
Sync Codex chat history metadata after switching model providers.

Context:
- Codex home:
- previous provider:
- current provider:
- current config.toml provider setting:
- whether Codex Desktop/Codex CLI is currently closed:
- whether old chats are missing, archived, or visible but not resumable:

Please:
1. confirm the current provider from `config.toml`
2. run `codex-provider status` or `npx github:Dailin521/codex-provider-sync status`
3. verify whether rollout/session metadata and `state_5.sqlite` disagree
4. create or confirm a timestamped backup before changing history state
5. run `codex-provider sync` or `npx github:Dailin521/codex-provider-sync sync`
   to sync metadata to the current provider
6. run status again and report the before/after provider counts
7. warn if old histories contain `encrypted_content`, because visibility can be
   restored while continuing or compacting those chats may still fail with
   `invalid_encrypted_content`
8. keep API/auth/provider config unchanged unless explicitly asked to change it
```

Expected output:
- backup path
- current provider
- rollout/session provider counts before and after sync
- SQLite provider counts before and after sync
- encrypted-content warning, if present
- restart instruction for Codex Desktop when needed
