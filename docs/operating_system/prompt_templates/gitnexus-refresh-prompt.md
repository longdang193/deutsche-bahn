---
name: gitnexus-refresh-prompt
description: Refresh or repair GitNexus freshness before high-trust graph use.
type: prompt
stage: maintenance
entry_points:
- GitNexus freshness is stale, failed, or inconsistent with current repo state
- high-trust GitNexus usage is needed for impact analysis/refactor safety
prerequisites:
- repository path is known
- GitNexus is installed in the current environment
next_steps:
- implementation-next-action-gate-prompt.md
- validate-or-drift-prompt.md
related_skills:
- gitnexus-guide
- gitnexus-impact-analysis
- skill-planning-dispatch
required_reads:
- AGENTS.md
- docs/operating_system/governance/repo-governance.md
tags:
- prompt
- maintenance
- gitnexus
distribution_tier: starter_kit
---

# GitNexus Refresh Prompt

Use this when GitNexus is stale, partially broken, or returning results that no
longer match the current repo state.

```text
Refresh or repair GitNexus for this repo before relying on it again.

Context:
- repo:
- current GitNexus freshness state:
- whether GitNexus is stale, failing, or returning suspicious results:
- recent symptoms:
- whether this is blocking exploration, debugging, or impact analysis:

Please:
1. check GitNexus freshness first
2. report whether the current state is fresh, stale, or failed
3. rerun the recommended GitNexus refresh path for this machine
4. verify whether the refresh fixed the problem
5. report what still does not work, if anything
6. fall back to source-first guidance if GitNexus remains stale or broken
7. keep GitNexus-specific artifacts private-only
```

Expected output:
- freshness result before refresh
- refresh command used
- status after refresh
- remaining issues, if any
- source-first fallback guidance when refresh does not fully recover GitNexus
