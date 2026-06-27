---
name: env-gitignore-contract
description: Enforce baseline .env ignore rules in .gitignore to prevent secret leakage.
alwaysApply: true
required_reads:
- AGENTS.md
- docs/operating_system/governance/repo-governance.md
tags:
- rule
- security
- gitignore
distribution_tier: starter_kit
---

# Env Gitignore Contract Rule

Repository `.gitignore` must include baseline environment-file protections:

## Required

- `.env`
- `.env.*`
- `!.env.example` when `.env.example` template is tracked

## Guidance

- `.env.example` should contain placeholders only, never real secrets.
- Real environment files must not be committed.
