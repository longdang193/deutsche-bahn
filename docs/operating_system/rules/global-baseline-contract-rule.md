---
name: global-baseline-contract
description: Enforce AGENTS.md as the shared cross-tool baseline contract.
alwaysApply: true
required_reads:
- AGENTS.md
- docs/operating_system/governance/repo-governance.md
tags:
- baseline
- cross-tool
- governance
- rule
distribution_tier: starter_kit
---

# Global Baseline Contract Rule

Use `AGENTS.md` as the shared baseline contract across Codex, Claude, and
Gemini runtimes. Runtime targets are generated and deployed; do not hand-edit
runtime target files.
